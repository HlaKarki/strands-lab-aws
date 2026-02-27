import asyncio
import logging
import os
from dotenv import load_dotenv

from strands import Agent
from strands.models import BedrockModel
from strands_tools import shell

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)

logger = logging.getLogger("my_agent")

tool_use_ids = []
def callback_handler(**kwargs):
    if "data" in kwargs:
        logger.info(kwargs["data"])
    elif "current_tool_use" in kwargs:
        tool = kwargs["current_tool_use"]
        tool_id = tool.get("toolUseId") or tool.get("id")  # Try both possible keys
        if tool_id and tool_id not in tool_use_ids:
            logger.info(f"\n[Using tool: {tool.get('name')}]")
            tool_use_ids.append(tool_id)

agent = Agent(
    model=BedrockModel(model_id=os.getenv("BEDROCK_MODEL_ID"), region_name=os.getenv("AWS_REGION")),
    tools=[shell],
    callback_handler=callback_handler
)

result = agent("What operating system am i using?")

# Print just the text content from the assistant's response
print(result.message["content"][0]["text"])