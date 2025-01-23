"""
MacOS application controller using Accessibility API
"""

import asyncio
import logging
import os
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Optional

import objc
from ApplicationServices import (
	AXObserverCreate,
	AXUIElementCopyAttributeValue,
	AXUIElementCreateApplication,
	AXUIElementPerformAction,
	kAXRaiseAction,
	kAXUIElementDestroyedNotification,
	kAXWindowsAttribute,
)
from CoreFoundation import CFRunLoopGetCurrent

from mlx_use.mac.actions import click, type_into
from mlx_use.mac.tree import MacUITreeBuilder
from mlx_use.mac.views import MacAppInfo, MacUIState

if TYPE_CHECKING:
	from mlx_use.mac.manager import MacManager

logger = logging.getLogger(__name__)


@dataclass
class MacAppConfig:
	"""Configuration for Mac application interaction"""

	bundle_id: str
	highlight_elements: bool = True
	ui_poll_interval: float = 0.5
	max_retries: int = 3
	retry_delay: float = 1.0


@dataclass
class MacAppSession:
	"""Represents an active application session"""

	pid: int
	tree_builder: MacUITreeBuilder
	observer: Optional[objc.objc_object] = None


class MacAppContext:
	def __init__(self, manager: 'MacManager', config: MacAppConfig = MacAppConfig(bundle_id='com.apple.Notes')):
		self.context_id = str(uuid.uuid4())
		self.config = config
		self.manager = manager
		self.session: Optional[MacAppSession] = None
		self._current_pid: Optional[int] = None

	async def __aenter__(self):
		await self.initialize()
		return self

	async def __aexit__(self, exc_type, exc_val, exc_tb):
		await self.close()

	async def initialize(self):
		"""Initialize application session"""
		logger.info(f'Initializing Mac app context for {self.config.bundle_id}')
		pid = await self._get_app_pid()

		if not pid:
			raise RuntimeError(f'Failed to launch/find app with bundle ID {self.config.bundle_id}')

		self.session = MacAppSession(pid=pid, tree_builder=MacUITreeBuilder(), observer=self._setup_observer(pid))

	def _setup_observer(self, pid: int) -> objc.objc_object:
		"""Set up accessibility observer for UI changes"""

		def callback(observer, element, notification, userdata):
			asyncio.create_task(self._handle_ui_change())

		error, observer = AXObserverCreate(pid, callback)
		if error != 0:
			logger.error('Failed to create AXObserver')
			return None

		app_ref = AXUIElementCreateApplication(pid)
		AXObserverAddNotification(observer, app_ref, kAXUIElementDestroyedNotification, None)
		AXObserverAddNotification(observer, app_ref, kAXFocusedUIElementChangedNotification, None)

		# Add observer to run loop
		CFRunLoopGetCurrent().addSource(AXObserverGetRunLoopSource(observer), kCFRunLoopDefaultMode)
		return observer

	async def _get_app_pid(self) -> Optional[int]:
		"""Get or launch target application PID"""
		ws = NSWorkspace.sharedWorkspace()
		app = (
			ws.runningApplications()
			.filteredArrayUsingPredicate_(NSPredicate.predicateWithFormat_('bundleIdentifier == %@', self.config.bundle_id))
			.firstObject()
		)

		if not app or not app.isRunning():
			success = ws.launchApplication_(self.config.bundle_id)
			if not success:
				return None
			await asyncio.sleep(2)  # Wait for app launch

		return app.processIdentifier() if app else None

	async def close(self):
		"""Clean up application session"""
		if self.session and self.session.observer:
			CFRunLoopGetCurrent().removeSource(AXObserverGetRunLoopSource(self.session.observer), kCFRunLoopDefaultMode)
		self.session = None

	async def get_state(self) -> MacUIState:
		"""Get current application UI state"""
		if not self.session:
			raise RuntimeError('Session not initialized')

		root = await self.session.tree_builder.build_tree(self.session.pid)
		return MacUIState(
			ui_tree=root,
			interactive_elements=root.get_clickable_elements_string(),
			active_pid=self.session.pid,
			frontmost_app=await self.get_frontmost_app(),
		)

	async def get_frontmost_app(self) -> str:
		"""Get name of frontmost application"""
		ws = NSWorkspace.sharedWorkspace()
		return ws.frontmostApplication().localizedName()

	async def perform_action(self, action: Dict) -> bool:
		"""Execute a Mac accessibility action"""
		action_type = action.get('type')
		index = action.get('index')

		if action_type == 'click':
			return await self.click_element(index)
		elif action_type == 'type':
			return await self.type_into_element(index, action.get('text'))
		elif action_type == 'focus_window':
			return await self.focus_window(action.get('window_index'))
		return False

	async def click_element(self, index: int) -> bool:
		"""Click element by index"""
		if not self.session:
			return False

		element = self.session.tree_builder._element_cache.get(index)
		return click(element) if element else False

	async def type_into_element(self, index: int, text: str) -> bool:
		"""Type text into element by index"""
		if not self.session:
			return False

		element = self.session.tree_builder._element_cache.get(index)
		return type_into(element, text) if element else False

	async def focus_window(self, window_index: int) -> bool:
		"""Focus a specific application window"""
		if not self.session:
			return False

		app_ref = AXUIElementCreateApplication(self.session.pid)
		error, windows = AXUIElementCopyAttributeValue(app_ref, kAXWindowsAttribute)

		if error == 0 and windows and window_index < len(windows):
			return AXUIElementPerformAction(windows[window_index], kAXRaiseAction) == 0
		return False

	async def _handle_ui_change(self):
		"""Handle UI change notifications"""
		logger.debug('UI change detected, updating state...')
		await self.get_state()

	async def get_state(self):
		pass
