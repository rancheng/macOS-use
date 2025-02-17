import asyncio
import json
import logging
from typing import Literal
import subprocess

import Cocoa
from playwright.async_api import Page

from mlx_use.agent.views import ActionModel, ActionResult
from mlx_use.controller.registry.service import Registry
from mlx_use.controller.views import (
	DoneAction,
	InputTextAction,
	ClickElementAction,
	OpenAppAction,
	RightClickElementAction,
	AppleScriptAction,
	ScrollElementAction
)
from mlx_use.mac.actions import click, type_into, right_click, scroll
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
					
					if not element_to_input_text.enabled:
						msg = f'❌ Cannot input text: Element is disabled: {element_to_input_text}'
						print(msg)
						return ActionResult(extracted_content=msg, error=msg)
						
					input_successful = type_into(element_to_input_text, text, submit)
					if input_successful:
						print('✅ Input successful!')
						return ActionResult(extracted_content=f'Successfully input text into element with index {index}')
					else:
						msg = f'❌ Input failed for element with index {index}'
						print(msg)
						return ActionResult(extracted_content=msg, error=msg)
				else:
					msg = f'❌ Invalid index: {index}'
					print(msg)
					return ActionResult(extracted_content=msg, error=msg)
			except Exception as e:
				msg = f'❌ An error occurred: {str(e)}'
				print(msg)
				return ActionResult(extracted_content=msg, error=msg)

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
					
					if not element_to_click.enabled:
						msg = f'❌ Cannot click: Element is disabled: {element_to_click}'
						print(msg)
						return ActionResult(extracted_content=msg, error=msg)
						
					click_successful = click(element_to_click)
					if click_successful:
						print('✅ Click successful!')
						return ActionResult(extracted_content=f'Successfully clicked element with index {index}')
					else:
						msg = f'❌ Click failed for element with index {index}'
						print(msg)
						return ActionResult(extracted_content=msg, error=msg)
				else:
					msg = f'❌ Invalid index: {index}'
					print(msg)
					return ActionResult(extracted_content=msg, error=msg)
			except Exception as e:
				msg = f'❌ An error occurred: {str(e)}'
				print(msg)
				return ActionResult(extracted_content=msg, error=msg)
		
		@self.registry.action(
			'Right click element',
			param_model=RightClickElementAction,
			requires_mac_builder=True
		)
		async def right_click_element(index: int, mac_tree_builder: MacUITreeBuilder):
			logger.info(f'Right clicking element {index}')
			try:
				if index in mac_tree_builder._element_cache:
					element_to_right_click = mac_tree_builder._element_cache[index]
					print(f'Attempting to right click: {element_to_right_click}')
					
					if not element_to_right_click.enabled:
						msg = f'❌ Cannot right click: Element is disabled: {element_to_right_click}'
						print(msg)
						return ActionResult(extracted_content=msg, error=msg)
						
					right_click_successful = right_click(element_to_right_click)
					if right_click_successful:
						print('✅ Right click successful!')
						return ActionResult(extracted_content=f'Successfully right clicked element with index {index}')
					else:
						msg = f'❌ Right click failed for element with index {index}'
						print(msg)
						return ActionResult(extracted_content=msg, error=msg)
				else:
					msg = f'❌ Invalid index: {index}'
					print(msg)
					return ActionResult(extracted_content=msg, error=msg)
			except Exception as e:
				msg = f'❌ An error occurred: {str(e)}'
				print(msg)
				return ActionResult(extracted_content=msg, error=msg)

		@self.registry.action(
			'Scroll element',
			param_model=ScrollElementAction,
			requires_mac_builder=True
		)
		async def scroll_element(index: int, direction: Literal['up', 'down', 'left', 'right'], mac_tree_builder: MacUITreeBuilder):
			logger.info(f'Scrolling element {index} {direction}')
			try:
				if index in mac_tree_builder._element_cache:
					element_to_scroll = mac_tree_builder._element_cache[index]
					print(f'Attempting to scroll {direction}: {element_to_scroll}')
					
					if not element_to_scroll.enabled:
						msg = f'❌ Cannot scroll: Element is disabled: {element_to_scroll}'
						print(msg)
						return ActionResult(extracted_content=msg, error=msg)
						
					scroll_successful = scroll(element_to_scroll, direction)
					if scroll_successful:
						print('✅ Scroll successful!')
						return ActionResult(extracted_content=f'Successfully scrolled element with index {index} {direction}')
					else:
						msg = f'❌ Scroll failed for element with index {index}'
						print(msg)
						return ActionResult(extracted_content=msg, error=msg)
				else:
					msg = f'❌ Invalid index: {index}'
					print(msg)
					return ActionResult(extracted_content=msg, error=msg)
			except Exception as e:
				msg = f'❌ An error occurred: {str(e)}'
				print(msg)
				return ActionResult(extracted_content=msg, error=msg)

		@self.registry.action(
			'Open a mac app',
			param_model=OpenAppAction
		)
		async def open_app(app_name: str):
			workspace = Cocoa.NSWorkspace.sharedWorkspace()
			print(f'\nLaunching app: {app_name}...')
			success = workspace.launchApplication_(app_name)
			if success:
				print(f'✅ Launched app using name: {app_name}')
			else:
				print(f'❌ Failed to launch app with name: {app_name}. Trying lowercased...')
				app_name_lower = app_name.lower()
				success = workspace.launchApplication_(app_name_lower)
				if success:
					print(f'✅ Launched app using lowercased name: {app_name_lower}')
				else:
					msg = f'❌ Failed to launch app: {app_name} (and lowercased: {app_name_lower})'
					print(msg)
					return ActionResult(extracted_content=msg, error=msg)

			await asyncio.sleep(1)  # Give it a moment to appear in running apps
			pid = None
			for app in workspace.runningApplications():
				if app.bundleIdentifier() and app_name.lower() in app.bundleIdentifier().lower():
					print(f'Bundle ID: {app.bundleIdentifier()}')
					pid = app.processIdentifier()
					print(f'PID: {pid}')
					break
			
			if pid is None:
				msg = f'Could not find running app with name: {app_name} in running applications.'
				print(msg)
				return ActionResult(extracted_content=msg, error=msg)
			else:
				return ActionResult(extracted_content=f'Successfully opened app {app_name}', current_app_pid=pid)
			
		@self.registry.action(
			'Run a AppleScript',
			param_model=AppleScriptAction
		)
		async def run_apple_script(script: str):
			logger.info(f'Running AppleScript: {script}')
			try:
				subprocess.run(['osascript', '-e', script])
				return ActionResult(extracted_content=f'Successfully ran AppleScript: {script}')
			except Exception as e:
				error_msg = f'Failed to run AppleScript: {str(e)}'
				logger.error(error_msg)
				return ActionResult(extracted_content=error_msg, error=error_msg)

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
			msg = f'Error executing action: {str(e)}'
			logger.error(msg)
			return ActionResult(extracted_content=msg, error=msg)

class NoParamsAction(ActionModel):
	"""
	Simple parameter model requiring no arguments.
	"""
	pass
