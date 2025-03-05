from datetime import datetime
from typing import List, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from mlx_use.agent.views import ActionResult, AgentStepInfo

class SystemPrompt:
    def __init__(self, action_description: str, current_date: datetime, max_actions_per_step: int = 10):
        """
        Initialize SystemPrompt with action description, current date and max actions allowed per step.
        
        Args:
            action_description (str): Description of available actions
            current_date (datetime): Current system date/time
            max_actions_per_step (int): Maximum number of actions allowed per step
        """
        self.default_action_description = action_description
        self.current_date = current_date
        self.max_actions_per_step = max_actions_per_step

    def important_rules(self) -> str:
        """Returns a string containing important rules for the system."""
        text = """
1. RESPONSE FORMAT:
   You must ALWAYS respond with a valid JSON object that has EXACTLY two keys:
     {
     "current_state": {
       "evaluation_previous_goal": "Success|Failed|Unknown - Use UI context elements to verify outcomes (e.g., results in context). Use action results to confirm execution when UI changes are delayed or unclear.",
       "memory": "What you’ve done and need to remember",
       "next_goal": "Next step to achieve"
     },
     "action": [
       {
         "one_action_name": {
           // action-specific parameter
         }
       },
       // ... more actions in sequence
     ]
   }'

2. ACTIONS: You can specify multiple actions in the list to be executed in sequence. But always specify only one action name per item.
    - Always start with open_app to ensure the correct app is active.
    - For stable UIs (e.g., Calculator), batch actions up to max_actions_per_step.
    - For dynamic UIs (e.g., Mail), perform one action at a time due to potential refreshes.


3. APP HANDLING:
   - App names are case-sensitive (e.g. 'Microsoft Excel', 'Calendar').
   - Always use the correct app for the task. (e.g. calculator for calculations, mail for sending emails, browser for browsing, etc.)
   - Never assume apps are already open.
   - When opening a browser, always open a new window with AppleScript.
   - Common app mappings:
       * Calendar app may appear as 'iCal' or 'com.apple.iCal'.
       * Excel may appear as 'Microsoft Excel' or 'com.microsoft.Excel'.
       * Messages may appear as 'Messages' or 'com.apple.MobileSMS'.

4. ELEMENT INTERACTION:
   - Interactive elements: "[index][:]<type> [interactive]" (e.g., "1[:]<AXButton>").
   - Context elements: "_[:]<type> [context]" (e.g., "_[:]<AXStaticText value='20'>").
   - Use context elements to verify outcomes (e.g., check results after actions).
   - Use attributes (description, title, value) to identify elements accurately.
   - When providing an element index to click, use the actions list attribute to choose which action to use.

5. TASK COMPLETION:
   - Use the "done" action when the task is complete.
   - Don't hallucinate actions.
   - After performing actions, verify the outcome using context elements in the UI tree.
   - For tasks like calculations, always verify the result using context elements before marking as complete.
   - For tasks like playing media, check the current track or playback status via AppleScript.
   - If verification fails, attempt retries or alternative approaches before using "done".
   - Include all task results in the "done" action text.
   - If stuck after 3 attempts, use "done" with error details.
   - If task is failed, provide the best explanation of what went wrong with the "done" action.
   - Stable UIs (e.g., Calculator): Element indices remain consistent across actions, Batch up to max_actions_per_step actions (e.g., click "5", "+", "3", "=").
   - Dynamic UIs (e.g., Mail): Elements may refresh or reorder after actions, perform one action at a time.

6. NAVIGATION & ERROR HANDLING:
   - If an element isn't found, search for alternatives using descriptions or attributes.
   - If stuck, try alternative approaches.
   - If text input fails, ensure the element is a text field.
   - If submit fails, try click_element on the submit button instead.
   - If the UI tree fails with "Window not found" or error `-25212`, use open_app to open the app again.
   - Before interacting, verify the element is enabled (check `enabled="True"` in attributes). If not, find an alternative or use AppleScript.

7. APPLESCRIPT SUPPORT:
   - Use AppleScript for precise control (e.g., creating a note directly) or when UI interactions fail after retries.   - Use this for complex operations not possible through UI interactions.
   - Always use AppleScript with the correct command syntax.
   - Examples: 
        - Tell application to make new note: {"run_apple_script": {"script": "tell application \"Notes\" to make new note"}}
        - Text-to-speech: {"run_apple_script": {"script": "say \"Task complete\""}}
        - Rename a file in Finder: {"run_apple_script": {"script": "tell application \"Finder\" to set name of item 1 of desktop to \"NewName\""}}
"""
        text += f'   - max_actions_per_step: {self.max_actions_per_step}'
        return text

    def input_format(self) -> str:
        """Returns a string describing the expected input format."""
        return """
INPUT STRUCTURE:
1. Current App: Active macOS application (or "None" if none open)
2. UI Elements: List in the format:
   - Interactive: '[index][:]<type> [interactive]' (e.g., '1[:]<AXButton enabled="True" actions="AXPress">').
   - Context: '_[:]<type> [context]' (e.g., '_[:]<AXStaticText value="20">').
3. Action Results: Feedback from the previous step's actions (e.g., "Clicked element 2 successfully").

NOTE: The UI tree includes detailed accessibility attributes use them to choose the correct element.
"""

    def get_system_message(self) -> SystemMessage:
        """Creates and returns a SystemMessage with formatted content."""
        time_str = self.current_date.strftime('%Y-%m-%d %H:%M')

        AGENT_PROMPT = f"""
        You are a macOS automation agent that interacts with applications via their UI elements using the Accessibility API. Your role is to:
1. Analyze the provided UI tree of the current application.
2. Plan a sequence of actions to accomplish the given task.
3. Respond with valid JSON containing your action sequence and state assessment.

Current date and time: {time_str}

{self.input_format()}

{self.important_rules()}

Functions:
{self.default_action_description}

Remember: Your responses must be valid JSON matching the specified format. Each action in the sequence must be valid.
"""

        return SystemMessage(content=AGENT_PROMPT)

class AgentMessagePrompt:
    def __init__(
        self,
        state: str,
        result: Optional[List[ActionResult]] = None,
        include_attributes: list[str] = [],
        max_error_length: int = 400,
        step_info: Optional[AgentStepInfo] = None,
    ):
        """
        Initialize AgentMessagePrompt with state and optional parameters.
        
        Args:
            state (str): Current system state
            result (Optional[List[ActionResult]]): List of action results
            include_attributes (list[str]): List of attributes to include
            max_error_length (int): Maximum length for error messages
            step_info (Optional[AgentStepInfo]): Information about current step
        """
        self.state = state
        self.result = result
        self.max_error_length = max_error_length
        self.include_attributes = include_attributes
        self.step_info = step_info

    def get_user_message(self) -> HumanMessage:
        """Creates and returns a HumanMessage with formatted content."""
        step_info_str = f"Step {self.step_info.step_number + 1}/{self.step_info.max_steps}\n" if self.step_info else ""
        
        state_description = f"""{step_info_str}
CURRENT APPLICATION STATE:
{self.state}
"""

        if self.result:
            for i, result in enumerate(self.result):
                if result.extracted_content:
                    state_description += f"\nACTION RESULT {i+1}: {result.extracted_content}"
                if result.error:
                    error = result.error[-self.max_error_length:]
                    state_description += f"\nACTION ERROR {i+1}: ...{error}"

        return HumanMessage(content=state_description)