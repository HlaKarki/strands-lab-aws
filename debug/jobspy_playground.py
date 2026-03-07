import asyncio
import csv

from services.job_swarm import JobSwarm


# def test_jobspy():
#     jobs = scrape_jobs(
#         site_name=["linkedin"],
#         search_term="software engineer",
#         location="Maryland, USA",
#         results_wanted=2,
#         hours_old=72,
#         verbose=2,
#         linkedin_fetch_description=True,
#     )
#
#     print(f"\nFound {len(jobs)} jobs")
#     print(f"\nColumns: {jobs.columns.tolist()}")
#     print(f"\nFirst few results:")
#     print(jobs.head())
#
#     # Clean
#     # jobs = jobs[["site", "title", "company", "location", "description", "date_posted", "job_url", "is_remote", "company_url"]]
#
#     print(jobs.to_dict("records"))
#     # Save to CSV
#     output_file = "../scrapers/jobs_output_2.csv"
#     jobs.to_csv(output_file, quoting=csv.QUOTE_NONNUMERIC, index=False)
#     print(f"\nSaved results to {output_file}")
#
#     return jobs


async def test_resume_agent():
    """Test the job application agent with resume loading"""
    print("\n" + "="*60)
    print("Testing Job Application Agent")
    print("="*60 + "\n")

    jobswarm = JobSwarm()
    agent = jobswarm.get_job_application_swarm()

    # Test: Agent should detect resume not loaded and ask for it
    result = await agent.invoke_async("Analyze my resume for me")

    print("\n" + "="*60)
    print("📊 Agent Response:")
    print("="*60)
    print(result.message["content"][0]["text"])


async def test_job_finder_agent():
    """Test the job finder agent in the swarm"""
    print("\n" + "="*60)
    print("🔍 Testing Job Finder Swarm")
    print("="*60 + "\n")

    jobswarm = JobSwarm()

    # Test: Find jobs and potentially score them
    # job_finder = jobswarm._get_job_finder_agent()
    # result = await job_finder.invoke_async("Find me software engineer job opportunities. front end preferred but all works")
    # print(result.message)

    swarm = jobswarm.get_job_application_swarm()
    result = await swarm.invoke_async("Using my resume, find me non-senior level SWE job postings. anywhere in the U.S. is okay. Just 5 postings.")
    print("\n" + "="*60)
    print("📊 Swarm Response:")
    print("="*60)
    print(f"Status: {result.status}")
    print(f"Execution time: {result.execution_time}s")
    print(f"Execution count: {result.execution_count}")
    print(f"\nFull result dict: {result.to_dict()}")


if __name__ == "__main__":
    # test_jobspy()
    # asyncio.run(test_resume_agent())
    asyncio.run(test_job_finder_agent())

