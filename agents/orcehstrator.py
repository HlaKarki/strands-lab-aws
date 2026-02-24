import os
from typing import Optional, Dict, Any

from dotenv import load_dotenv
from strands import Agent, tool
from strands.models import BedrockModel

from agents.quiz import create_quiz_agent
from agents.tutor import create_tutor_agent
from tools.state import load_progress, update_topic_progress, get_next_topic, save_progress

# Load env variables
load_dotenv(verbose=True)

# Available topics
ALL_TOPICS = [
    "API Design & Microservices",
    "Scalability & Distributed Systems",
    "Database Design & Data Modeling",
    "Cloud-Native & AWS Architecture",
]

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

# Global variables
_current_user_id: Optional[str] = None
_session_progress: Optional[Dict[str, Any]] = None

def set_session_user(user_id: str):
    """Set the current user for the session and load their progress"""
    global _current_user_id, _session_progress
    _current_user_id = user_id
    _session_progress = load_progress(user_id)
    print(f"Session started for user: {user_id}")
    print(f"Progress loaded: {_session_progress}")

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

@tool
def update_progress(topic: str, quiz_score: Optional[float] = None) -> str:
    """
    Update the user's progress after completing a topic or a quiz.

    :param topic: The topic that was covered (e.g. "API Design & Microservices")
    :param quiz_score: Optional quiz score (0-100) if they took a quiz
    :return: Confirmation message
    """
    global _current_user_id, _session_progress

    if not _current_user_id:
        return "Error: No active user session"

    success = update_topic_progress(_current_user_id, topic, quiz_score)

    if success:
        _session_progress = load_progress(_current_user_id)

        score_message = f"with score {quiz_score}" if quiz_score is not None else ""
        return f"Progress updated for topic '{topic}' {score_message}"
    else:
        return f"Failed to update progress for topic '{topic}'"

@tool
def get_user_progress() -> str:
    """
    Get the current user's learning progress.

    :return: Summary of topics covered and quiz scores
    """
    global _session_progress

    if not _session_progress:
        return "No progress data available"

    topics = _session_progress.get('topics_covered', [])
    scores = _session_progress.get('quiz_scores', {})
    current = _session_progress.get('current_topic', 'None')

    summary = f"Topics covered: {len(topics)}/{len(ALL_TOPICS)}"

    if topics:
        summary += "\nCompleted topics:\n"
        for topic in topics:
            score = scores.get(topic, "Not quizzed")
            summary += f"\t-{topic}: {score}\n"

    summary += f"\nCurrent topic: {current}\n"

    next_topic = get_next_topic(_session_progress['user_id'], ALL_TOPICS)
    if next_topic:
        summary += f"\nSuggested next topic: {next_topic}"
    else:
        summary += f"\nAll topics completed! Consider revewing or going deeper"

    return summary

def save_session():
    global _current_user_id, _session_progress

    if _current_user_id and _session_progress:
        success = save_progress(_current_user_id, _session_progress)
        if success:
            print(f"\nSession saved for user: {_current_user_id}")
        else:
            print(f"\nFailed to save session for user: {_current_user_id}")

def create_orchestrator(user_id: Optional[str] = None):
    # Set session user if provided
    if user_id:
        set_session_user(user_id)

    model = BedrockModel(
        model_id=os.getenv("BEDROCK_MODEL_ID"),
        region_name=os.getenv("AWS_REGION")
    )

    # Create orchestrator
    return Agent(
        model=model,
        system_prompt=ORCHESTRATOR_PROMPT,
        tools=[tutor_agent, quiz_agent, update_progress, get_user_progress],
    )