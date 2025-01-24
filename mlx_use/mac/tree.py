# --- START OF FILE mac_use/mac/tree.py ---
import asyncio

# --- START OF FILE mac_use/mac/actions.py ---
import logging
from typing import Callable, Dict, List, Optional

import Cocoa
from ApplicationServices import AXUIElementPerformAction, AXUIElementSetAttributeValue, kAXPressAction, kAXValueAttribute
from Foundation import NSString

from mlx_use.mac.element import MacElementNode

logger = logging.getLogger(__name__)

import Cocoa
import objc
from ApplicationServices import (
	AXError,
	AXUIElementCopyActionNames,
	AXUIElementCopyAttributeValue,
	AXUIElementCreateApplication,
	kAXChildrenAttribute,
	kAXDescriptionAttribute,
	kAXErrorAPIDisabled,
	kAXErrorAttributeUnsupported,
	kAXErrorCannotComplete,
	kAXErrorFailure,
	kAXErrorIllegalArgument,
	kAXErrorSuccess,  # Import kAXErrorSuccess
	kAXMainWindowAttribute,
	kAXRoleAttribute,
	kAXTitleAttribute,
	kAXValueAttribute,
	kAXWindowsAttribute,
)
from CoreFoundation import CFRunLoopAddSource, CFRunLoopGetCurrent, kCFRunLoopDefaultMode

from .element import MacElementNode

logger = logging.getLogger(__name__)


class MacUITreeBuilder:
	def __init__(self):
		self.highlight_index = 0
		self._element_cache = {}
		self._observers = {}
		self._processed_elements = set()  # To avoid infinite recursion

		self._current_app_pid = None

	def _setup_observer(self, pid: int) -> bool:
		"""Setup accessibility observer for an application"""
		return True  #  Temporarily always return True

	def _get_attribute(self, element: 'AXUIElement', attribute: str) -> any:
		"""Safely get an accessibility attribute with error reporting"""
		try:
			error, value_ref = AXUIElementCopyAttributeValue(element, attribute, None)
			if error == kAXErrorSuccess:
				return value_ref
			elif error == kAXErrorAttributeUnsupported:
				logger.debug(f"Attribute '{attribute}' is not supported for this element.")
				return None
			else:
				logger.debug(f"Error getting attribute '{attribute}': {error}")
				return None
		except Exception as e:
			logger.debug(f"Exception getting attribute '{attribute}': {str(e)}")
			return None

	def _get_actions(self, element: 'AXUIElement') -> List[str]:
		"""Get available actions for an element"""
		try:
			actions = AXUIElementCopyActionNames(element, None)
			return actions
		except Exception as e:
			print(f'Error getting actions: {e}')
			return []

	async def _process_element(
		self, element: 'AXUIElement', pid: int, parent: Optional[MacElementNode] = None
	) -> Optional[MacElementNode]:
		"""Process a single UI element"""
		element_identifier = str(element)
		if element_identifier in self._processed_elements:
			return None  # Avoid processing the same element again

		self._processed_elements.add(element_identifier)

		try:
			role = self._get_attribute(element, kAXRoleAttribute)
			title = self._get_attribute(element, kAXTitleAttribute)
			value = self._get_attribute(element, kAXValueAttribute)
			description = self._get_attribute(element, kAXDescriptionAttribute)
			is_enabled = self._get_attribute(element, 'AXEnabled')  # Using the string representation as a fallback

			if not role:
				return None

			node = MacElementNode(
				role=role,
				identifier=element_identifier,
				attributes={},
				is_visible=bool(is_enabled) if is_enabled is not None else True,
				parent=parent,
				app_pid=pid,
			)
			if title:
				node.attributes['title'] = title
			if value:
				node.attributes['value'] = value
			if description:
				node.attributes['description'] = description
			node._element = element

			actions = self._get_actions(element)

			# Determine interactivity based on role and наличие actions
			interactive_roles = ['AXButton', 'AXTextField', 'AXCheckBox', 'AXRadioButton', 'AXComboBox', 'AXMenuButton']
			node.is_interactive = role in interactive_roles or bool(actions)

			if node.is_interactive:
				node.highlight_index = self.highlight_index
				self._element_cache[self.highlight_index] = node
				self.highlight_index += 1

			children_ref = self._get_attribute(element, kAXChildrenAttribute)
			if children_ref:
				if isinstance(children_ref, objc.lookUpClass('NSArray')):
					for child in children_ref:
						child_node = await self._process_element(child, pid, node)
						if child_node:
							node.children.append(child_node)
				else:
					logger.warning(f'Unexpected type for children: {type(children_ref)}, value: {children_ref}')

			return node

		except Exception as e:
			print(f'Error processing element: {e}')
			return None

	async def build_tree(self, pid: Optional[int] = None) -> Optional[MacElementNode]:
		"""Build UI tree for a specific application"""
		try:
			if pid is None and self._current_app_pid is None:
				print('No PID provided and no current app PID set')
				raise ValueError('No PID provided and no current app PID set')

			if pid is not None:
				self._current_app_pid = pid

				if not self._setup_observer(self._current_app_pid):
					print('Failed to setup accessibility observer')
					return None

			print(f'\nAttempting to create AX element for pid {self._current_app_pid}')
			app_ref = AXUIElementCreateApplication(self._current_app_pid)

			print('Testing accessibility permissions (Role)...')
			error, role_attr = AXUIElementCopyAttributeValue(app_ref, kAXRoleAttribute, None)
			if error == kAXErrorSuccess:
				print(f'✅ Successfully got role attribute: ({error}, {role_attr})')
			else:
				print(f'❌ Error getting role attribute: {error}')
				if error == kAXErrorAPIDisabled:
					print('Accessibility is not enabled. Please enable it in System Settings.')
				return None

			root = MacElementNode(
				role='application',
				identifier=str(app_ref),
				attributes={},
				is_visible=True,
				app_pid=self._current_app_pid,
			)
			root._element = app_ref

			# Try to get the main window
			print('\nTrying to get the main window...')
			error, main_window_ref = AXUIElementCopyAttributeValue(app_ref, kAXMainWindowAttribute, None)
			if error == kAXErrorSuccess and main_window_ref:
				print(f'✅ Found main window: ({error}, {main_window_ref})')
				window_node = await self._process_element(main_window_ref, self._current_app_pid, root)
				if window_node:
					root.children.append(window_node)
			else:
				print(f'⚠️ Could not get main window or an error occurred: {error}')

			return root

		except Exception as e:
			print(f'Error building tree: {str(e)}')
			import traceback

			traceback.print_exc()
			return None

	def cleanup(self):
		"""Cleanup observers"""
		pass  # Temporarily do nothing
