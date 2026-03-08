import os

from strands import Agent
from strands.models import BedrockModel
from strands.multiagent import GraphBuilder
from strands.multiagent.graph import GraphState
from strands.session.file_session_manager import FileSessionManager
from dotenv import load_dotenv
from services.fotmob import FotmobClient
from services.job_swarm import JobSwarm

load_dotenv(verbose=True)

class Orchestrator:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.model = BedrockModel(model_id=os.getenv("BEDROCK_MODEL_ID"), region_name=os.getenv("AWS_REGION"))
        self.session_manager = FileSessionManager(
            session_id=user_id,
            storage_dir="./sessions"
        )
        self.router_agent = self._build_router_agent()
        self.football_agent = self._get_football_agent()
        self.jobs_agent = self._get_jobs_agent()
        self.chat_agent = self._build_chat_agent()

    @staticmethod
    def _get_football_agent():
        return FotmobClient().get_football_agent()

    @staticmethod
    def _get_jobs_agent():
        return JobSwarm().get_job_application_swarm()

    def _build_router_agent(self):
        return Agent(
            name="router_agent",
            model=self.model,
            tools=[],
            callback_handler=None,
            system_prompt="""You are a routing agent that analyzes user intent.

            Based on the user's message, determine which specialized agent should handle it:
            - football_agent: For football/soccer queries (matches, players, teams, leagues)
            - jobs_agent: For job searching, resume analysis, career assistance
            - chat_agent: For general conversation or unclear requests
            
            CRITICAL: You MUST include EXACTLY ONE of these agent names in your response:
            - "football_agent"
            - "jobs_agent"
            - "chat_agent"
            
            Examples:
            - User: "Show me Arsenal's fixtures" → You: "Routing to football_agent for match information"
            - User: "Help me find a job" → You: "Routing to jobs_agent for career assistance"
            - User: "What's up?" → You: "Routing to chat_agent for casual conversation"
            
            Be brief and only mention ONE agent name."""
        )

    def _build_chat_agent(self):
        return Agent(
            name="chat_agent",
            model=self.model,
            tools=[],
            callback_handler=None,
            system_prompt="""You are a helpful general assistant for casual conversation.

            Output Formatting:
                - This is a CLI terminal application. DO NOT use markdown formatting.
                - NO bold (**text**), NO headers (##), NO italics, NO markdown syntax.
                - Use plain text with clear structure:
                  * Section headers in UPPERCASE or with simple prefixes like "==="
                  * Use indentation (2-4 spaces) for hierarchy
                  * Use simple ASCII separators: ---, ===, •, -, etc.
                  * Use line breaks for readability
                        
            Handle greetings, general questions, and unclear requests.
            If the user's intent becomes clear (they want football info or job help),
            you can suggest they ask about those topics.
            
            CRITICAL OUTPUT FORMAT:
            1. First, briefly think through what you're doing (1-2 sentences max)
            2. Output exactly: ---FINAL---
            3. Then write ONLY your response to the user
            
            IMPORTANT: Do NOT repeat your thinking after ---FINAL---. Only write what the user should see."""
        )

    @staticmethod
    def _should_route_to_football(state: GraphState) -> bool:
        """Route to football agent if router detected football intent."""
        router_result = state.results.get("router_agent")
        if not router_result:
            return False

        response = str(router_result.result).lower()
        return "football_agent" in response

    @staticmethod
    def _should_route_to_jobs(state: GraphState) -> bool:
        """Route to jobs agent if router detected job-related intent."""
        router_result = state.results.get("router_agent")
        if not router_result:
            return False

        response = str(router_result.result).lower()
        return "jobs_agent" in response

    @staticmethod
    def _should_route_to_chat(state: GraphState) -> bool:
        """Route to chat agent for general conversation."""
        router_result = state.results.get("router_agent")
        if not router_result:
            return False

        response = str(router_result.result).lower()
        return "chat_agent" in response

    def get_graph(self):
        builder = GraphBuilder()

        # nodes
        builder.add_node(self.router_agent, "router_agent")
        builder.add_node(self.football_agent, "football_agent")
        builder.add_node(self.jobs_agent, "jobs_agent")
        builder.add_node(self.chat_agent, "chat_agent")

        # Conditional edges from router
        builder.add_edge("router_agent", "football_agent",
                        condition=self._should_route_to_football)
        builder.add_edge("router_agent", "jobs_agent",
                        condition=self._should_route_to_jobs)
        builder.add_edge("router_agent", "chat_agent",
                        condition=self._should_route_to_chat)

        builder.set_entry_point("router_agent")
        builder.set_execution_timeout(60 * 10)  # 10 minute
        builder.set_session_manager(self.session_manager)


        return builder.build()