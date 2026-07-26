from agentspan.agents import Agent, AgentRuntime, ConversationMemory, tool
from dotenv import load_dotenv
import os
from tavily_agent_toolkit import search_and_format

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")

memory = ConversationMemory(max_messages=50)
session_id = "chatbot_session"

@tool
def say_hello():
    "Before answering any message, use this tool"
    print("HI,12345")


import asyncio

@tool
def internet_search_tool(query: str) -> str:
    """
    Search the internet for latest information.
    """
    tavily_api_key = os.getenv("TAVILY_API_KEY")

    return asyncio.run(search_and_format(
            queries=[query],
            api_key=tavily_api_key,
            search_depth="basic",
            max_results=3,
        ))


chatbot_agent=Agent(
    name="chatbot_agent",
    model="openai/gpt-5.4",
    instructions="You are a helpful agent named Alex. Use tools for better responses.",
    tools=[internet_search_tool, say_hello],
    memory=memory
)

def get_resp(query):
    with AgentRuntime() as runtime:
        result = runtime.run(chatbot_agent, query, session_id=session_id)
        return result

def main():
    while True:
        query = input("Ask Query: ")

        if query == "q":
            break

        resp = get_resp(query)
        resp.print_result()

import multiprocessing as mp
if __name__ == "__main__":
    mp.set_start_method("fork", force=True)
    main()