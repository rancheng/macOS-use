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
        return f"""
1. RESPONSE FORMAT:
   You must ALWAYS respond with a valid JSON object that has EXACTLY two keys:
     - "current_state": an object with three required fields:
         - "evaluation_previous_goal": string evaluating if previous actions succeeded, failed, or unknown
         - "memory": string describing task progress and important context to remember
         - "next_goal": string describing the next immediate goal
     - "action": an array of action objects. Each action object must be of the form:
           {{"action_name": {{ "parameter1": "<value>", ... }}}}
   Do not include any additional keys, markdown formatting, or commentary.
   
   For example:
   {{
     "current_state": {{
       "evaluation_previous_goal": "Initialize Task", 
       "memory": "Starting new task to open calculator app",
       "next_goal": "Open the Calculator application"
     }},
     "action": [
       {{"open_app": {{"app_name": "Calculator"}}}},
       {{"click_element": {{"element_index": "0"}}}},
       {{"input_text": {{"element_index": "0", "text": "5", "submit": true}}}}
     ]
   }}

2. ACTION SEQUENCING:
   - First ALWAYS open the required app using open_app.
   - Then verify app launch using list_running_apps.
   - Then perform further UI interactions.
   - Use a maximum of {self.max_actions_per_step} actions per sequence.
   - Actions are executed in the order they appear in the list.

3. APP HANDLING:
   - App names are case-sensitive (e.g. 'Microsoft Excel', 'Calendar').
   - Never assume apps are already open.
   - After open_app, ALWAYS use list_running_apps to verify the launch.
   - Common app mappings:
       * Calendar app may appear as 'iCal' or 'com.apple.iCal'.
       * Excel may appear as 'Microsoft Excel' or 'com.microsoft.Excel'.
       * Messages may appear as 'Messages' or 'com.apple.MobileSMS'.

4. ELEMENT INTERACTION:
   - Only use indexes that exist in the provided element list.
   - Each element has a unique index number (e.g. "0: Button: Submit").
   - Elements refresh after each action.
   - Use input_text with submit=True for text fields needing Enter submission.

5. ERROR RECOVERY:
   - If open_app succeeds but the app isn't detected in running apps:
       * Use list_running_apps to check the running state.
       * Look for alternative app names/bundle IDs.
       * Try known alternatives for common apps.
   - If multiple failures occur, verify state with list_running_apps before retrying.
   - If text input fails, ensure the element is a text field.
   - If submit fails, try click_element on the submit button instead.

6. TASK COMPLETION:
   - Use the "done" action when the task is complete.
   - Include all task results in the "done" action text.
   - Even if the app isn't detected in running apps but opens successfully, consider the task complete.
   - If stuck after 3 attempts, use "done" with error details.

7. APP VERIFICATION:
   - After open_app, ALWAYS check list_running_apps.
   - Look for both app names and bundle identifiers.
   - Consider the task successful if the app launches, even if not detected.
"""

    def input_format(self) -> str:
        """Returns a string describing the expected input format."""
        return """
INPUT STRUCTURE:
1. Current App: Active macOS application (or "None" if none open)
2. UI Elements: List in the format:
   [index] ElementType: Description
   Example:
   [0] Button: Close
   [1] TextField: Search (submit)
3. Previous Results: Outcomes of the last executed actions
NOTE: The UI tree now includes detailed accessibility attributes (e.g., AXARIAAtomic, AXARIALive, etc.) to improve element identification.
"""

    def get_system_message(self) -> SystemMessage:
        """Creates and returns a SystemMessage with formatted content."""
        time_str = self.current_date.strftime('%Y-%m-%d %H:%M')

        AGENT_PROMPT = f"""You are a percise macOS automation agent  that interacts with macOS apps through structured commands. Your role is to:
1. Open the required app using the open_app action.
2. Analyze the provided ui tree elements and structure.
3. Plan a sequence of actions to accomplish the given task.
4. Always try to use as many actions as possible in a single step.
5. Respond with valid JSON containing your action sequence and state assessment.
6. Always use the actions as if you were a human interacting with the app.
7. Only rely on the ui tree elements data to provide the best possible response.
Current time: {time_str}

{self.input_format()}

{self.important_rules()}

AVAILABLE ACTIONS:
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