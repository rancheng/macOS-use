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
	kAXErrorSuccess,
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
		self._processed_elements = set()
		self._current_app_pid = None
		self.max_depth = 30
		self.max_children = 250

		# Define interactive actions we care about
		self.INTERACTIVE_ACTIONS = {
			'AXPress',            # Most buttons and clickable elements
			'AXShowMenu',         # Menu buttons
			'AXIncrement',        # Spinners/steppers
			'AXDecrement',
			'AXConfirm',         # Dialogs
			'AXCancel',
			'AXRaise',           # Windows
			'AXSetValue'         # Text fields/inputs
		}

		# Actions that require scrolling
		self.SCROLL_ACTIONS = {
			'AXScrollLeftByPage',
			'AXScrollRightByPage',
			'AXScrollUpByPage',
			'AXScrollDownByPage'
		}

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
				# logger.debug(f"Attribute '{attribute}' is not supported for this element.")
				return None
			else:
				# logger.debug(f"Error getting attribute '{attribute}': {error}")
				return None
		except Exception as e:
			# logger.debug(f"Exception getting attribute '{attribute}': {str(e)}")
			return None

	def _get_actions(self, element: 'AXUIElement') -> List[str]:
		"""Get available actions for an element with proper error handling"""
		try:
			error, actions = AXUIElementCopyActionNames(element, None)
			if error == kAXErrorSuccess and actions:
				# Convert NSArray to Python list
				return list(actions)
			return []
		except Exception as e:
			logger.debug(f'Error getting actions: {e}')
			return []

	def _is_interactive(self, element: 'AXUIElement', role: str, actions: List[str]) -> bool:
		"""Determine if an element is truly interactive based on its role and actions."""
		if not actions:
			return False

		# Check if element has any interactive actions
		has_interactive = any(action in self.INTERACTIVE_ACTIONS for action in actions)
		has_scroll = any(action in self.SCROLL_ACTIONS for action in actions)
		
		# Special handling for text input fields
		if 'AXSetValue' in actions and role == 'AXTextField':
			enabled = self._get_attribute(element, 'AXEnabled')
			return bool(enabled)

		# Special handling for buttons with AXPress
		if 'AXPress' in actions and role in ['AXButton', 'AXLink']:
			enabled = self._get_attribute(element, 'AXEnabled')
			return bool(enabled)

		return has_interactive or has_scroll

	async def _process_element(self, element: 'AXUIElement', pid: int, parent: Optional[MacElementNode] = None, depth: int = 0) -> Optional[MacElementNode]:
		"""Process a single UI element"""
		element_identifier = str(element)
		
		if element_identifier in self._processed_elements:
			return None

		self._processed_elements.add(element_identifier)

		try:
			role = self._get_attribute(element, kAXRoleAttribute)
			if not role:
				return None

			# Get all possible attributes and actions
			actions = self._get_actions(element)
			
			# Create node with enhanced attributes
			node = MacElementNode(
				role=role,
				identifier=element_identifier,
				attributes={},
				is_visible=True,
				parent=parent,
				app_pid=pid,
			)
			node._element = element

			# Store the actions in the node's attributes for reference
			if actions:
				node.attributes['actions'] = actions

			# Get basic attributes
			title = self._get_attribute(element, kAXTitleAttribute)
			value = self._get_attribute(element, kAXValueAttribute)
			description = self._get_attribute(element, kAXDescriptionAttribute)
			is_enabled = self._get_attribute(element, 'AXEnabled')
			
			# Additional useful attributes
			position = self._get_attribute(element, 'AXPosition')
			size = self._get_attribute(element, 'AXSize')
			subrole = self._get_attribute(element, 'AXSubrole')

			# Update node attributes
			if title:
				node.attributes['title'] = title
			if value:
				node.attributes['value'] = value
			if description:
				node.attributes['description'] = description
			if is_enabled is not None:
				node.is_visible = bool(is_enabled)
				node.attributes['enabled'] = bool(is_enabled)
			if position:
				node.attributes['position'] = position
			if size:
				node.attributes['size'] = size
			if subrole:
				node.attributes['subrole'] = subrole

			# Determine if element should be included as context
			is_context = (role in ['AXStaticText', 'AXTextField'] and 
						'AXSetValue' not in actions and
						(parent is None or parent.role == 'AXWindow' or parent.is_interactive))

			# Determine interactivity based on actions
			node.is_interactive = self._is_interactive(element, role, actions)
			
			if node.is_interactive:
				node.highlight_index = self.highlight_index
				self._element_cache[self.highlight_index] = node
				self.highlight_index += 1
			elif is_context:
				node.highlight_index = None
				self._element_cache[f'ctx_{element_identifier}'] = node
				logger.debug(f'Added context element {role}')

			# Process children
			children_ref = self._get_attribute(element, kAXChildrenAttribute)
			if children_ref and depth < self.max_depth:
				try:
					children_count = len(list(children_ref))
					if children_count > self.max_children:
						logger.error(f"Max children limit ({self.max_children}) exceeded for element {role}. Found {children_count} children. Some elements will not be processed.")
					
					children_list = list(children_ref)[:self.max_children]
					for child in children_list:
						child_node = await self._process_element(child, pid, node, depth + 1)
						if child_node:
							node.children.append(child_node)
				except Exception as e:
					logger.warning(f"Error processing children: {e}")
			elif children_ref and depth >= self.max_depth:
				logger.error(f"Max depth limit ({self.max_depth}) reached for element {role}. Children at depth {depth} will not be processed.")

			return node

		except Exception as e:
			logger.error(f'Error processing element: {str(e)}')
			return None

	def cleanup(self):
		"""Cleanup observers and release resources"""
		# Clear the element cache to prevent holding on to stale references
		self._element_cache.clear()
		# Clear processed elements set
		self._processed_elements.clear()
		# Reset highlight index
		self.highlight_index = 0
		# Reset current app PID
		self._current_app_pid = None
		
		# Force garbage collection to release any Objective-C references
		import gc
		gc.collect()
		
		# Log the cleanup
		logger.debug("MacUITreeBuilder cleanup completed: all references released")

	def reset_state(self):
		"""Reset the state between major steps"""
		self.highlight_index = 0  # Reset index
		self._element_cache.clear()  # Clear cache
		self._processed_elements.clear()  # Clear processed set
		
		# Don't reset _current_app_pid here as it's needed for continuity between steps
		
		# Log the reset
		logger.debug("MacUITreeBuilder state reset")

	async def build_tree(self, pid: Optional[int] = None) -> Optional[MacElementNode]:
		"""Build UI tree for a specific application"""
		try:
			# Reset processed elements and cache before building new tree
			self._processed_elements.clear()
			self._element_cache.clear()
			self.highlight_index = 0

			if pid is None and self._current_app_pid is None:
				logger.debug('No app is currently open - waiting for app to be launched')
				raise ValueError('No app is currently open')

			if pid is not None:
				# Always update with the latest PID if provided
				self._current_app_pid = pid

			# Verify the process is still running
			import subprocess
			try:
				result = subprocess.run(['ps', '-p', str(self._current_app_pid)], capture_output=True, text=True)
				if result.returncode != 0:
					logger.error(f"Process with PID {self._current_app_pid} is no longer running")
					self._current_app_pid = None
					self.cleanup()
					return None
			except Exception as e:
				logger.error(f"Error checking process status: {e}")

			if not self._setup_observer(self._current_app_pid):
				logger.warning('Failed to setup accessibility observer')
				return None

			logger.debug(f'Creating AX element for pid {self._current_app_pid}')
			app_ref = AXUIElementCreateApplication(self._current_app_pid)

			logger.debug('Testing accessibility permissions (Role)...')
			error, role_attr = AXUIElementCopyAttributeValue(app_ref, kAXRoleAttribute, None)
			if error == kAXErrorSuccess:
				logger.debug(f'Successfully got role attribute: ({error}, {role_attr})')
			else:
				logger.error(f'Error getting role attribute: {error}')
				if error == kAXErrorAPIDisabled:
					logger.error('Accessibility is not enabled. Please enable it in System Settings.')
				elif error == -25204:
					logger.error(f'Error -25204: Accessibility connection failed. The app may have been closed or restarted.')
					# Reset current app PID as it's no longer valid
					self._current_app_pid = None
					# Force cleanup to release any hanging references
					self.cleanup()
				return None

			root = MacElementNode(
				role='application',
				identifier=str(app_ref),
				attributes={},
				is_visible=True,
				app_pid=self._current_app_pid,
			)
			root._element = app_ref

			logger.debug('Trying to get the main window...')
			error, main_window_ref = AXUIElementCopyAttributeValue(app_ref, kAXMainWindowAttribute, None)
			if error == '-25212':
				return None, "Window not found"
			if error != kAXErrorSuccess or not main_window_ref:
				logger.warning(f'Could not get main window (error: {error}), trying fallback attribute AXWindows')
				error, windows = AXUIElementCopyAttributeValue(app_ref, kAXWindowsAttribute, None)
				if error == kAXErrorSuccess and windows:
					try:
						windows_list = list(windows)
						if windows_list:
							main_window_ref = windows_list[0]
							logger.debug(f'Fallback: selected first window from AXWindows: {main_window_ref}')
						else:
							logger.warning("Fallback: AXWindows returned an empty list")
					except Exception as e:
						logger.error(f'Failed to iterate over AXWindows: {e}')
				else:
					logger.error(f'Fallback failed: could not get AXWindows (error: {error})')

			if main_window_ref:
				logger.debug(f'Found main window: {main_window_ref}')
				window_node = await self._process_element(main_window_ref, self._current_app_pid, root)
				if window_node:
					root.children.append(window_node)
			else:
				logger.error('Could not determine a main window for the application.')

			return root

		except Exception as e:
			if 'No app is currently open' not in str(e):
				logger.error(f'Error building tree: {str(e)}')
				import traceback
				traceback.print_exc()
			return None
