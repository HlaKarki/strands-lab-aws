import os
from dotenv import load_dotenv
from strands import Agent, tool
from strands.models.bedrock import BedrockModel
from strands_tools import calculator, current_time

# Load env variables
load_dotenv(verbose=True)

# Define a custom tool as a Python function using the @tool decorator
@tool
def letter_counter(word: str, letter: str) -> int:
    """
    Count occurrences of a specific letter in a word.

    :param word: The input word to search in
    :param letter: The specific letter to count
    :return: The number of occurrences of the letter in the word
    """

    if not isinstance(word, str) or not isinstance(letter, str):
        return 0

    if len(letter) != 1:
        raise ValueError("The 'letter' parameter must be a single character")

    return word.lower().count(letter.lower())

# Create an agent
model_id = os.getenv("BEDROCK_MODEL_ID")
region = os.getenv("AWS_REGION")
agent = Agent(
    model=BedrockModel(model_id=model_id, region_name=region),
    tools=[calculator, current_time, letter_counter],
)

# Ask the agent a question that uses the available tools
message = """
I have 4 requests

1. What is the time right now?
2. Calculate 3111696 / 74088
3. Tell me how many letter R's are in the word "strawberry"
"""

agent(message)
