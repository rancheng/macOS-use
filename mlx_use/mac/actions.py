# --- START OF FILE mac_use/mac/actions.py ---
import logging

import Cocoa
from ApplicationServices import AXUIElementPerformAction, AXUIElementSetAttributeValue, kAXPressAction, kAXValueAttribute, kAXConfirmAction
from Foundation import NSString

from mlx_use.mac.element import MacElementNode

logger = logging.getLogger(__name__)


def click(element: MacElementNode) -> bool:
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


def type_into(element: MacElementNode, text: str, submit: bool = False) -> bool:
    """Simulates typing text into a Mac UI element with action-based submission"""
    try:
        if not element._element:
            logger.error(f'❌ Cannot type: Element reference is missing for {element}')
            return False

        # Type the text using attribute setting
        ns_string = NSString.stringWithString_(text)
        type_result = AXUIElementSetAttributeValue(element._element, kAXValueAttribute, ns_string)
        
        if type_result != 0:
            logger.error(f"❌ Failed to type '{text}' into element: {element}, error code: {type_result}")
            return False
            
        logger.info(f"✅ Successfully typed '{text}' into element: {element}")
        
        # Handle submission using accessibility action instead of keyboard events
        if submit:
            # Try standard confirm action first
            confirm_result = AXUIElementPerformAction(element._element, kAXConfirmAction)
            
            if confirm_result == 0:
                logger.info("✅ Successfully submitted using confirm action")
                return True
            else:
                # Fallback to press action if confirm fails
                press_result = AXUIElementPerformAction(element._element, kAXPressAction)
                if press_result == 0:
                    logger.info("✅ Successfully submitted using press action")
                    return True
                else:
                    logger.error(f"❌ Failed to submit form, confirm error: {confirm_result}, press error: {press_result}")
                    return False
        
        return True

    except Exception as e:
        logger.error(f'❌ Error typing into element: {element}, {e}')
        return False