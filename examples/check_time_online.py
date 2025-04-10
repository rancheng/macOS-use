import os
import sys

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
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
	
	if llm_provider == "OAI":
		api_key = os.getenv('OPENAI_API_KEY')
		return ChatOpenAI(model='gpt-4o', api_key=SecretStr(api_key))
	
	if llm_provider == "openrouter":
		api_key = os.getenv('OPENROUTER_API_KEY')
		
		# 创建自定义的ChatOpenAI实例
		return ChatOpenAI(
			model='openrouter/quasar-alpha',  # 可以根据需要选择不同模型
			api_key=SecretStr(api_key),
			base_url="https://openrouter.ai/api/v1",
			extra_headers={
				"HTTP-Referer": "https://github.com/browser-use/macOS-use",  # 项目URL
				"X-Title": "macOS-use",  # 项目名称
			}
		)
	
	if llm_provider == "google":
		api_key = os.getenv('GEMINI_API_KEY')
		return ChatGoogleGenerativeAI(model='gemini-2.0-flash-exp',  api_key=SecretStr(api_key))
	
# 优先使用OpenRouter，如果有API密钥
if os.getenv('OPENROUTER_API_KEY'):
	llm = set_llm('openrouter')
else:
	llm = set_llm('OAI')

controller = Controller()

task = 'Can you check what hour is Shabbat in israel today? call done when you finish.'


agent = Agent(
	task=task,
	llm=llm,
	controller=controller,
	use_vision=False,
	max_actions_per_step=10,
)


async def main():
	await agent.run(max_steps=25)


asyncio.run(main())
