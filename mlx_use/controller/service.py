import asyncio
import json
import logging

import Cocoa
from playwright.async_api import Page

from mlx_use.agent.views import ActionModel, ActionResult
from mlx_use.controller.registry.service import Registry
from mlx_use.controller.views import (
	DoneAction,
	InputTextAction,
	ClickElementAction,
	OpenAppAction
)
from mlx_use.mac.actions import click, type_into
from mlx_use.mac.tree import MacUITreeBuilder
from mlx_use.utils import time_execution_async, time_execution_sync

logger = logging.getLogger(__name__)


class Controller:
	def __init__(
		self,
		exclude_actions: list[str] = [],
	):
		self.exclude_actions = exclude_actions
		self.registry = Registry(exclude_actions)
		self._register_default_actions()

	def _register_default_actions(self):
		"""Register all default browser actions"""

		@self.registry.action(
				'Complete task with text for the user',
				param_model=DoneAction)
		async def done(text: str):
			return ActionResult(extracted_content=text, is_done=True)

		@self.registry.action(
				'Input text', 
				param_model=InputTextAction,
				requires_mac_builder=True)
		async def input_text(index: int, text: str, submit: bool, mac_tree_builder: MacUITreeBuilder):
			logger.info(f'Inputting text {text} into element with index {index}')

			try:
				if index in mac_tree_builder._element_cache:
					element_to_input_text = mac_tree_builder._element_cache[index]
					print(f'Attempting to input text: {element_to_input_text}')
					input_successful = type_into(element_to_input_text, text, submit)
					if input_successful:
						print('✅ Input successful!')
					else:
						print('❌ Input failed.')
				else:
					print('❌ Invalid index.')
			except ValueError:
				print("❌ Invalid input. Please enter a number or 'q'.")
			except Exception as e:
				print(f'❌ An error occurred: {e}')

			return ActionResult(extracted_content=f'input text into element with index {index}')

		@self.registry.action(
				'Click element',
				param_model=ClickElementAction,
				  requires_mac_builder=True)
		async def click_element(index: int, mac_tree_builder: MacUITreeBuilder):
			logger.info(f'Clicking element {index}')

			try:
				if index in mac_tree_builder._element_cache:
					element_to_click = mac_tree_builder._element_cache[index]
					print(f'Attempting to click: {element_to_click}')
					click_successful = click(element_to_click)
					if click_successful:
						print('✅ Click successful!')
					else:
						print('❌ Click failed.')
				else:
					print('❌ Invalid index.')
			except ValueError:
				print("❌ Invalid input. Please enter a number or 'q'.")
			except Exception as e:
				print(f'❌ An error occurred: {e}')

			return ActionResult(extracted_content=f'clicked element with index {index}')

		@self.registry.action(
			'Open a mac app always use lowercase',
			param_model=OpenAppAction
		)
		async def open_app(app_name: str):
			workspace = Cocoa.NSWorkspace.sharedWorkspace()
			app_name = app_name.lower()
			print(f'\nLaunching {app_name} app...')
			success = workspace.launchApplication_(app_name)
			if not success:
				print(f'❌ Failed to launch {app_name} app\n ending with {success}')
				return
			# Find Calculator app
			await asyncio.sleep(1)  # Give it a moment to appear in running apps
			pid = None
			for app in workspace.runningApplications():
				if app.bundleIdentifier() and app_name in app.bundleIdentifier().lower():
					print(f'Bundle ID: {app.bundleIdentifier()}')
					pid = app.processIdentifier()
					print(f'PID: {pid}')
					break
			if pid is None:
				msg = f'Could not find {app_name} app in:\n {workspace.runningApplications()}'
				print(msg)
				return ActionResult(extracted_content=msg)
			else:
				return ActionResult(extracted_content=f'We opened the app {app_name}', current_app_pid=pid)

	def action(self, description: str, **kwargs):
		"""Decorator for registering custom actions

		@param description: Describe the LLM what the function does (better description == better function calling)
		"""
		return self.registry.action(description, **kwargs)

	@time_execution_async('--multi-act')
	async def multi_act(
		self, actions: list[ActionModel], mac_tree_builder: MacUITreeBuilder, check_for_new_elements: bool = True
	) -> list[ActionResult]:
		"""Execute multiple actions"""
		results = []

		for i, action in enumerate(actions):
			results.append(await self.act(action, mac_tree_builder))

			logger.debug(f'Executed action {i + 1} / {len(actions)}')
			if results[-1].is_done or results[-1].error or i == len(actions) - 1:
				break

		return results

	@time_execution_sync('--act')
	async def act(self, action: ActionModel, mac_tree_builder: MacUITreeBuilder) -> ActionResult:
		"""Execute an action"""
		try:
			for action_name, params in action.model_dump(exclude_unset=True).items():
				if params is not None:
					# remove highlights
					result = await self.registry.execute_action(action_name, params, mac_tree_builder=mac_tree_builder)
					if isinstance(result, str):
						return ActionResult(extracted_content=result)
					elif isinstance(result, ActionResult):
						return result
					elif result is None:
						return ActionResult()
					else:
						raise ValueError(f'Invalid action result type: {type(result)} of {result}')
			return ActionResult()
		except Exception as e:
			raise e
