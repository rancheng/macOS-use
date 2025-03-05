import os
import json
import queue
import logging
import asyncio
import traceback
from pathlib import Path
from typing import Optional, Generator, AsyncGenerator, List
from dotenv import load_dotenv, set_key
import gradio as gr

from ..utils.logging_utils import setup_logging
from ..models.llm_models import LLM_MODELS, get_llm
from ..services.google_form import send_prompt_to_google_sheet
from ..config.example_prompts import EXAMPLE_CATEGORIES

# Import mlx_use from parent directory
import sys
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from mlx_use import Agent
from mlx_use.controller.service import Controller

class MacOSUseGradioApp:
    def __init__(self):
        self.agent = None
        self.controller = Controller()
        self.is_running = False
        self.log_queue = queue.Queue()
        self.setup_logging()
        self.terminal_buffer = []
        self.automations = {}  # Dictionary to store automation flows
        self.preferences_file = Path(__file__).parent.parent.parent / 'preferences.json'
        self.preferences = self.load_preferences()
        self._cleanup_state()
        self.example_categories = EXAMPLE_CATEGORIES
        self.llm_models = LLM_MODELS
        self.current_task = None  # Store the current running task
        
        # Load environment variables
        load_dotenv()

    def _cleanup_state(self):
        """Reset all state variables"""
        self.is_running = False
        self.agent = None
        self.current_task = None  # Clear current task reference
        # Don't clear terminal_buffer when stopping the agent
        # But do clear the log queue
        while not self.log_queue.empty():
            try:
                self.log_queue.get_nowait()
            except queue.Empty:
                break

    def setup_logging(self):
        """Set up logging to capture terminal output"""
        setup_logging(self.log_queue)

    def get_terminal_output(self) -> str:
        """Get accumulated terminal output"""
        while True:
            try:
                log = self.log_queue.get_nowait()
                self.terminal_buffer.append(log)
            except queue.Empty:
                break
        return "".join(self.terminal_buffer)

    def stream_terminal_output(self) -> Generator[str, None, None]:
        """Stream terminal output in real-time"""
        while self.is_running:
            output = self.get_terminal_output()
            if output:
                yield output
            yield

    def stop_agent(self) -> tuple:
        """Stop the running agent"""
        if self.agent and self.is_running:
            self.is_running = False
            
            # Set the agent's internal stop flag if it exists
            if hasattr(self.agent, '_stopped'):
                self.agent._stopped = True
                
            # Explicitly cancel the task if it exists
            if self.current_task and not self.current_task.done():
                self.current_task.cancel()
                
            # Get the current terminal output before cleanup
            terminal_output = self.get_terminal_output()
            
            # Clean up state but don't affect terminal_buffer
            self._cleanup_state()
            
            # Append message to the existing output instead of replacing it
            return (
                terminal_output + "\nAgent stopped by user",
                gr.update(interactive=True),
                gr.update(interactive=False),
                gr.update(value="")  # Clear result output when stopping
            )
        return (
            "No agent running",
            gr.update(interactive=True),
            gr.update(interactive=False),
            gr.update(value="")  # Clear result output when no agent is running
        )

    def add_automation(self, name: str, description: str) -> dict:
        """Add a new automation flow"""
        if name in self.automations:
            raise ValueError(f"Automation '{name}' already exists")
        
        self.automations[name] = {
            "description": description,
            "agents": []
        }
        return gr.update(choices=list(self.automations.keys()))

    def add_agent_to_automation(self, automation_name: str, agent_prompt: str, position: int = -1) -> list:
        """Add a new agent to an automation flow"""
        if automation_name not in self.automations:
            raise ValueError(f"Automation '{automation_name}' does not exist")
        
        new_agent = {
            "prompt": agent_prompt,
            "max_steps": 25,  # Default values
            "max_actions": 1
        }
        
        if position == -1 or position >= len(self.automations[automation_name]["agents"]):
            self.automations[automation_name]["agents"].append(new_agent)
        else:
            self.automations[automation_name]["agents"].insert(position, new_agent)
            
        return self.automations[automation_name]["agents"]

    def remove_agent_from_automation(self, automation_name: str, agent_index: int) -> list:
        """Remove an agent from an automation flow"""
        if automation_name not in self.automations:
            raise ValueError(f"Automation '{automation_name}' does not exist")
        
        if not isinstance(agent_index, int):
            raise ValueError("Agent index must be an integer")
            
        if agent_index < 0 or agent_index >= len(self.automations[automation_name]["agents"]):
            raise ValueError(f"Invalid agent index {agent_index}")
        
        self.automations[automation_name]["agents"].pop(agent_index)
        return self.automations[automation_name]["agents"]

    def get_automation_agents(self, automation_name: str) -> list:
        """Get the list of agents for an automation flow"""
        if automation_name not in self.automations:
            raise ValueError(f"Automation '{automation_name}' does not exist")
        
        return self.automations[automation_name]["agents"]

    def save_api_key_to_env(self, provider: str, api_key: str) -> None:
        """Save API key to .env file based on provider"""
        env_path = Path(__file__).parent.parent.parent.parent / '.env'
        
        # Create .env file if it doesn't exist
        if not env_path.exists():
            env_path.touch()
        
        # Map provider to environment variable name
        provider_to_env = {
            "OpenAI": "OPENAI_API_KEY",
            "Anthropic": "ANTHROPIC_API_KEY",
            "Google": "GEMINI_API_KEY",
            "alibaba": "DEEPSEEK_API_KEY"
        }
        
        env_var = provider_to_env.get(provider)
        if env_var and api_key:
            set_key(str(env_path), env_var, api_key)

    def extract_result_text(self, output: str) -> str:
        """Extract the result text from the output by checking various formats."""
        lines = output.split('\n')
        result_text = ""
        
        # Check if task reached max steps
        if "❌ Failed to complete task in maximum steps" in output:
            return "Task reached maximum steps without completion.  "
        
        # Check for other result formats
        for line in lines:
            line = line.strip()
            if "📄 Result:" in line:
                result_text = line.split("📄 Result:", 1)[1].strip()
            elif "📝 Result:" in line:
                result_text = line.split("📝 Result:", 1)[1].strip()
            elif "Result:" in line:
                result_text = line.split("Result:", 1)[1].strip()
            elif line.startswith("✅"):
                idx = lines.index(line)
                if idx > 0:
                    prev_line = lines[idx-1].strip()
                    if "📄 Result:" in prev_line:
                        result_text = prev_line.split("📄 Result:", 1)[1].strip()
                    elif "📝 Result:" in prev_line:
                        result_text = prev_line.split("📝 Result:", 1)[1].strip()
        
        # If no explicit result found but task completed steps
        if not result_text and "📍 Step" in output:
            last_eval = None
            for line in reversed(lines):
                if "Eval:" in line:
                    last_eval = line.split("Eval:", 1)[1].strip()
                    break
            if last_eval:
                result_text = f"Last status: {last_eval}"
        
        return result_text

    def get_saved_api_key(self, provider: str) -> str:
        """Get saved API key from .env file based on provider"""
        provider_to_env = {
            "OpenAI": "OPENAI_API_KEY",
            "Anthropic": "ANTHROPIC_API_KEY",
            "Google": "GEMINI_API_KEY",
            "alibaba": "DEEPSEEK_API_KEY"
        }
        env_var = provider_to_env.get(provider)
        return os.getenv(env_var, "") if env_var else ""

    def load_preferences(self) -> dict:
        """Load user preferences from JSON file"""
        if self.preferences_file.exists():
            try:
                with open(self.preferences_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Failed to load preferences: {e}")
        return {"share_prompt": False, "share_terminal": True}  # Default preferences

    def save_preferences(self) -> None:
        """Save user preferences to JSON file"""
        try:
            with open(self.preferences_file, 'w') as f:
                json.dump(self.preferences, f)
        except Exception as e:
            logging.error(f"Failed to save preferences: {e}")

    def update_share_prompt(self, value: bool) -> None:
        """Update share_prompt preference"""
        self.preferences["share_prompt"] = value
        self.save_preferences()

    def update_share_terminal(self, value: bool) -> None:
        """Update share_terminal preference"""
        self.preferences["share_terminal"] = value
        self.save_preferences()

    def update_llm_preferences(self, provider: str, model: str) -> None:
        """Update LLM provider and model preferences"""
        self.preferences["llm_provider"] = provider
        self.preferences["llm_model"] = model
        self.save_preferences()

    async def run_automation(
        self,
        automation_name: str,
        llm_provider: str,
        llm_model: str,
        api_key: str,
    ) -> AsyncGenerator[tuple[str, dict, dict], None]:
        """Run an automation flow by executing its agents in sequence"""
        if automation_name not in self.automations:
            raise ValueError(f"Automation '{automation_name}' does not exist")

        # Save API key to .env file
        self.save_api_key_to_env(llm_provider, api_key)

        automation = self.automations[automation_name]
        self._cleanup_state()
        
        # Clear terminal buffer for new automation
        self.terminal_buffer = []
        
        try:
            for i, agent_config in enumerate(automation["agents"]):
                # Initialize LLM
                llm = get_llm(llm_provider, llm_model, api_key)
                if not llm:
                    raise ValueError(f"Failed to initialize {llm_provider} LLM")
                
                # Initialize agent
                self.agent = Agent(
                    task=agent_config["prompt"],
                    llm=llm,
                    controller=self.controller,
                    use_vision=False,
                    max_actions_per_step=agent_config["max_actions"]
                )
                
                self.is_running = True
                last_update = ""
                
                try:
                    # Start the agent run
                    agent_task = asyncio.create_task(self.agent.run(max_steps=agent_config["max_steps"]))
                    self.current_task = agent_task  # Store reference to current task
                    
                    # While the agent is running, yield updates periodically
                    while not agent_task.done() and self.is_running:
                        current_output = self.get_terminal_output()
                        if current_output != last_update:
                            # Check if we've had a "done" action
                            if "\"done\":" in current_output and "📄 Result:" in current_output:
                                logging.info("Detected 'done' action, stopping agent")
                                self.is_running = False
                                if not agent_task.done():
                                    agent_task.cancel()
                                break
                                
                            yield (
                                f"Running agent {i+1}/{len(automation['agents'])}\n{current_output}",
                                gr.update(interactive=False),
                                gr.update(interactive=True)
                            )
                            last_update = current_output
                        await asyncio.sleep(0.1)
                    
                    if not agent_task.done():
                        agent_task.cancel()
                        await asyncio.sleep(0.1)  # Allow time for cancellation
                    else:
                        result = await agent_task
                    
                    # Final update for this agent
                    final_output = self.get_terminal_output()
                    if final_output != last_update:
                        yield (
                            f"Completed agent {i+1}/{len(automation['agents'])}\n{final_output}",
                            gr.update(interactive=True) if i == len(automation["agents"]) - 1 else gr.update(interactive=False),
                            gr.update(interactive=False) if i == len(automation["agents"]) - 1 else gr.update(interactive=True)
                        )
                    
                except Exception as e:
                    error_details = f"Error Details:\n{traceback.format_exc()}"
                    self.terminal_buffer.append(f"\nError occurred in agent {i+1}:\n{str(e)}\n\n{error_details}")
                    yield (
                        "".join(self.terminal_buffer),
                        gr.update(interactive=True),
                        gr.update(interactive=False)
                    )
                    break
                
                self._cleanup_state()
                
        except Exception as e:
            error_details = f"Error Details:\n{traceback.format_exc()}"
            error_msg = f"Error occurred:\n{str(e)}\n\n{error_details}"
            yield (
                error_msg,
                gr.update(interactive=True),
                gr.update(interactive=False)
            )
            self._cleanup_state()

    async def get_llm_response(
        self,
        system_message: str,
        user_message: str,
        llm_provider: str,
        llm_model: str
    ) -> str:
        """Get a direct response from the LLM model without using the Agent"""
        try:
            # Get the API key
            api_key = self.get_saved_api_key(llm_provider)
            if not api_key:
                raise ValueError(f"No API key found for {llm_provider}")
            
            # Initialize LLM
            llm = get_llm(llm_provider, llm_model, api_key)
            if not llm:
                raise ValueError(f"Failed to initialize {llm_provider} LLM")
            
            # Create the messages
            from langchain_core.messages import SystemMessage, HumanMessage
            messages = [
                SystemMessage(content=system_message),
                HumanMessage(content=user_message)
            ]
            
            # Get the response
            response = await llm.ainvoke(messages)
            return response.content
            
        except Exception as e:
            logging.error(f"Error getting LLM response: {e}")
            return user_message  # Return the original message if there's an error
            
    async def run_agent(
        self,
        task: str,
        max_steps: int,
        max_actions: int,
        llm_provider: str,
        llm_model: str,
        api_key: str,
        share_prompt: bool,
        share_terminal: bool
    ) -> AsyncGenerator[tuple[str, dict, dict, dict], None]:
        """Run the agent with the specified configuration"""
        # Clean up any previous state
        self._cleanup_state()
        
        # Clear terminal buffer for new task, but only when starting a new task (not when stopping)
        self.terminal_buffer = []
        
        try:
            # Validate inputs
            if not task or not task.strip():
                yield (
                    "Please enter a task description",
                    gr.update(interactive=True),
                    gr.update(interactive=False),
                    gr.update(value="Task description is required")
                )
                return
                
            if not api_key:
                yield (
                    "API key is required",
                    gr.update(interactive=True),
                    gr.update(interactive=False),
                    gr.update(value="API key is required")
                )
                return
            
            # Save API key to .env file
            self.save_api_key_to_env(llm_provider, api_key)
            
            # Send the prompt to the Google Form/Sheet if requested
            if share_prompt and not share_terminal:
                try:
                    # If only sharing prompt but not terminal, send immediately
                    logging.info(f"Immediately sending prompt only to Google Form (share_prompt={share_prompt}, share_terminal={share_terminal})")
                    success = await asyncio.to_thread(send_prompt_to_google_sheet, task)
                    if not success:
                        logging.warning("Failed to send prompt to Google Form")
                except Exception as e:
                    logging.error(f"Error sending prompt to Google Form: {e}")
            elif share_prompt or share_terminal:
                # If either or both are enabled, we'll send after completion
                logging.info(f"Will send data after completion (share_prompt={share_prompt}, share_terminal={share_terminal})")
            
            # Initialize LLM
            llm = get_llm(llm_provider, llm_model, api_key)
            if not llm:
                yield (
                    f"Failed to initialize {llm_provider} LLM",
                    gr.update(interactive=True),
                    gr.update(interactive=False),
                    gr.update(value=f"Failed to initialize {llm_provider} LLM")
                )
                return
            
            # Initialize agent
            self.agent = Agent(
                task=task,
                llm=llm,
                controller=self.controller,
                use_vision=False,
                max_actions_per_step=max_actions
            )
            
            self.is_running = True
            last_update = ""
            
            try:
                # Start the agent run
                agent_task = asyncio.create_task(self.agent.run(max_steps=max_steps))
                self.current_task = agent_task  # Store reference to current task
                
                # Track "done" actions to detect when to stop
                # Stop immediately after a single done action
                
                # While the agent is running, yield updates periodically
                while not agent_task.done() and self.is_running:
                    current_output = self.get_terminal_output()
                    if current_output != last_update:
                        result_text = self.extract_result_text(current_output)
                        
                        # Check if we've had a "done" action
                        if "\"done\":" in current_output and "📄 Result:" in current_output:
                            logging.info("Detected 'done' action, stopping agent")
                            self.is_running = False
                            if not agent_task.done():
                                agent_task.cancel()
                            break
                            
                        yield (
                            current_output,
                            gr.update(interactive=False),
                            gr.update(interactive=True),
                            gr.update(value=result_text)
                        )
                        last_update = current_output
                    await asyncio.sleep(0.1)
                
                if not agent_task.done():
                    agent_task.cancel()
                    await asyncio.sleep(0.1)  # Allow time for cancellation
                else:
                    result = await agent_task
                    await asyncio.sleep(0.1)  # Allow time for logs to flush
                
                # Final update with latest output and result
                final_output = self.get_terminal_output()
                final_result_text = self.extract_result_text(final_output)
                
                # Send data to Google Form if either sharing preference is enabled
                if share_prompt or share_terminal:
                    try:
                        if share_terminal:
                            # Send both prompt and terminal output
                            logging.info(f"Sending prompt and terminal output to Google Form (length: {len(final_output)})")
                            success = await asyncio.to_thread(send_prompt_to_google_sheet, task, final_output)
                        else:
                            # Send only the prompt (when share_prompt=true but share_terminal=false)
                            # This is a backup in case the initial send failed
                            logging.info("Sending prompt only to Google Form (backup after completion)")
                            success = await asyncio.to_thread(send_prompt_to_google_sheet, task)
                            
                        if not success:
                            logging.warning("Failed to send data to Google Form")
                        else:
                            if share_terminal:
                                logging.info("Successfully sent prompt and terminal output to Google Form")
                            else:
                                logging.info("Successfully sent prompt to Google Form")
                    except Exception as e:
                        logging.error(f"Error sending data to Google Form: {e}")
                
                if final_output != last_update:
                    yield (
                        final_output,
                        gr.update(interactive=True),
                        gr.update(interactive=False),
                        gr.update(value=final_result_text)
                    )
                
            except Exception as e:
                error_details = f"Error Details:\n{traceback.format_exc()}"
                self.terminal_buffer.append(f"\nError occurred:\n{str(e)}\n\n{error_details}")
                yield (
                    "".join(self.terminal_buffer),
                    gr.update(interactive=True),
                    gr.update(interactive=False),
                    gr.update(value="An error occurred while running the agent")
                )
            finally:
                self._cleanup_state()
            
        except Exception as e:
            error_details = f"Error Details:\n{traceback.format_exc()}"
            error_msg = f"Error occurred:\n{str(e)}\n\n{error_details}"
            yield (
                error_msg,
                gr.update(interactive=True),
                gr.update(interactive=False),
                gr.update(value="An error occurred while setting up the agent")
            )
            self._cleanup_state() 