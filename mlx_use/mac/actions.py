# --- START OF FILE mac_use/mac/actions.py ---
import logging

import Cocoa
from ApplicationServices import AXUIElementPerformAction, AXUIElementSetAttributeValue, kAXPressAction, kAXValueAttribute
from Foundation import NSString

from mlx_use.mac.element import MacElementNode

logger = logging.getLogger(__name__)


def click_element(element: MacElementNode) -> bool:
	"""Simulates a click on a Mac UI element."""
	try:
		if element._element:
			result = AXUIElementPerformAction(element._element, kAXPressAction)
			if result == 0:  # 0 indicates success
				logger.info(f'✅ Successfully clicked on element: {element}')
				return True
			else:
				logger.error(f'❌ Failed to click on element: {element}, error code: {result}')
				return False
		else:
			logger.error(f'❌ Cannot click: Element reference is missing for {element}')
			return False
	except Exception as e:
		logger.error(f'❌ Error clicking element: {element}, {e}')
		return False


def type_into_element(element: MacElementNode, text: str) -> bool:
	"""Simulates typing text into a Mac UI element."""
	try:
		if element._element:
			# Use NSString to bridge the Python string
			ns_string = NSString.stringWithString_(text)
			result = AXUIElementSetAttributeValue(element._element, kAXValueAttribute, ns_string)
			if result == 0:
				logger.info(f"✅ Successfully typed '{text}' into element: {element}")
				return True
			else:
				logger.error(f"❌ Failed to type '{text}' into element: {element}, error code: {result}")
				return False
		else:
			logger.error(f'❌ Cannot type: Element reference is missing for {element}')
			return False
	except Exception as e:
		logger.error(f'❌ Error typing into element: {element}, {e}')
		return False
