# --- START OF FILE examples/basic_agent.py ---
import asyncio
import json
import time
import logging
import Cocoa
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import SecretStr

from mlx_use.mac.actions import click, type_into
from mlx_use.mac.tree import MacUITreeBuilder

NOTES_BUNDLE_ID = 'com.apple.Notes'
NOTES_APP_NAME = 'Notes'

# Replace with your actual Gemini API key
llm = ChatGoogleGenerativeAI(model='gemini-2.0-flash-exp', api_key=SecretStr(GEMINI_API_KEY))


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


class FolderCreationState:
	def __init__(self):
		self.new_folder_clicked = False
		self.folder_name_entered = False
		self.last_action = None

	def get_context(self, ui_tree_string: str) -> str:
		if not self.new_folder_clicked:
			return "Find and click the 'New Folder' button."
		elif not self.folder_name_entered:
			return "The 'New Folder' button has been clicked. Look for the newly appeared text field to type the folder name."
		else:
			return 'Folder name has been entered.'

	def update(self, action_name: str, success: bool = True, element_info: str = '') -> None:
		if not success:
			return

		if action_name == 'click' and 'New Folder' in element_info:
			self.new_folder_clicked = True
			self.last_action = 'clicked_new_folder'
		elif action_name == 'type' and self.new_folder_clicked:
			self.folder_name_entered = True
			self.last_action = 'entered_folder_name'


async def main():
	try:
		workspace = Cocoa.NSWorkspace.sharedWorkspace()
		state = FolderCreationState()

		print(f'\nLaunching {NOTES_APP_NAME} app...')
		success = workspace.launchApplication_(NOTES_APP_NAME)

		if not success:
			print(f'❌ Failed to launch {NOTES_APP_NAME} app')
			return

		# Find Notes app
		await asyncio.sleep(2)
		notes_app = None
		for app in workspace.runningApplications():
			if app.bundleIdentifier() and NOTES_BUNDLE_ID.lower() in app.bundleIdentifier().lower():
				notes_app = app
				print(f'\nFound {NOTES_APP_NAME} app!')
				print(f'Bundle ID: {app.bundleIdentifier()}')
				print(f'PID: {app.processIdentifier()}')
				break

		if not notes_app:
			print(f'❌ Could not find {NOTES_APP_NAME} app')
			return

		is_ready = await wait_for_app_ready(notes_app)
		if not is_ready:
			print(f'❌ App failed to become ready')
			return

		builder = MacUITreeBuilder()
		max_steps = 10  # Limit the number of interaction steps
		goal_achieved = False
		for step in range(max_steps):
			if goal_achieved:
				print('✅ Goal already achieved, stopping further actions')
				break

			print(f'\n--- Step {step + 1}/{max_steps} ---')
			root = await builder.build_tree(notes_app.processIdentifier(), notification_callback=notification_handler)

			if not root:
				print(f'❌ Failed to build UI tree for {NOTES_APP_NAME}')
				break

			ui_tree_string = root.get_clickable_elements_string()

			# Add state context to the prompt
			state_context = state.get_context(ui_tree_string)

			prompt = f"""You are an intelligent agent designed to automate tasks within the macOS "Notes" application.

Current Goal: Create a new folder in the notes app called 'Ofir folder'.
Current Step: {state_context}

To create a new folder, you need to:
1. Click the "New Folder" button.
2. After clicking "New Folder", a **new text field will appear**. This is where you should type the folder name. **Do not type into the search bar.**
3. Type "Ofir folder" into the new text field.
4. Click the "OK" button to create the folder.

You can interact with the application by performing the following actions:

- **click**: Simulate a click on an interactive element. To perform this action, you need to specify the `index` of the element to click.
- **type**: Simulate typing text into a text field. To perform this action, you need to specify the `index` of the text field and the `text` to type.

Here is the current state of the "Notes" application's user interface, represented as a tree structure. Each interactive element is marked with a `highlight` index that you can use to target it for an action:
Use code with caution.
Python
{ui_tree_string}

Based on the current UI and your goal, choose the next action you want to perform. Respond with a JSON object in the following format:

RESPONSE FORMAT: You must ALWAYS respond with valid JSON in this exact format:
{{
  "action": "click" or "type",
  "parameters": {{
    "index": <element_index>
    }} // OR
    "index": <element_index>,
    "text": "<text_to_type>"
  }}
}}
Use code with caution.
For example, to click the element with highlight: 1, you would respond with:

{{
  "action": "click",
  "parameters": {{
    "index": 1
  }}
}}
Use code with caution.
Json
To type "Hello" into the text field with highlight: 5, you would respond with:

{{
  "action": "type",
  "parameters": {{
    "index": 5,
    "text": "Hello"
  }}
}}
Use code with caution.
Json
After each action, you will receive feedback on whether the action was successful. Use this feedback to adjust your strategy and achieve the goal.

Remember your goal: "Create a new folder in the notes app called 'Ofir folder'". Analyze the current UI and available actions carefully to determine the most effective next step."""

			llm_response = llm.invoke(prompt)
			print(f'LLM Response.content is: {llm_response.content}\n\n')
			print(f'LLM Response is: {llm_response}')

			try:
				# Clean up the response by removing markdown code blocks
				response_content = llm_response.content
				if response_content.startswith('```') and response_content.endswith('```'):
					lines = response_content.split('\n')
					response_content = '\n'.join(lines[1:-1])  # Remove first and last lines

				action_json = json.loads(response_content)
				action_name = action_json.get('action')
				parameters = action_json.get('parameters', {})

				success = False
				if action_name == 'click':
					index_to_click = parameters.get('index')
					if isinstance(index_to_click, int) and index_to_click in builder._element_cache:
						element_to_click = builder._element_cache[index_to_click]
						success = click(element_to_click)
						state.update(action_name, success, str(element_to_click))
					else:
						logging.error('❌ Invalid index for click action.')
				elif action_name == 'type':
					index_to_type = parameters.get('index')
					text_to_type = parameters.get('text')
					if isinstance(index_to_type, int) and text_to_type is not None and index_to_type in builder._element_cache:
						element_to_type_into = builder._element_cache[index_to_type]
						print(f"Attempting to type '{text_to_type}' into: {element_to_type_into}")
						success = type_into(element_to_type_into, text_to_type)
						print(f'Typing successful: {success}')
						state.update(action_name, success)
					else:
						print('❌ Invalid index or text for type action.')
				else:
					print(f'❌ Unknown action: {action_name}')

				state.update(action_name, success)

			except json.JSONDecodeError:
				print('❌ Could not decode LLM response as JSON.')
			except Exception as e:
				print(f'❌ An error occurred: {e}')

			# Check if goal has been achieved
			if 'Ofir folder' in ui_tree_string:
				print("✅ Goal achieved! 'Ofir folder' found in the UI tree.")
				goal_achieved = True
				continue

			await asyncio.sleep(1)  # Give time for the UI to update

	except Exception as e:
		print(f'❌ Error: {e}')
		import traceback

		traceback.print_exc()
	finally:
		if 'builder' in locals():
			builder.cleanup()


if __name__ == '__main__':
	asyncio.run(main())
