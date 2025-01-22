import os
import sys

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import argparse
import asyncio

from mlx_use import Agent
from mlx_use.browser.browser import Browser, BrowserConfig
from mlx_use.controller.service import Controller

llm = ChatOpenAI(model='gpt-4o', temperature=0.0)
task = 'go to reddit and search for post about brower-use '


controller = Controller()


task = 'open the calculator app 10 times never stop.'


agent = Agent(
	task=task,
	llm=llm,
	controller=controller,
	use_vision=True,
	max_actions_per_step=1,
)


async def main():
	await agent.run(max_steps=25)

	input('Press Enter to close the browser...')


asyncio.run(main())
