"""
Goal: An agent that can explain system design topics in depth with examples, trade-offs, and AWS-specific content.

Key features:
1. System prompt that makes it an expert tutor in system design
2. Focused on teaching (not quizzing)
3. Covering topics from specs:
    - API Design & Microservices
    - Scalability & Distributed Systems
    - Database Design
    - Cloud-Native & AWS Architecture
"""
import os

from dotenv import load_dotenv
from strands import Agent
from strands.models import BedrockModel

# Load env variables
load_dotenv(verbose=True)

TUTOR_PROMPT = """
You are an expert system design tutor preparing software engineers for senior-level interviews.
Your job is to teach concepts clearly with real-world examples and AWS-specific implementations.

When teaching a topic:
- Explain the concept and why it matters
- Give concrete examples
- Discuss trade-offs and when to use what
- Connect to interview scenarios
- Invite follow-up questions

Focus on: API Design, Scalability, Database, Cloud Architecture
"""

def create_tutor_agent():
    model = BedrockModel(
        model_id=os.getenv("BEDROCK_MODEL_ID"),
        region_name=os.getenv("AWS_REGION"),
    )

    return Agent(
        model=model,
        system_prompt=TUTOR_PROMPT,
        tools=[]
    )