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

# Constant list of AX attributes for enhanced UI tree details 
AX_ATTRIBUTES = [
	"AXARIAAtomic",
	"AXARIALive",
	"AXARIARelevant",
	"AXActivationPoint",
	"AXAlternateUIVisible",
	"AXApplication",
	"AXBlockQuoteLevel",
	"AXButton",
	"AXCaretBrowsingEnabled",
	"AXCheckBox",
	"AXChildrenInNavigationOrder",
	"AXCloseButton",
	"AXCodeStyleGroup",
	"AXContainer",
	"AXContent",
	"AXContentList",
	"AXContents",
	"AXDOMClassList",
	"AXDOMIdentifier",
	"AXDescription",
	"AXEditableAncestor",
	"AXEdited",
	"AXElementBusy",
	"AXEmbeddedImageDescription",
	"AXEmptyGroup",
	"AXEnabled",
	"AXEndTextMarker",
	"AXFieldset",
	"AXFocusableAncestor",
	"AXFocused",
	"AXFrame",
	"AXFullScreen",
	"AXFullScreenButton",
	"AXGroup",
	"AXHasDocumentRoleAncestor",
	"AXHasPopup",
	"AXHasWebApplicationAncestor",
	"AXHeading",
	"AXHelp",
	"AXHighestEditableAncestor",
	"AXHorizontalOrientation",
	"AXHorizontalScrollBar",
	"AXIdentifier",
	"AXImage",
	"AXInlineText",
	"AXInsertionPointLineNumber",
	"AXInvalid",
	"AXLandmarkNavigation",
	"AXLandmarkRegion",
	"AXLanguage",
	"AXLayoutCount",
	"AXLink",
	"AXLinkRelationshipType",
	"AXLinkUIElements",
	"AXLinkedUIElements",
	"AXList",
	"AXListMarker",
	"AXLoaded",
	"AXLoadingProgress",
	"AXMain",
	"AXMaxValue",
	"AXMenuButton",
	"AXMinValue",
	"AXMinimizeButton",
	"AXMinimized",
	"AXModal",
	"AXNextContents",
	"AXNumberOfCharacters",
	"AXOrientation",
	"AXParent",
	"AXPath",
	"AXPlaceholderValue",
	"AXPopUpButton",
	"AXPosition",
	"AXPreventKeyboardDOMEventDispatch",
	"AXRadioButton",
	"AXRelativeFrame",
	"AXRequired",
	"AXRoleDescription",
	"AXScrollArea",
	"AXScrollBar",
	"AXSections",
	"AXSegment",
	"AXSelected",
	"AXSelectedChildren",
	"AXSelectedTextMarkerRange",
	"AXSelectedTextRange",
	"AXSize",
	"AXSplitGroup",
	"AXSplitter",
	"AXSplitters",
	"AXStandardWindow",
	"AXStartTextMarker",
	"AXStaticText",
	"AXSubrole",
	"AXTabButton",
	"AXTabGroup",
	"AXTabs",
	"AXTextArea",
	"AXTextField",
	"AXTextMarker",
	"AXTextMarkerRange",
	"AXTitle",
	"AXToggle",
	"AXToolbar",
	"AXTopLevelNavigator",
	"AXTopLevelUIElement",
	"AXUIElement",
	"AXUIElementCopyAttributeNames",
	"AXUIElementCreateApplication",
	"AXURL",
	"AXUnknown",
	"AXValue",
	"AXValueAutofillAvailable",
	"AXVerticalOrientation",
	"AXVerticalScrollBar",
	"AXVisibleCharacterRange",
	"AXVisibleChildren",
	"AXVisited",
	"AXWebArea",
	"AXWindow",
	"AXZoomButton",
]

