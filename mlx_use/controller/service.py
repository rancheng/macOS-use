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
			logger.debug(f'Inputting text {text} into element with index {index}')

			try:
				if index in mac_tree_builder._element_cache:
					element_to_input_text = mac_tree_builder._element_cache[index]
					
					if not element_to_input_text.enabled:
						msg = f'❌ Cannot input text: Element is disabled: {element_to_input_text}'
						return ActionResult(extracted_content=msg, error=msg)
						
					input_successful = type_into(element_to_input_text, text, submit)
					if input_successful:
						return ActionResult(extracted_content=f'Successfully input text into element with index {index}')
					else:
						msg = f'❌ Input failed for element with index {index}'
						return ActionResult(extracted_content=msg, error=msg)
				else:
					msg = f'❌ Invalid index: {index}'
					return ActionResult(extracted_content=msg, error=msg)
			except Exception as e:
				msg = f'❌ An error occurred: {str(e)}'
				logging.error(msg)
				return ActionResult(extracted_content=msg, error=msg)

		@self.registry.action(
				'Click element and choose action',
				param_model=ClickElementAction,
				  requires_mac_builder=True)
		async def click_element(index: int, action: str, mac_tree_builder: MacUITreeBuilder):
			logger.debug(f'Clicking element {index}')

			try:
				if index in mac_tree_builder._element_cache:
					element_to_click = mac_tree_builder._element_cache[index]
					
					if not element_to_click.enabled:
						msg = f'❌ Cannot click: Element is disabled: {element_to_click}'
						logging.error(msg)
						return ActionResult(extracted_content=msg, error=msg)
						
					click_successful = click(element_to_click, action)
					if click_successful:
						logger.debug(f'Successfully clicked element with index {index}')
						return ActionResult(
							extracted_content=f'Successfully clicked element with index {index}',
							include_in_memory=True
						)
					else:
						msg = f'❌ Click failed for element with index {index}'
						logging.error(msg)
						return ActionResult(extracted_content=msg, error=msg)
				else:
					msg = f'❌ Invalid index: {index}'
					logging.error(msg)
					return ActionResult(extracted_content=msg, error=msg)
			except Exception as e:
				msg = f'❌ An error occurred: {str(e)}'
				logging.error(msg)
				return ActionResult(extracted_content=msg, error=msg)
		
		@self.registry.action(
			'Right click element',
			param_model=RightClickElementAction,
			requires_mac_builder=True
		)
		async def right_click_element(index: int, mac_tree_builder: MacUITreeBuilder):
			logger.debug(f'Right clicking element {index}')
			try:
				if index in mac_tree_builder._element_cache:
					element_to_right_click = mac_tree_builder._element_cache[index]

					if not element_to_right_click.enabled:
						msg = f'❌ Cannot right click: Element is disabled: {element_to_right_click}'
						return ActionResult(extracted_content=msg, error=msg)
						
					right_click_successful = right_click(element_to_right_click)
					if right_click_successful:
						return ActionResult(extracted_content=f'Successfully right clicked element with index {index}')
					else:
						msg = f'❌ Right click failed for element with index {index}'
						return ActionResult(extracted_content=msg, error=msg)
				else:
					msg = f'❌ Invalid index: {index}'
					return ActionResult(extracted_content=msg, error=msg)
			except Exception as e:
				msg = f'❌ An error occurred: {str(e)}'
				logging.error(msg)
				return ActionResult(extracted_content=msg, error=msg)

		@self.registry.action(
			'Scroll element',
			param_model=ScrollElementAction,
			requires_mac_builder=True
		)
		async def scroll_element(index: int, direction: Literal['up', 'down', 'left', 'right'], mac_tree_builder: MacUITreeBuilder):
			logger.debug(f'Scrolling element {index} {direction}')
			try:
				if index in mac_tree_builder._element_cache:
					element_to_scroll = mac_tree_builder._element_cache[index]

					if not element_to_scroll.enabled:
						msg = f'❌ Cannot scroll: Element is disabled: {element_to_scroll}'
						return ActionResult(extracted_content=msg, error=msg)
						
					scroll_successful = scroll(element_to_scroll, direction)
					if scroll_successful:
						return ActionResult(extracted_content=f'Successfully scrolled element with index {index} {direction}')
					else:
						msg = f'❌ Scroll failed for element with index {index}'
						return ActionResult(extracted_content=msg, error=msg)
				else:
					msg = f'❌ Invalid index: {index}'
					return ActionResult(extracted_content=msg, error=msg)
			except Exception as e:
				msg = f'❌ An error occurred: {str(e)}'
				logging.error(msg)
				return ActionResult(extracted_content=msg, error=msg)

		@self.registry.action(
			'Open a mac app',
			param_model=OpenAppAction
		)
		async def open_app(app_name: str):
			workspace = Cocoa.NSWorkspace.sharedWorkspace()
			logging.info(f'\nLaunching app: {app_name}...')
			success = workspace.launchApplication_(app_name)
			if success:
				logging.info(f'✅ Launched app using name: {app_name}')
			else:
				logging.error(f'❌ Failed to launch app with name: {app_name}. Trying lowercased...')
				app_name_lower = app_name.lower()
				success = workspace.launchApplication_(app_name_lower)
				if success:
					logging.info(f'✅ Launched app using lowercased name: {app_name_lower}')
				else:
					msg = f'❌ Failed to launch app: {app_name} (and lowercased: {app_name_lower})'
					return ActionResult(extracted_content=msg, error=msg)

			await asyncio.sleep(1)  # Give it a moment to appear in running apps
			pid = None
			for app in workspace.runningApplications():
				if app.bundleIdentifier() and app_name.lower() in app.bundleIdentifier().lower():
					logging.debug(f'Bundle ID: {app.bundleIdentifier()}')
					pid = app.processIdentifier()
					logging.debug(f'PID: {pid}')
					break

			# If no PID is found, try to find the app by name with pgrep -i 
			if pid is None:
				try:
					result = subprocess.run(
						['pgrep', '-i', app_name],
						capture_output=True,
						text=True
					)
					if result.returncode == 0 and result.stdout.strip():
						# pgrep might return multiple PIDs, take the first one
						pid = int(result.stdout.strip().split('\n')[0])
						logging.debug(f'Found PID using pgrep: {pid}')
					else:
						logging.error(f'❌ Failed to find PID for app: {app_name} with pgrep')
				except Exception as e:
					logging.error(f'❌ Error while running pgrep: {str(e)}')
				
			if pid is None:
				msg = f'Could not find running app with name: {app_name} in running applications.'
				logging.error(msg)
				logger.error(f'running apps: {workspace.runningApplications()}')
				return ActionResult(extracted_content=msg, error=msg)
			else:
				return ActionResult(extracted_content=f'Successfully opened app {app_name}', current_app_pid=pid)
			
		@self.registry.action(
			'Run a AppleScript',
			param_model=AppleScriptAction
		)
		async def run_apple_script(script: str):
			logger.debug(f'Running AppleScript: {script}')
			
			# Wrap the original script in error handling and return value logic
			wrapped_script = f'''
				try
					{script}
					return "OK"
				on error errMsg
					return "ERROR: " & errMsg
				end try
			'''
			
			try:
				result = subprocess.run(
					['osascript', '-e', wrapped_script],
					capture_output=True,
					text=True
				)
				
				if result.returncode == 0:
					output = result.stdout.strip()
					if output == "OK":
						return ActionResult(extracted_content="Success")
					elif output.startswith("ERROR:"):
						error_msg = output
						logger.error(error_msg)
						return ActionResult(extracted_content=error_msg, error=error_msg)
					else:
						return ActionResult(extracted_content=output)
				else:
					error_msg = f"AppleScript failed with return code {result.returncode}: {result.stderr.strip()}"
					logger.error(error_msg)
					return ActionResult(extracted_content=error_msg, error=error_msg)
					
			except Exception as e:
				error_msg = f"Failed to run AppleScript: {str(e)}"
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
