import os
import sys

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import argparse
import asyncio

from mlx_use import Agent
from pydantic import SecretStr
from mlx_use.controller.service import Controller


def set_llm(llm_provider:str = None):
	if not llm_provider:
		raise ValueError("No llm provider was set")
	
	if llm_provider == "OAI":
		try:
			api_key = os.getenv('OPENAI_API_KEY')
		except Exception as e:
			print(f"Error while getting API key: {e}")
			api_key = None
		return ChatOpenAI(model='gpt-4o', api_key=SecretStr(api_key))
	
	if llm_provider == "google":
		try:
			api_key = os.getenv('GEMINI_API_KEY')
		except Exception as e:
			print(f"Error while getting API key: {e}")
			api_key = None
		return ChatGoogleGenerativeAI(model='gemini-2.0-flash-exp',  api_key=SecretStr(api_key))
	if llm_provider == "anthropic":
		try:
			api_key = os.getenv('ANTHROPIC_API_KEY')
		except Exception as e:
			print(f"Error while getting API key: {e}")
			api_key = None
		return ChatAnthropic(model='claude-3-7-sonnet-20250219',  api_key=SecretStr(api_key))

llm = set_llm('google')
llm = set_llm('OAI')
llm = set_llm('anthropic')

controller = Controller()


async def main():

	agent_greeting = Agent(
		task='Say "Hi there $whoami,  What can I do for you today?"',
		llm=llm,
		controller=controller,
		use_vision=False,
		max_actions_per_step=1,
		max_failures=5
	)
  
	await agent_greeting.run(max_steps=25)
	task = input("Enter the task: ")
  
	agent_task = Agent(
		task=task,
		llm=llm,
		controller=controller,
		use_vision=False,
		max_actions_per_step=4,
		max_failures=5
	)
	
	await agent_task.run(max_steps=25)


asyncio.run(main())
