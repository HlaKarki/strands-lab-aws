import os
import pymupdf
from pathlib import Path
from dotenv import load_dotenv
from jobspy import scrape_jobs
from strands import tool, Agent
from strands.models import BedrockModel

load_dotenv()

class JobSwarm:
    def __init__(self):
        self.site_name = ["linkedin"]
        self.scraper_result_limit = 5
        self.scraper_result_age = 72
        self.resume_path = None
        self.resume_content: str | None = None

    @staticmethod
    def _clean_path(path: str) -> str:
        """
        Clean up path string from terminal escape codes and formatting.
        Handles drag-drop artifacts, quotes, backslashes, and expands home directory.
        """
        path = path.strip()
        path = path.replace('\\', '')
        path = path.strip("'\"")
        path = os.path.expanduser(path)
        return path

    def _parse_resume_file(self):
        path = Path(self.resume_path)

        if not path.exists():
            raise FileNotFoundError(f"Resume file not found: {self.resume_path}")

        if path.suffix.lower() == '.txt':
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        elif path.suffix.lower() == '.pdf':
            doc = pymupdf.open(path)
            content = ""
            for page in doc:
                text = page.get_text()
                content += text
            return content

        elif path.suffix.lower() in ['.docx', '.doc']:
            raise NotImplementedError("DOCX not supported. Use .pdf or .txt.")
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")

    @tool
    def load_resume(self, file_path: str = None):
        """
        Load and parse the user's resume from a file.

        This is the FIRST tool to call when the user wants to analyze their resume,
        score job fit, or perform any resume-related operations.

        Supports PDF and TXT file formats. Automatically handles:
        - Terminal escape codes from drag-and-drop
        - Path cleaning (quotes, backslashes, ~)
        - File validation

        Use this tool when:
        - User mentions analyzing their resume
        - User wants job fit scoring (resume required)
        - User asks about their skills, experience, or qualifications
        - Any other tool requires resume data but it's not loaded yet

        :param file_path: Optional absolute path to resume file (.pdf or .txt).
                         If not provided, will prompt user to paste/drag the file path.
        :return: Confirmation message with character count of loaded resume
        """
        if not file_path:
            print("\n📄 Drag your resume file here (or paste the path): ")
            file_path = input().strip()

        file_path = self._clean_path(file_path)

        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"Resume file not found: {file_path}")

        valid_extensions = ['.pdf', '.txt']
        if not any(file_path.lower().endswith(ext) for ext in valid_extensions):
            raise ValueError(f"❌ Unsupported file type. Supported: {', '.join(valid_extensions)}")

        self.resume_path = file_path
        self.resume_content = self._parse_resume_file()

        return f"Resume loaded: {len(self.resume_content)} chars"

    @tool
    def analyze_resume(self):
        """
        Analyze and return the full content of the user's loaded resume.

        This tool retrieves the complete resume text for analysis. Use the resume content
        to extract skills, experience, education, and qualifications.

        IMPORTANT: Resume must be loaded first using the load_resume tool.
        If resume is not loaded, this tool will raise an error instructing you to load it.

        Use this tool when:
        - User asks "what's on my resume?" or "analyze my resume"
        - Need resume content to compare against job descriptions
        - Extracting specific information (skills, years of experience, education)
        - Preparing resume summary or highlights

        Prerequisites:
        - Must call load_resume tool first if resume not already loaded

        :return: Full text content of the resume
        :raises ValueError: If resume is not loaded yet
        """
        if not self.resume_content:
            raise ValueError("⚠️ Resume not loaded. Use 'load_resume' tool first to load your resume.")

        return self.resume_content

    def job_scraper(self, search_term="software engineer", location="Virginia, USA"):
        jobs = scrape_jobs(
            site_name=self.site_name,
            search_term=search_term,
            location=location,
            results_wanted=self.scraper_result_limit,
            hours_old=self.scraper_result_age,
            verbose=0,
            linkedin_fetch_description=True,
        )

        return jobs.to_dict("records")

    def fit_scorer(self):
        pass

    def gap_analyst(self):
        pass

    def cover_letter_writer(self):
        pass

    def interview_prepper(self):
        pass

    def get_job_application_swarm(self):
        return Agent(
            model=BedrockModel(model_id=os.getenv("BEDROCK_MODEL_ID"), region_name=os.getenv("AWS_REGION")),
            tools=[self.load_resume, self.analyze_resume],
            callback_handler=None,
            system_prompt="""You are an intelligent job application assistant that helps users with their job search.

Your capabilities:
- Load and analyze resumes (PDF/TXT formats)
- Extract skills, experience, and qualifications from resumes
- (Coming soon: Job searching, fit scoring, cover letter writing, interview prep)

CRITICAL WORKFLOW:
1. Resume is REQUIRED for most operations
2. If resume is not loaded and user asks for resume-related tasks:
   - Call load_resume tool first (it will prompt user for file path)
   - Then proceed with the requested analysis
3. If load_resume tool is called without a file_path parameter, it will interactively ask the user to provide the path

ERROR HANDLING:
- If analyze_resume raises "Resume not loaded" error, immediately call load_resume
- Guide user through the process clearly
- Confirm successful resume loading before proceeding

COMMUNICATION STYLE:
- Be concise and helpful
- Clearly explain what you're doing and why
- If asking for file path, mention user can drag & drop the file
- Provide actionable insights from resume analysis
"""
        )