# print_app_tree.py
# --- START OF FILE examples/basic_agent.py ---
import asyncio
import time
from typing import Optional

import Cocoa

from mlx_use.mac.actions import click  # Import the click_element function
from mlx_use.mac.tree import MacUITreeBuilder


def notification_handler(notification, element):
	"""Handle accessibility notifications"""
	print(f'Received notification: {notification}')


async def wait_for_app_ready(app, max_attempts=10, delay=2.5) -> bool:
	"""Wait for app to be ready with detailed status checking"""
	for i in range(max_attempts):
		try:
			if not app:
				print(f'Attempt {i + 1}/{max_attempts}: App object is None')
				await asyncio.sleep(delay)
				continue

			if app:
				app.activateWithOptions_(Cocoa.NSApplicationActivateIgnoringOtherApps)
				await asyncio.sleep(1)
				print(f'✅ App is running and ready')
				return True

			await asyncio.sleep(delay)

		except Exception as e:
			print(f'Error checking app status: {e}')
			await asyncio.sleep(delay)

	return False


async def main():
	try:
		workspace = Cocoa.NSWorkspace.sharedWorkspace()

		print(f'\nLaunching {CALCULATOR_APP_NAME} app...')
		success = workspace.launchApplication_(CALCULATOR_APP_NAME)

		if not success:
			print(f'❌ Failed to launch {CALCULATOR_APP_NAME} app\n ending with {success}')
			return

		# Find Calculator app
		await asyncio.sleep(2)  # Give it a moment to appear in running apps
		calculator_app = None
		for app in workspace.runningApplications():
			if app.bundleIdentifier() and CALCULATOR_BUNDLE_ID in app.bundleIdentifier().lower():
				calculator_app = app
				print(f'\nFound {CALCULATOR_APP_NAME} app!')
				print(f'Bundle ID: {app.bundleIdentifier()}')
				print(f'PID: {app.processIdentifier()}')
				break

		if not calculator_app:
			print(f'❌ Could not find {CALCULATOR_APP_NAME} app in:\n {workspace.runningApplications()}')
			return

		# Wait for app to be ready
		is_ready = await wait_for_app_ready(calculator_app)
		if not is_ready:
			print(f'❌ App failed to become ready')
			return

		builder = MacUITreeBuilder()  # Initialize builder outside the loop

		while True:
			# Build UI tree
			root = await builder.build_tree(calculator_app.processIdentifier(), notification_callback=notification_handler)

			if root:
				print(f'\n✅ Successfully built UI tree for {CALCULATOR_APP_NAME}!')
				print(f'Number of root children: {len(root.children)}')

				def print_tree(node, indent=0):
					print('  ' * indent + repr(node))
					for child in node.children:
						print_tree(child, indent + 1)

				print(f'\nAll elements in the tree for {CALCULATOR_APP_NAME}:')
				print_tree(root)

				print(f'\nInteractive elements found in {CALCULATOR_APP_NAME}:')
				print(root.get_clickable_elements_string())

				try:
					index_to_click = input(
						f"\nEnter the index of the element to click in {CALCULATOR_APP_NAME} (or 'q' to quit): "
					)
					if index_to_click.lower() == 'q':
						break
					index = int(index_to_click)
					if index in builder._element_cache:
						element_to_click = builder._element_cache[index]
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
			else:
				print(f'❌ Failed to build UI tree for {CALCULATOR_APP_NAME}')
				break  # Exit the loop if tree building fails

	except Exception as e:
		print(f'❌ Error: {e}')
		import traceback

		traceback.print_exc()
	finally:
		# Cleanup
		if 'builder' in locals():
			builder.cleanup()


if __name__ == '__main__':
	app = input('What app should I lunch?')
	CALCULATOR_BUNDLE_ID = f'com.apple.{app}'
	CALCULATOR_APP_NAME = f'{app.capitalize()}'
	asyncio.run(main())
