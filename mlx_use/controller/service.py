import asyncio
import json
import logging

import Cocoa
from playwright.async_api import Page

from mlx_use.agent.views import ActionModel, ActionResult
from mlx_use.browser.context import BrowserContext
from mlx_use.controller.registry.service import Registry
from mlx_use.controller.views import (
	ClickElementAction,
	DoneAction,
	ExtractPageContentAction,
	GoToUrlAction,
	InputTextAction,
	OpenTabAction,
	ScrollAction,
	SearchGoogleAction,
	SendKeysAction,
	SwitchTabAction,
)
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

		@self.registry.action('Click element')
		async def click_element(index: int):
			return 'done'

		@self.registry.action(
			'Open a mac app',
		)
		async def open_app(app_name: str):
			workspace = Cocoa.NSWorkspace.sharedWorkspace()
			print(f'\nLaunching {app_name} app...')
			success = workspace.launchApplication_(app_name)
			if not success:
				print(f'❌ Failed to launch {app_name} app\n ending with {success}')
				return
			# Find Calculator app
			await asyncio.sleep(1)  # Give it a moment to appear in running apps
			for app in workspace.runningApplications():
				if app.bundleIdentifier() and app_name in app.bundleIdentifier().lower():
					print(f'Bundle ID: {app.bundleIdentifier()}')
					print(f'PID: {app.processIdentifier()}')
					break

			return f'We opened the app {app_name}'

	def action(self, description: str, **kwargs):
		"""Decorator for registering custom actions

		@param description: Describe the LLM what the function does (better description == better function calling)
		"""
		return self.registry.action(description, **kwargs)

	@time_execution_async('--multi-act')
	async def multi_act(
		self, actions: list[ActionModel], browser_context: BrowserContext, check_for_new_elements: bool = True
	) -> list[ActionResult]:
		"""Execute multiple actions"""
		results = []

		session = await browser_context.get_session()
		cached_selector_map = session.cached_state.selector_map
		cached_path_hashes = set(e.hash.branch_path_hash for e in cached_selector_map.values())
		await browser_context.remove_highlights()

		for i, action in enumerate(actions):
			if action.get_index() is not None and i != 0:
				new_state = await browser_context.get_state()
				new_path_hashes = set(e.hash.branch_path_hash for e in new_state.selector_map.values())
				if check_for_new_elements and not new_path_hashes.issubset(cached_path_hashes):
					# next action requires index but there are new elements on the page
					logger.info(f'Something new appeared after action {i} / {len(actions)}')
					break

			results.append(await self.act(action, browser_context))

			logger.debug(f'Executed action {i + 1} / {len(actions)}')
			if results[-1].is_done or results[-1].error or i == len(actions) - 1:
				break

			await asyncio.sleep(browser_context.config.wait_between_actions)
			# hash all elements. if it is a subset of cached_state its fine - else break (new elements on page)

		return results

	@time_execution_sync('--act')
	async def act(self, action: ActionModel, browser_context: BrowserContext) -> ActionResult:
		"""Execute an action"""
		try:
			for action_name, params in action.model_dump(exclude_unset=True).items():
				if params is not None:
					# remove highlights
					result = await self.registry.execute_action(action_name, params, browser=browser_context)
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
