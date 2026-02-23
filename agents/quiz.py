import os
from dotenv import load_dotenv
from strands import Agent, tool
from strands.models import BedrockModel

# Load env variables
load_dotenv(verbose=True)

QUIZ_PROMPT = """
You are a system design interview quiz master. Your job is to:
1. Generate realistic scenario-based questions on requested topics
2. Evaluate answers for correctness, depth, and trade-off awareness
3. Provide constructive feedback and scores

When generating questions:
- Make them open-ended scenarios (not multiple choice)
- Require the candidate to explain their reasoning
- Test understanding of trade-offs, not memorization

When evaluating answers:
- Score from 0-10
- Highlight what was good
- Point out what was missed
- Suggest what a strong answer would include

Topics: API Design, Scalability, Databases, Cloud Architecture
"""

@tool
def generate_question(topic: str) -> str:
    """
    Generate a system design interview question on a specific topic.

    :param topic: The system design topic (e.g., "API Design", "Scalability", "Databases", "Cloud Architecture")
    :return: A scenario-based interview question
    """

    # The agent will implement this via its reasoning
    return f"Generate a challenging interview question about {topic}"

@tool
def evaluate_answer(question: str, answer: str) -> dict:
    """
    Evaluate a candidate's answer to a system design question.

    :param question: The original question asked
    :param answer: The candidate's response
    :return: Dictionary with score (0-10), feedback, and what was missed
    """
    # The agent will implement this via its reasoning
    return {
        "question": question,
        "answer": answer,
        "evaluation_request": "Evaluate this answer",
    }

def create_quiz_agent():
    model = BedrockModel(
        model_id=os.getenv("BEDROCK_MODEL_ID"),
        region_name=os.getenv("AWS_REGION"),
    )

    return Agent(
        model=model,
        system_prompt=QUIZ_PROMPT,
        tools=[generate_question, evaluate_answer],
    )