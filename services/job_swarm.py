import os
import pymupdf
from pathlib import Path
from dotenv import load_dotenv
from strands import tool, Agent
from strands.models import BedrockModel
from strands.multiagent import Swarm
from strands_tools import http_request, current_time, file_write

load_dotenv()

class JobSwarm:
    def __init__(self):
        self.site_name = ["linkedin"]
        self.scraper_result_limit = 5
        self.scraper_result_age = 72
        self.resume_path = None
        self.resume_content: str | None = None
        self.model = BedrockModel(model_id=os.getenv("BEDROCK_MODEL_ID"), region_name=os.getenv("AWS_REGION"))

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

    # @tool
    # def scrape_jobs(self, search_term="software engineer", location="Virginia, USA"):
    #     """
    #     Scrape job listings from LinkedIn.
    #
    #     Returns detailed job information including:
    #     - Job title, company, location
    #     - Full job description
    #     - Salary information (when available)
    #     - Date posted, job type (remote/onsite)
    #     - Direct application links
    #
    #     Use this for bulk job searching across major job boards.
    #
    #     :param search_term: Job search query (e.g., "software engineer", "data scientist")
    #     :param location: Geographic location (e.g., "Virginia, USA", "New York, NY")
    #     :return: List of job dictionaries with full details
    #     """
    #     jobs = scrape_jobs(
    #         site_name=self.site_name,
    #         search_term=search_term,
    #         location=location,
    #         results_wanted=self.scraper_result_limit,
    #         hours_old=self.scraper_result_age,
    #         verbose=0,
    #         linkedin_fetch_description=True,
    #     )
    #
    #     return jobs.to_dict("records")

    def fit_scorer(self):
        pass

    def gap_analyst(self):
        pass

    def cover_letter_writer(self):
        pass

    def interview_prepper(self):
        pass

    def _get_resume_agent(self):
        return Agent(
            name="resume_agent",
            model=self.model,
            tools=[self.load_resume, self.analyze_resume],
            callback_handler=None,
            system_prompt="""You are a resume analysis specialist.

            Your tools:
            1. load_resume - Load user's resume from file (prompts for path if not provided)
            2. analyze_resume - Get resume content and analyze
            
            Workflow:
            - If user wants to analyze resume, use load_resume first (if not already loaded)
            - Then use analyze_resume to extract skills, experience, education
            - After analyzing resume, hand off to job_finder if user wants to search for jobs
            
            IMPORTANT: Resume is required for job fit scoring. Make sure to load it before any job search operations."""
        )

    def _get_job_finder_agent(self):
        return Agent(
            name="job_finder",
            model=self.model,
            tools=[http_request, current_time],
            callback_handler=None,
            system_prompt="""You find jobs using http_request to fetch from curated, high-quality job sources.

            CURATED JOB SOURCES (use these):
            
            Startup/Early-Stage:
            - https://www.workatastartup.com (YC companies)
            - https://wellfound.com/jobs
            - https://breakoutlist.com
            - https://www.f6s.com/jobs
            - https://www.rocketship.fm
            
            Developer/Engineering:
            - https://news.ycombinator.com/submitted?id=whoishiring (HN Who's Hiring, monthly)
            - https://cord.co
            
            Government-Funded/Research:
            - https://seedfund.nsf.gov/awardees/history/ (NSF SBIR/STTR)
            - https://www.sbir.gov/sbirsearch/award/all
            
            Industry-Specific:
            - https://climatebase.org/jobs (climate tech)
            - https://terra.do/climate-jobs
            - https://aijobs.net (AI/ML)
            
            Regional Tech:
            - https://builtin.com (multiple cities)
            
            Quality General:
            - https://www.themuse.com/jobs
            
            Extract for each job: job_url, job_title, company_name, location, job_description, salary_range, job_type, work_arrangement, experience_level, required_skills, date_posted.

            After finding jobs, hand off to persist_job_applications to save them locally.""",
        )

    def _get_persist_job_applications_agent(self):
        return Agent(
            name="persist_job_applications",
            model=self.model,
            tools=[file_write, current_time],
            callback_handler=None,
            system_prompt="""Extract job postings from the previous agent's output and save them locally.

            CRITICAL: Look at the job_finder agent's output above to get the job data.
            
            Save to: ./resumes/opportunities/jobs_{current_timestamp}.json
            
            JSON Format (must include ALL fields for each job):
            ```json
            [
              {
                "job_url": "https://...",
                "job_title": "Senior Software Engineer",
                "company_name": "Acme Corp",
                "location": "San Francisco, CA",
                "job_description": "Full description...",
                "salary_range": "$150k-$190k",
                "job_type": "Full-time",
                "work_arrangement": "Hybrid",
                "experience_level": "Senior",
                "required_skills": ["Python", "AWS"],
                "date_posted": "2024-03-01",
                "application_deadline": null,
                "benefits": ["equity", "health insurance"],
                "scraped_at": "{current_timestamp}"
              }
            ]
            ```
            
            Steps:
            1. Use current_time to get timestamp
            2. Extract all jobs from previous output
            3. Use file_write to save as JSON
            4. Confirm: "Saved X jobs to ./resumes/opportunities/jobs_{timestamp}.json"
            5. Hand off to fit_scorer to analyze and score the jobs against the user's resume"""
        )

    def _get_fit_scorer_agent(self):
        return Agent(
            name="fit_scorer",
            model=self.model,
            tools=[self.analyze_resume],
            callback_handler=None,
            system_prompt="""You are a job fit scoring specialist who analyzes how well jobs match the user's resume.

            Workflow:
            1. Use analyze_resume tool to get the user's resume content
            2. Look at the jobs from the previous agent's output
            3. For EACH job, provide:
               - fit_score (0-100): Overall match quality
               - matching_skills: Skills from resume that match job requirements
               - missing_skills: Required skills the candidate lacks
               - skill_gaps: Brief explanation of what needs improvement
               - recommendation: Apply now / Learn X first / Not a good fit
            
            4. Rank jobs by fit_score (highest first)
            5. Present results clearly to user
            6. Hand off to persist_scored_applications to save the scored jobs locally
            
            Scoring criteria:
            - 90-100: Excellent match, apply immediately
            - 75-89: Strong match, good opportunity
            - 60-74: Decent match, consider applying
            - 40-59: Moderate gaps, apply if interested
            - 0-39: Significant gaps, not recommended""",
        )

    def _get_persist_scored_applications_agent(self):
        return Agent(
            name="persist_scored_applications",
            model=self.model,
            tools=[file_write, current_time],
            callback_handler=None,
            system_prompt="""Extract scored job postings from the fit_scorer agent's output and save them locally.

            CRITICAL: Look at the fit_scorer agent's output above to get the scored job data.
            
            Save to: ./resumes/scored/scored_jobs_{current_timestamp}.json
            
            JSON Format (must include ALL fields for each scored job):
            ```json
            [
              {
                "job_url": "https://...",
                "job_title": "Senior Software Engineer",
                "company_name": "Acme Corp",
                "location": "San Francisco, CA",
                "job_description": "Full description...",
                "salary_range": "$150k-$190k",
                "job_type": "Full-time",
                "work_arrangement": "Hybrid",
                "experience_level": "Senior",
                "required_skills": ["Python", "AWS"],
                "date_posted": "2024-03-01",
                "fit_score": 85,
                "matching_skills": ["Python", "AWS", "PostgreSQL"],
                "missing_skills": ["Kubernetes", "GraphQL"],
                "skill_gaps": "Need to learn Kubernetes for container orchestration",
                "recommendation": "Strong match - apply ASAP",
                "scored_at": "{current_timestamp}"
              }
            ]
            ```
            
            Steps:
            1. Use current_time to get timestamp
            2. Extract all scored jobs from fit_scorer's output
            3. Use file_write to save as JSON
            4. Confirm: "Saved X scored jobs to ./resumes/scored/scored_jobs_{timestamp}.json"
            
            After saving, hand off to application_writer if user wants cover letters."""
        )

    def _get_app_writer_agent(self):
        return Agent(
            name="application_writer",
            model=self.model,
            tools=[],
            callback_handler=None,
            system_prompt="""You are a job application specialist.

            Your role:
            - Write tailored cover letters for specific jobs
            - Generate interview preparation materials
            - Create application strategies
            
            Currently no tools available - coming soon:
            - write_cover_letter - Generate customized cover letters
            - prep_interview - Create interview prep materials
            - identify_talking_points - Extract key selling points from resume
            
            For now, provide general application advice based on the job and resume context.""",
        )

    def get_job_application_swarm(self):
        resume_agent = self._get_resume_agent()
        job_finder = self._get_job_finder_agent()
        persist_jobs_agent = self._get_persist_job_applications_agent()
        fit_scorer = self._get_fit_scorer_agent()
        persist_scored_applications_agent = self._get_persist_scored_applications_agent()
        app_writer = self._get_app_writer_agent()

        return Swarm(
            nodes=[resume_agent, job_finder, persist_jobs_agent, fit_scorer, persist_scored_applications_agent, app_writer],
            entry_point=resume_agent,
            max_handoffs=20,
            max_iterations=20
        )
