import os
import sys

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from openai import OpenAI


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
	
	if llm_provider == "openrouter" and os.getenv('OPENROUTER_API_KEY'):
		# 使用新的OpenAI客户端与OpenRouter API交互
		client = OpenAI(
			base_url="https://openrouter.ai/api/v1",
			api_key=os.getenv('OPENROUTER_API_KEY'),
		)
		
		# 创建自定义的ChatOpenAI实例
		return ChatOpenAI(
			model='openrouter/quasar-alpha',  # 或其他适合的模型
			api_key=SecretStr(os.getenv('OPENROUTER_API_KEY')),
			base_url="https://openrouter.ai/api/v1",
			extra_headers={
				"HTTP-Referer": "https://github.com/browser-use/macOS-use",  # 项目URL
				"X-Title": "macOS-use",  # 项目名称
			}
		)
	
	if llm_provider == "google" and os.getenv('GEMINI_API_KEY'):
		return ChatGoogleGenerativeAI(model='gemini-2.0-flash-exp', api_key=SecretStr(os.getenv('GEMINI_API_KEY')))
	
	if llm_provider == "anthropic" and os.getenv('ANTHROPIC_API_KEY'):
		return ChatAnthropic(model='claude-3-sonnet-20240229', api_key=SecretStr(os.getenv('ANTHROPIC_API_KEY')))
	
	return None

# Try to set LLM based on available API keys
llm = None
if os.getenv('OPENROUTER_API_KEY'):
	llm = set_llm('openrouter')
elif os.getenv('GEMINI_API_KEY'):
	llm = set_llm('google')
elif os.getenv('OPENAI_API_KEY'):
	llm = set_llm('OAI')
elif os.getenv('ANTHROPIC_API_KEY'):
	llm = set_llm('anthropic')

if not llm:
	raise ValueError("No API keys found. Please set at least one of OPENROUTER_API_KEY, GEMINI_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY in your .env file")

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
	
	task_print="""

Instructions:
YOU MUST USE IPHONE MIRRORING TO FOR THE FOLLOWING TASKS-
1. Click iPhone Mirroring in the Dock or open from Applications/Launchpad (requires macOS Sequoia 15+)
found at: /System/Applications/Utilities/iPhone http://Mirroring.app

HOW TO USE IPHONE MIRRORING:
- Tap/swipe using mouse/trackpad
- Type using Mac keyboard
- Go to Home Screen (Command-1)
- Open App Switcher (Command-2)
- Open Spotlight (Command-3)
- Control audio through Mac
Note: Camera/mic access not available. Connection pauses after inactivity.
IMPORTANT: Open Spotlight (Command-3) to search for and open the app you want to use.

TASK:

/n
"""
	task = task_print+input("Enter the task you'd like to perform with iPhone Mirroring: ")
  
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
