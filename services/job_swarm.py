import os
import pymupdf
from pathlib import Path
from dotenv import load_dotenv
from strands import tool, Agent
from strands.models import BedrockModel
from strands.multiagent import Swarm
from strands_tools import http_request, current_time, file_write
from prompt_toolkit.shortcuts import PromptSession

load_dotenv()

class JobSwarm:
    def __init__(self):
        self.site_name = ["linkedin"]
        self.scraper_result_limit = 5
        self.scraper_result_age = 72
        self.resume_path = None
        self.resume_content: str | None = None
        self.model = BedrockModel(model_id=os.getenv("BEDROCK_MODEL_ID"), region_name=os.getenv("AWS_REGION"))
        self.output_prompt = """Output Formatting:
        - This is a CLI terminal application. DO NOT use markdown formatting.
        - NO bold (**text**), NO headers (##), NO italics, NO markdown syntax.
        - Use plain text with clear structure:
          * Section headers in UPPERCASE or with simple prefixes like "==="
          * Use indentation (2-4 spaces) for hierarchy
          * Use simple ASCII separators: ---, ===, •, -, etc.
          * Use line breaks for readability"""
        self.final_output_contract = """CRITICAL OUTPUT FORMAT:
        1. First, briefly explain what you're doing and call tools as needed (1-2 sentences max)
        2. Output exactly: ---FINAL---
        3. Then write ONLY the response meant for the user

        IMPORTANT: Do NOT repeat your thinking after ---FINAL---. Everything after the marker goes directly to the user."""

        # Shared state between agents
        self.jobs_found: list = []
        self.scored_jobs: list = []

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
    async def load_resume(self, file_path: str = None):
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
        if self.resume_content:
            return f"Resume loaded: ({len(self.resume_content)} chars). Use analyze_resume to view it."

        if not file_path:
            print("\n📄 Drag your resume file here (or paste the path): ")
            session = PromptSession()
            file_path = await session.prompt_async("> ")
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

    @tool
    def save_jobs_to_state(self, jobs: list):
        """
        Save found jobs to shared state so other agents can access them.

        Use this tool after scraping/finding jobs to persist them in memory.
        This allows persist_job_applications and fit_scorer agents to access
        the jobs without parsing conversational text.

        :param jobs: List of job dictionaries with fields: job_url, job_title,
                     company_name, location, job_description, salary_range, etc.
        :return: Confirmation message with job count
        """
        self.jobs_found = jobs
        return f"✓ Saved {len(jobs)} jobs to shared state. Fields: {list(jobs[0].keys()) if jobs else 'none'}"

    @tool
    def get_jobs_from_state(self):
        """
        Retrieve jobs that were found by job_finder agent.

        Use this tool to access the list of jobs without re-searching or parsing text.
        Returns empty list if no jobs have been saved yet.

        :return: List of job dictionaries
        """
        import json
        if not self.jobs_found:
            return "No jobs in state yet. job_finder needs to save jobs first."
        return json.dumps(self.jobs_found, indent=2)

    @tool
    def save_scored_jobs_to_state(self, scored_jobs: list):
        """
        Save scored/analyzed jobs to shared state.

        Use this tool after fit_scorer analyzes jobs against the resume.

        :param scored_jobs: List of job dicts with added fields: fit_score,
                            matching_skills, missing_skills, recommendation
        :return: Confirmation message
        """
        self.scored_jobs = scored_jobs
        return f"✓ Saved {len(scored_jobs)} scored jobs to shared state"

    @tool
    def get_scored_jobs_from_state(self):
        """
        Retrieve scored jobs from fit_scorer agent.

        :return: List of scored job dictionaries
        """
        import json
        if not self.scored_jobs:
            return "No scored jobs yet. fit_scorer needs to analyze jobs first."
        return json.dumps(self.scored_jobs, indent=2)

    def _get_resume_agent(self):
        return Agent(
            name="resume_agent",
            model=self.model,
            tools=[self.load_resume, self.analyze_resume],
            callback_handler=None,
            system_prompt=f"""You are a resume analysis specialist.

            Your tools:
            1. load_resume - Load user's resume from file (prompts for path if not provided)
            2. analyze_resume - Get resume content and analyze
            
            Workflow:
            - If user wants to analyze resume, use load_resume first (if not already loaded)
            - Then use analyze_resume to extract skills, experience, education
            - After analyzing resume, hand off to job_finder if user wants to search for jobs
            
            {self.output_prompt}
            
            IMPORTANT: If user wants to SEARCH/FIND jobs: Immediately hand off to job_finder. 
            NEVER ask about resume for job searches.
            
            {self.final_output_contract}"""
        )

    def _get_job_finder_agent(self):
        return Agent(
            name="job_finder",
            model=self.model,
            tools=[http_request, current_time, self.save_jobs_to_state],
            callback_handler=None,
            system_prompt=f"""You are a job finder who ONLY searches the pre-approved curated job sources listed below.

            CRITICAL RULES:
            ❌ DO NOT search generic job boards (LinkedIn, Indeed, Glassdoor, Monster, etc.)
            ❌ DO NOT search Google or other search engines for jobs
            ❌ DO NOT make up or guess job board URLs
            ✅ ONLY use the exact URLs listed below
            ✅ Systematically check each relevant source from the list
            ✅ If a URL doesn't work or returns no results, move to the next one

            CURATED JOB SOURCES (ONLY use these - no exceptions):

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

            Quality General:
            - https://www.themuse.com/jobs

            Search Strategy:
            1. Based on user's criteria (level, location, industry), pick 3-5 most relevant sources from the list above
            2. Use http_request to fetch job listings from each chosen source
            3. Parse the response (JSON/HTML) to extract job data
            4. For EACH job, create a dictionary with: job_url, job_title, company_name, location, job_description, salary_range, job_type, work_arrangement, experience_level, required_skills, date_posted
            5. Collect all jobs into a list: [job1_dict, job2_dict, ...]
            6. Use save_jobs_to_state tool to save the list
            7. Aim for 5-15 total jobs that match user's criteria

            After saving jobs to state, hand off to persist_job_applications to save them to file.
            
            {self.final_output_contract}""",
        )

    def _get_persist_job_applications_agent(self):
        return Agent(
            name="persist_job_applications",
            model=self.model,
            tools=[file_write, current_time, self.get_jobs_from_state],
            callback_handler=None,
            system_prompt=f"""Save job postings to a local JSON file.

            Steps:
            1. Use get_jobs_from_state to retrieve jobs from shared state
            2. Use current_time to get timestamp for filename
            3. Use file_write to save to: ./resumes/opportunities/YYYYMMDD/jobs_[time].json (e.g. 20260307/18:03:26-05:00.json)
            4. Confirm: "Saved X jobs to ./resumes/opportunities/YYYYMMDD/jobs_[time].json" (e.g. 20260307/18:03:26-05:00.json)
            5. Hand off to fit_scorer to analyze and score the jobs against the user's resume
            
            The jobs are already in JSON format from shared state - just save them directly.
            
            {self.final_output_contract}"""
        )

    def _get_fit_scorer_agent(self):
        return Agent(
            name="fit_scorer",
            model=self.model,
            tools=[self.analyze_resume, self.get_jobs_from_state, self.save_scored_jobs_to_state],
            callback_handler=None,
            system_prompt=f"""You are a job fit scoring specialist who analyzes how well jobs match the user's resume.

            Workflow:
            1. Use analyze_resume tool to get the user's resume content
            2. Use get_jobs_from_state to retrieve the job list
            3. For EACH job, analyze and add these fields:
               - fit_score (0-100): Overall match quality
               - matching_skills: Skills from resume that match job requirements
               - missing_skills: Required skills the candidate lacks
               - skill_gaps: Brief explanation of what needs improvement
               - recommendation: Apply now / Learn X first / Not a good fit
            
            4. Rank jobs by fit_score (highest first)
            5. Use save_scored_jobs_to_state to save the scored jobs list
            6. Present results clearly to user
            7. Hand off to persist_scored_applications to save to file
            
            Scoring criteria:
            - 90-100: Excellent match, apply immediately
            - 75-89: Strong match, good opportunity
            - 60-74: Decent match, consider applying
            - 40-59: Moderate gaps, apply if interested
            - 0-39: Significant gaps, not recommended
            
            After saving jobs to state, hand off to persist_scored_applications to save them to file.
            
            {self.final_output_contract}""",
        )

    def _get_persist_scored_applications_agent(self):
        return Agent(
            name="persist_scored_applications",
            model=self.model,
            tools=[file_write, current_time, self.get_scored_jobs_from_state],
            callback_handler=None,
            system_prompt=f"""Save scored job postings to a local JSON file.

            Steps:
            1. Use get_scored_jobs_from_state to retrieve scored jobs from shared state
            2. Use current_time to get timestamp for filename
            3. Use file_write to save to: ./resumes/scored/YYYYMMDD/scored_jobs_[time].json (e.g. 20260307/18:03:26-05:00.json)
            4. Confirm: "Saved X scored jobs to ./resumes/scored/YYYYMMDD/scored_jobs_[time].json" (e.g. 20260307/18:03:26-05:00.json)
            
            The scored jobs are already in JSON format from shared state - just save them directly.
            
            {self.output_prompt}
            
            After saving, hand off to application_writer if user wants cover letters.
            
            {self.final_output_contract}"""
        )

    def _get_app_writer_agent(self):
        return Agent(
            name="application_writer",
            model=self.model,
            tools=[],
            callback_handler=None,
            system_prompt=f"""You are a job application specialist.

            Your role:
            - Write tailored cover letters for specific jobs
            - Generate interview preparation materials
            - Create application strategies
            
            Currently no tools available - coming soon:
            - write_cover_letter - Generate customized cover letters
            - prep_interview - Create interview prep materials
            - identify_talking_points - Extract key selling points from resume
            
            For now, provide general application advice based on the job and resume context.
            
            {self.output_prompt}
            
            {self.final_output_contract}""",
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
