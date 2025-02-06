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
	OpenAppAction,
	RightClickElementAction
)
from mlx_use.mac.actions import click, type_into, right_click
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
					right_click_successful = right_click(element_to_right_click)
					if right_click_successful:
						print('✅ Right click successful!')
					else:
						print('❌ Right click failed.')
				else:
					print('❌ Invalid index.')
			except Exception as e:
				print(f'❌ An error occurred: {e}')

			return ActionResult(extracted_content=f'right clicked element with index {index}')

		@self.registry.action(
			'Open a mac app',
			param_model=OpenAppAction
		)
		async def open_app(app_name: str):
			workspace = Cocoa.NSWorkspace.sharedWorkspace()
			print(f'\nLaunching app: {app_name}...')
			success = workspace.launchApplication_(app_name) # Try launching as is first
			if success:
				print(f'✅ Launched app using name: {app_name}')
			else:
				print(f'❌ Failed to launch app with name: {app_name}. Trying lowercased...')
				app_name_lower = app_name.lower() # Fallback to lowercased
				success = workspace.launchApplication_(app_name_lower)
				if success:
					print(f'✅ Launched app using lowercased name: {app_name_lower}')
				else:
					print(f'❌ Failed to launch app with lowercased name: {app_name_lower}')
					msg = f'Failed to launch app: {app_name} (and lowercased: {app_name_lower})'
					logger.debug(msg)
					return ActionResult(extracted_content=msg, error=msg) # Return error if both fail

			if not success: # If still not successful after both attempts
				return ActionResult(extracted_content=f'Failed to open app {app_name}')

			await asyncio.sleep(1)  # Give it a moment to appear in running apps
			pid = None
			for app in workspace.runningApplications():
				if app.bundleIdentifier() and app_name.lower() in app.bundleIdentifier().lower(): # keep lowercasing for bundle ID check for broader match
					print(f'Bundle ID: {app.bundleIdentifier()}')
					pid = app.processIdentifier()
					print(f'PID: {pid}')
					break
			if pid is None:
				if success:
					pid = app.processIdentifier()
					return ActionResult(extracted_content=f'We opened the app {app_name}', current_app_pid=pid)
				else:
					msg = f'Could not find running app with name: {app_name} in running applications.'
					logger.debug(msg)
					return ActionResult(extracted_content=msg, error=msg) # Return error if PID not found
			else:
				return ActionResult(extracted_content=f'We opened the app {app_name}', current_app_pid=pid)

		@self.registry.action(
			'List running mac apps (returns localized name, bundle id, app path, and PID)',
			param_model=None,
			requires_mac_builder=False
		)
		async def list_running_apps():
			workspace = Cocoa.NSWorkspace.sharedWorkspace()
			apps = []
			for app in workspace.runningApplications():
				# Convert attributes explicitly to strings to ensure JSON-serializability
				localized_name = str(app.localizedName()) if app.localizedName() is not None else ""
				bundle_identifier = str(app.bundleIdentifier()) if app.bundleIdentifier() is not None else ""
				# Use str() to convert the app path (returned from the native selector) into a Python string
				app_path = str(app.bundleURL().path) if app.bundleURL() is not None else "Path not available"
				pid = app.processIdentifier()
				apps.append({
					"localized_name": localized_name,
					"bundle_identifier": bundle_identifier,
					"path": app_path,
					"pid": pid
				})
			output = json.dumps({"apps": apps}, indent=2)
			return ActionResult(extracted_content=output, current_app_pid=None)

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

class NoParamsAction(ActionModel):
	"""
	Simple parameter model requiring no arguments.
	"""
	pass
