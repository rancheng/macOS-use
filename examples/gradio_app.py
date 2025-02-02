import asyncio
import gradio as gr

from mlx_use import Agent
from mlx_use.controller.service import Controller
from langchain_openai import ChatOpenAI

# As an example, we are instantiating a ChatOpenAI language model.
# Ensure you have your OpenAI API key set as an environment variable, or pass it here.
llm = ChatOpenAI(temperature=0.0)

def run_agent_sync(task: str, max_steps: int = 10, max_failures: int = 5) -> str:
    """
    Synchronous wrapper for running the agent.
    Given a task description and optional parameters,
    run a limited number of steps, and return the result.
    """
    return asyncio.run(run_agent(task, max_steps, max_failures))

async def run_agent(task: str, max_steps: int = 10, max_failures: int = 5) -> str:
    """
    Asynchronously create an Agent, run it for a set number of steps, 
    and return the string representation of the agent's final conversation history.
    """
    # Initialize the controller which registers available actions
    controller = Controller()
    
    # Create an Agent with specified parameters
    agent = Agent(
        task=task,
        llm=llm,
        controller=controller,
        use_vision=False,
        max_actions_per_step=1,
        max_failures=max_failures
    )
    
    # Run the agent with specified maximum steps
    history = await agent.run(max_steps=max_steps)
    
    # Return a string summary of the AgentHistoryList
    return str(history)

iface = gr.Interface(
    fn=run_agent_sync,
    inputs=[
        gr.Textbox(lines=2, placeholder="Enter your task here...", label="Task"),
        gr.Number(value=10, label="Max Steps", minimum=1, maximum=100, step=1),
        gr.Number(value=5, label="Max Failures", minimum=1, maximum=20, step=1)
    ],
    outputs=gr.Textbox(lines=20, label="Agent Conversation History"),
    title="macOS-use Application",
    description="""
        Enter a task you want to see done. This Gradio app creates an macOS-use instance
        from the mlx_use package, runs it (for a specified number of steps), and returns the final conversation history.
        
        Parameters:
        - Max Steps: Maximum number of steps the agent will take (default: 10)
        - Max Failures: Maximum number of consecutive failures before stopping (default: 5)
    """
)

if __name__ == "__main__":
    iface.launch(pwa=True) 