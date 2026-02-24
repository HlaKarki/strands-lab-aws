from typing import Optional
from strands import tool
from agents.tutor import create_tutor_agent
from agents.quiz import create_quiz_agent
from tools.session import SessionContext


def create_orchestrator_tools(session: SessionContext):
    """
    Factory function that creates tool callables bound to a specific session context.
    This pattern avoids global variables and enables concurrent user sessions.

    :param session: SessionContext instance for the current user
    :return: List of tool functions for the orchestrator
    """

    @tool
    def tutor_agent(query: str) -> str:
        """
        Expert tutor that teaches system design concepts with examples,
        trade-offs, and AWS-specific implementations.

        :param query: The topic or question to teach about
        :return: Detailed explanation with examples
        """
        print(f" [{session.user_id}] Routing to Tutor Agent")
        tutor = create_tutor_agent()
        response = tutor(query)
        return response

    @tool
    def quiz_agent(query: str) -> str:
        """
        Quiz master that generates system design interview questions
        and evaluates answers with constructive feedback.

        :param query: Request to generate questions or evaluate an answer
        :return: Question or evaluation with score and feedback
        """
        print(f" [{session.user_id}] Routing to Quiz Agent")
        quiz = create_quiz_agent()
        response = quiz(query)
        return response

    @tool
    def update_progress(topic: str, quiz_score: Optional[float] = None) -> str:
        """
        Update the user's progress after completing a topic or quiz.
        This persists the data to DynamoDB.

        :param topic: Topic name (e.g., 'API Design & Microservices')
        :param quiz_score: Optional quiz score (0-100)
        :return: Confirmation message
        """
        success = session.update_topic(topic, quiz_score)
        if success:
            score_msg = f" (score: {quiz_score})" if quiz_score else ""
            return f" Progress saved for '{topic}'{score_msg}"
        return f" Failed to save progress for '{topic}'"

    @tool
    def get_user_progress() -> str:
        """
        Get the current user's learning progress summary.
        Shows topics covered, quiz scores, and suggests next steps.

        :return: Formatted summary of topics and scores
        """
        return session.get_summary()

    # Return all tools for the orchestrator agent
    return [tutor_agent, quiz_agent, update_progress, get_user_progress]
