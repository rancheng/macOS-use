import gradio as gr
import os
import sys
from pathlib import Path
import traceback
from typing import Optional, Generator, AsyncGenerator
import asyncio
import queue
import logging
import io
from datetime import datetime

# Add the parent directory to sys.path to import mlx_use
sys.path.append(str(Path(__file__).parent.parent))

from mlx_use import Agent
from mlx_use.controller.service import Controller
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import SecretStr

# Set up logging to capture terminal output
class QueueHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        try:
            msg = self.format(record)
            self.log_queue.put(f"{msg}\n")
        except Exception:
            self.handleError(record)

# LLM model mappings
LLM_MODELS = {
    "OpenAI": ["gpt-4o", "o3-mini"],
    "Anthropic": ["claude-3-5-sonnet-20240620"],
    "Google": ["gemini-1.5-flash-002"],
    "alibaba": ["qwen-2.5-72b-instruct"]
}

def get_llm(provider: str, model: str, api_key: str) -> Optional[object]:
    """Initialize LLM based on provider"""
    try:
        if provider == "OpenAI":
            return ChatOpenAI(model=model, api_key=SecretStr(api_key))
        elif provider == "Anthropic":
            return ChatAnthropic(model=model, api_key=SecretStr(api_key))
        elif provider == "Google":
            return ChatGoogleGenerativeAI(model=model, api_key=SecretStr(api_key))
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    except Exception as e:
        raise ValueError(f"Failed to initialize {provider} LLM: {str(e)}")

class MacOSUseGradioApp:
    def __init__(self):
        self.agent = None
        self.controller = Controller()
        self.is_running = False
        self.log_queue = queue.Queue()
        self.setup_logging()
        self.terminal_buffer = []
        self._cleanup_state()

    def _cleanup_state(self):
        """Reset all state variables"""
        self.is_running = False
        self.agent = None
        self.terminal_buffer = []
        while not self.log_queue.empty():
            try:
                self.log_queue.get_nowait()
            except queue.Empty:
                break

    def setup_logging(self):
        """Set up logging to capture terminal output"""
        # Remove existing handlers to prevent duplicates
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Create queue handler
        queue_handler = QueueHandler(self.log_queue)
        queue_handler.setFormatter(logging.Formatter('%(message)s'))
        root_logger.addHandler(queue_handler)

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
            return (
                self.get_terminal_output() + "\nAgent stopped by user",
                gr.update(interactive=True),
                gr.update(interactive=False)
            )
        return (
            "No agent running",
            gr.update(interactive=True),
            gr.update(interactive=False)
        )

    def update_model_choices(self, provider):
        """Update model choices based on provider selection"""
        return gr.Dropdown.update(choices=LLM_MODELS.get(provider, []))

    async def run_agent(
        self,
        task: str,
        max_steps: int,
        max_actions: int,
        llm_provider: str,
        llm_model: str,
        api_key: str,
    ) -> AsyncGenerator[tuple[str, dict, dict], None]:
        """Run the agent with the specified configuration"""
        # Clean up any previous state
        self._cleanup_state()
        
        try:
            # Validate inputs
            if not task:
                raise ValueError("Task description is required")
            if not api_key:
                raise ValueError("API key is required")
            
            # Initialize LLM
            llm = get_llm(llm_provider, llm_model, api_key)
            if not llm:
                raise ValueError(f"Failed to initialize {llm_provider} LLM")
            
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
                
                # While the agent is running, yield updates
                while not agent_task.done() and self.is_running:
                    current_output = self.get_terminal_output()
                    if current_output != last_update:
                        yield (
                            current_output,
                            gr.update(interactive=False),
                            gr.update(interactive=True)
                        )
                        last_update = current_output
                    await asyncio.sleep(0.1)
                
                if not agent_task.done():
                    agent_task.cancel()
                    await asyncio.sleep(0.1)  # Give it a moment to cancel
                else:
                    result = await agent_task
                
                # Final update
                final_output = self.get_terminal_output()
                if final_output != last_update:
                    yield (
                        final_output,
                        gr.update(interactive=True),
                        gr.update(interactive=False)
                    )
                
            except Exception as e:
                error_details = f"Error Details:\n{traceback.format_exc()}"
                self.terminal_buffer.append(f"\nError occurred:\n{str(e)}\n\n{error_details}")
                yield (
                    "".join(self.terminal_buffer),
                    gr.update(interactive=True),
                    gr.update(interactive=False)
                )
            finally:
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

    def create_interface(self):
        """Create the Gradio interface"""
        with gr.Blocks(title="macOS-use Interface") as demo:
            gr.Markdown("# macOS-use Interface")
            
            with gr.Tab("Agent"):
                with gr.Row():
                    with gr.Column(scale=2):
                        task_input = gr.Textbox(
                            label="Task Description",
                            placeholder="Enter task (e.g., 'open calculator')",
                            lines=3
                        )
                        with gr.Row():
                            max_steps = gr.Slider(
                                minimum=1,
                                maximum=100,
                                value=25,
                                step=1,
                                label="Max Run Steps"
                            )
                            max_actions = gr.Slider(
                                minimum=1,
                                maximum=20,
                                value=1,
                                step=1,
                                label="Max Actions per Step"
                            )
                        with gr.Row():
                            run_button = gr.Button("Run Agent", variant="primary")
                            stop_button = gr.Button("Stop", variant="stop", interactive=False)
                    
                    with gr.Column(scale=3):
                        terminal_output = gr.Textbox(
                            label="Terminal Output",
                            lines=25,
                            interactive=False,
                            autoscroll=True
                        )
            
            with gr.Tab("Configuration"):
                llm_provider = gr.Dropdown(
                    choices=list(LLM_MODELS.keys()),
                    label="LLM Provider",
                    value="OpenAI"
                )
                llm_model = gr.Dropdown(
                    choices=LLM_MODELS["OpenAI"],
                    label="Model"
                )
                api_key = gr.Textbox(
                    label="API Key",
                    type="password",
                    placeholder="Enter your API key"
                )
                
                # Update model choices when provider changes
                llm_provider.change(
                    fn=self.update_model_choices,
                    inputs=llm_provider,
                    outputs=llm_model
                )
            
            # Event handlers
            run_button.click(
                fn=self.run_agent,
                inputs=[
                    task_input,
                    max_steps,
                    max_actions,
                    llm_provider,
                    llm_model,
                    api_key
                ],
                outputs=[
                    terminal_output,
                    run_button,
                    stop_button
                ],
                queue=True,
                api_name=False
            )
            
            stop_button.click(
                fn=self.stop_agent,
                outputs=[
                    terminal_output,
                    run_button,
                    stop_button
                ]
            )

        return demo

def main():
    app = MacOSUseGradioApp()
    demo = app.create_interface()
    demo.queue(concurrency_count=1)  # Limit to one concurrent task
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )

if __name__ == "__main__":
    main() 