import os
from dotenv import load_dotenv
from strands import Agent, tool
from strands.models import BedrockModel

from agents.quiz import create_quiz_agent
from agents.tutor import create_tutor_agent

# Load env variables
load_dotenv(verbose=True)

ORCHESTRATOR_PROMPT = """
You are the System Design Interview Coach orchestrator. You manage the learning session.

Your workflow:
1. Greet the user and ask what topic they want to study
2. When they choose a topic, use the tutor_agent tool to teach it
3. After teaching, ask if they want to be quizzed
4. When ready to quiz, use the quiz_agent tool to generate questions and evaluate answers
5. Provide session summaries and suggest next topics

Available topics:
- API Design & Microservices
- Scalability & Distributed Systems
- Database Design & Data Modeling
- Cloud-Native & AWS Architecture

Be conversational (but not chatty), encouraging, and guide them through the session naturally.
When the user says things like "teach me" or "explain", use tutor_agent.
When they say "quiz me" or "test me", use quiz_agent.
"""

@tool
def tutor_agent(query: str) -> str:
    """
    Expert tutor that teaches system design concepts with examples, trade-offs, and AWS-specific implementations.

    :param query: The topic or question to teach about
    :return: Detailed explanation with examples
    """
    print("==> Routed to Tutor Agent")
    tutor = create_tutor_agent()
    response = tutor(query)
    return response

# Set up agents as tool
@tool
def quiz_agent(query: str) -> str:
    """
    Quiz master that generates system design interview questions and evaluates answers with constructive feedback.

    :param query: Request to generate questions or evaluate an answer
    :return: Question or evaluation with score and feedback
    """
    print("==> Routed to Quiz Agent")
    quiz = create_quiz_agent()
    response = quiz(query)
    return response

def create_orchestrator():
    model = BedrockModel(
        model_id=os.getenv("BEDROCK_MODEL_ID"),
        region_name=os.getenv("AWS_REGION")
    )

    # Create orchestrator
    return Agent(
        model=model,
        system_prompt=ORCHESTRATOR_PROMPT,
        tools=[tutor_agent, quiz_agent],
    )