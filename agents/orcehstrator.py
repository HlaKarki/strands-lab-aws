import os
from dotenv import load_dotenv
from strands import Agent
from strands.models import BedrockModel
from tools.session import SessionContext
from tools.orchestrator_tools import create_orchestrator_tools

# Load environment variables
load_dotenv(verbose=True)

ORCHESTRATOR_PROMPT = """
You are the System Design Interview Coach orchestrator. You manage the learning session.

Your workflow:
1. Greet the user and check their progress (use get_user_progress tool)
2. When they choose a topic, use tutor_agent to teach it
3. After teaching, ask if they want to be quizzed
4. Use quiz_agent to generate questions and evaluate answers
5. After quiz, call update_progress with the topic and score
6. Provide session summaries and suggest next uncovered topics

Available topics:
- API Design & Microservices
- Scalability & Distributed Systems
- Database Design & Data Modeling
- Cloud-Native & AWS Architecture

Be conversational (but not chatty), encouraging, and guide them through the session naturally.
When the user says things like "teach me" or "explain", use tutor_agent.
When they say "quiz me" or "test me", use quiz_agent.
After each quiz, use update_progress to save their score.
"""


class OrchestratorSession:
    """
    Session-scoped orchestrator bound to a specific user.
    Manages the conversation flow and coordinates between specialist agents.
    """

    def __init__(self, user_id: str):
        """
        Initialize orchestrator session for a specific user.

        :param user_id: Unique identifier for the user
        """
        self.session = SessionContext.create(user_id)
        self.agent = self._create_agent()

    def _create_agent(self) -> Agent:
        """
        Create the orchestrator agent with session-aware tools.

        :return: Configured Agent instance
        """
        # Create tools bound to this session
        tools = create_orchestrator_tools(self.session)

        # Initialize Bedrock model
        model = BedrockModel(
            model_id=os.getenv("BEDROCK_MODEL_ID"),
            region_name=os.getenv("AWS_REGION")
        )

        # Return agent with orchestration logic
        return Agent(
            model=model,
            system_prompt=ORCHESTRATOR_PROMPT,
            tools=tools,
        )

    def execute(self, user_input: str) -> str:
        """
        Execute one conversation turn with the user.

        :param user_input: User's message
        :return: Orchestrator's response
        """
        response = self.agent(user_input)
        return str(response)

    def save(self) -> bool:
        """
        Save session progress to DynamoDB.

        :return: True if save was successful
        """
        return self.session.save()


def create_orchestrator(user_id: str) -> OrchestratorSession:
    """
    Factory function to create a session-scoped orchestrator.

    :param user_id: Unique identifier for the user
    :return: OrchestratorSession instance
    """
    return OrchestratorSession(user_id)