class MacUITreeBuilder:
	def __init__(self):
		self.highlight_index = 0
		self._element_cache = {}
		self._observers = {}
		self._processed_elements = set()  # To avoid infinite recursion

		self._current_app_pid = None

		# Add limits to avoid processing too many nodes
		self.max_depth = 10         # maximum recursion depth
		self.max_children = 50      # maximum children per node to process

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
		self, element: 'AXUIElement', pid: int, parent: Optional[MacElementNode] = None, depth: int = 0
	) -> Optional[MacElementNode]:
		"""Process a single UI element"""
		element_identifier = str(element)
		
		# Add debug logging
		logger.debug(f'Processing element: {element_identifier}')
		
		# Avoid processing the same element again
		if element_identifier in self._processed_elements:
			logger.debug(f'Skipping already processed element: {element_identifier}')
			return None 

		self._processed_elements.add(element_identifier)

		try:
			# Add debug logging for attribute fetching
			logger.debug('Fetching basic attributes...')
			role = self._get_attribute(element, kAXRoleAttribute)
			logger.debug(f'Role: {role}')
			
			if not role:
				logger.debug('No role found, skipping element')
				return None

			# Create node with basic attributes first
			node = MacElementNode(
				role=role,
				identifier=element_identifier,
				attributes={},
				is_visible=True,  # Default to visible
				parent=parent,
				app_pid=pid,
			)
			node._element = element

			# Fetch other attributes with logging
			logger.debug('Fetching additional attributes...')
			title = self._get_attribute(element, kAXTitleAttribute)
			value = self._get_attribute(element, kAXValueAttribute)
			description = self._get_attribute(element, kAXDescriptionAttribute)
			is_enabled = self._get_attribute(element, 'AXEnabled')

			if title:
				node.attributes['title'] = title
			if value:
				node.attributes['value'] = value
			if description:
				node.attributes['description'] = description
			if is_enabled is not None:
				node.is_visible = bool(is_enabled)

			# Determine interactivity with more specific logging
			actions = self._get_actions(element)
			logger.debug(f'Available actions: {actions}')

			# Update interactive roles list and add logging
			interactive_roles = [
				'AXButton', 'AXTextField', 'AXCheckBox', 'AXRadioButton', 
				'AXComboBox', 'AXMenuButton', 'AXTextArea', 'AXPopUpButton'
				]
  
			# If the role is AXCell and it's a child of an AXRow,
			# skip marking it as interactive to avoid processing too many table cells.
			if role == "AXCell" and parent is not None and parent.role == "AXRow":
				node.is_interactive = False
			else:
				node.is_interactive = role in interactive_roles or bool(actions)
  
			logger.debug(f'Is interactive: {node.is_interactive} (role: {role})')

			if node.is_interactive:
				node.highlight_index = self.highlight_index
				self._element_cache[self.highlight_index] = node
				self.highlight_index += 1
				logger.debug(f'Added interactive element with highlight index: {node.highlight_index}')

			# Process children with additional checks
			children_ref = self._get_attribute(element, kAXChildrenAttribute)
			if children_ref:
				# Convert children_ref to a list so that it works with either a Python list or NSArray/tuple
				try:
					children_list = list(children_ref)
				except Exception as e:
					logger.warning(f"Unable to iterate children_ref: {e}")
					children_list = []
				
				child_count = len(children_list)
				if child_count > self.max_children:
					logger.debug(f'Limiting processing of children from {child_count} to {self.max_children}')
					children_list = children_list[:self.max_children]
				
				logger.debug(f'Processing {len(children_list)} children at depth {depth}')
				for i, child in enumerate(children_list):
					logger.debug(f'Processing child {i+1}/{len(children_list)} at depth {depth+1}')
					if depth >= self.max_depth:
						logger.debug(f'Maximum recursion depth ({self.max_depth}) reached, skipping further children')
						break
					child_node = await self._process_element(child, pid, node, depth=depth+1)
					if child_node:
						node.children.append(child_node)

			return node

		except Exception as e:
			logger.error(f'Error processing element: {str(e)}')
			return None

	async def build_tree(self, pid: Optional[int] = None) -> Optional[MacElementNode]:
		"""Build UI tree for a specific application"""
		try:
			if pid is None and self._current_app_pid is None:
				logger.debug('No app is currently open - waiting for app to be launched')
				raise ValueError('No app is currently open')

			if pid is not None:
				self._current_app_pid = pid

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

	def cleanup(self):
		"""Cleanup observers"""
		pass  # Temporarily do nothing
