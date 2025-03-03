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
	
	if llm_provider == "OAI" and os.getenv('OPENAI_API_KEY'):
		return ChatOpenAI(model='gpt-4', api_key=SecretStr(os.getenv('OPENAI_API_KEY')))
	
	if llm_provider == "google" and os.getenv('GEMINI_API_KEY'):
		return ChatGoogleGenerativeAI(model='gemini-2.0-flash-exp', api_key=SecretStr(os.getenv('GEMINI_API_KEY')))
	
	if llm_provider == "anthropic" and os.getenv('ANTHROPIC_API_KEY'):
		return ChatAnthropic(model='claude-3-sonnet-20240229', api_key=SecretStr(os.getenv('ANTHROPIC_API_KEY')))
	
	return None

# Try to set LLM based on available API keys
llm = None
if os.getenv('GEMINI_API_KEY'):
	llm = set_llm('google')
elif os.getenv('OPENAI_API_KEY'):
	llm = set_llm('OAI')
elif os.getenv('ANTHROPIC_API_KEY'):
	llm = set_llm('anthropic')

if not llm:
	raise ValueError("No API keys found. Please set at least one of GEMINI_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY in your .env file")

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
