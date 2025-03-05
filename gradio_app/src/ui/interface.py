import gradio as gr
from typing import Dict, List, Any

def create_agent_tab(app_instance) -> List[gr.components.Component]:
    with gr.Row():
        # Left Column (scale=2)
        with gr.Column(scale=2):
            gr.Markdown("### Examples: How to prompt the agent")            
            # Category Selection Buttons
            with gr.Row():
                quick_tasks_btn = gr.Button("Quick Tasks", variant="secondary")
                multi_step_btn = gr.Button("Multi-Step Tasks", variant="primary")
                advanced_btn = gr.Button("Advanced Workflows", variant="secondary")
            
            gr.Markdown("This is <span style='color: red; font-weight: bold;'>NOT a chat</span> - Check our prompt examples!")
            
            with gr.Group():
                with gr.Row():
                    gr.Markdown("<div style='text-align: center; width: 100%; padding-top: 3px;'>Task Prompt</div>")
                    refine_prompt_btn = gr.Button("Refine Prompt", size="sm")
                with gr.Row():
                    task_input = gr.Textbox(
                        label="",
                        placeholder="Enter task (e.g., 'open calculator')",
                        lines=3
                    )

            share_prompt = gr.Checkbox(
                label="Share prompt (only!) anonymously",
                value=app_instance.preferences["share_prompt"],
                info="Sharing your prompt (and prompt only) ANONYMOUSLY will help us improve our agent."
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
                    value=5,
                    step=1,
                    label="Max Actions per Step"
                )
            with gr.Row():
                run_button = gr.Button("Run", variant="primary")
                stop_button = gr.Button("Stop", interactive=False)

        # Right Column (scale=3)
        with gr.Column(scale=3):
            result_output = gr.Textbox(
                label="Result",
                lines=3,
                interactive=False,
                autoscroll=True
            )
            
            with gr.Accordion("Steps & Actions", open=False) as terminal_accordion:
                terminal_output = gr.Textbox(
                    label="Terminal Output",
                    lines=25,
                    interactive=False,
                    autoscroll=True
                )
            
            # Dynamic Example Containers
            with gr.Column() as examples_box:
                gr.Markdown("#### Task prompts examples, Try all of them!")
                
                # Level description markdown that will be updated
                level_description = gr.Markdown(visible=False)
                
                # Scrollable container for all example categories
                with gr.Column(elem_classes="scrollable-container") as examples_container:
                    # Quick Tasks Container
                    with gr.Column(visible=False) as quick_tasks_container:
                        quick_tasks = app_instance.example_categories.get("Quick Tasks", [])
                        quick_buttons = []
                        for example in quick_tasks:
                            btn = gr.Button(
                                value=example["name"],
                                variant="secondary"
                            )
                            quick_buttons.append(btn)
                            btn.click(
                                fn=lambda p=example["prompt"]: p,
                                outputs=task_input
                            )

                    # Multi-Step Tasks Container
                    with gr.Column(visible=True) as multi_step_container:
                        multi_step_tasks = app_instance.example_categories.get("Multi-Step Tasks", [])
                        for task in multi_step_tasks:
                            # Task name as a header
                            gr.Markdown(f"### {task['name']}")
                            # Buttons in a horizontal row below the task name
                            if "levels" in task:
                                with gr.Row():
                                    for level_dict in task["levels"]:
                                        level = level_dict["level"]
                                        prompt = level_dict["prompt"]
                                        level_descriptions = {
                                            "Bad": "Might work, but since this is not a chat, it's probably not the best way to do it.",
                                            "Good": "Will probably work, good enough for short prompt tasks",
                                            "Expert": "Most likely to work, for complex apps and tasks, use that!"
                                        }
                                        btn = gr.Button(
                                            value=f"{level} Example",
                                            variant="secondary"
                                        )
                                        btn.click(
                                            fn=lambda p=prompt, l=level, desc=level_descriptions.get(level, ""): (p, desc),
                                            outputs=[task_input, level_description]
                                        ).then(
                                            fn=lambda: gr.update(visible=True),
                                            outputs=level_description
                                        )
                                # Add some spacing between tasks
                                gr.Markdown("---")

                    # Advanced Workflows Container
                    with gr.Column(visible=False) as advanced_tasks_container:
                        advanced_tasks = app_instance.example_categories.get("Advanced Workflows", [])
                        for example in advanced_tasks:
                            btn = gr.Button(
                                value=example["name"],
                                variant="secondary"
                            )
                            btn.click(
                                fn=lambda p=example["prompt"]: p,
                                outputs=task_input
                            )

            # Add CSS for scrollable container to the interface
            gr.HTML("""
                <style>
                    .scrollable-container {
                        height: 400px;
                        overflow-y: auto;
                        padding-right: 10px;
                        margin-top: 10px;
                    }
                    /* Style the scrollbar */
                    .scrollable-container::-webkit-scrollbar {
                        width: 8px;
                    }
                    .scrollable-container::-webkit-scrollbar-track {
                        background: #f1f1f1;
                        border-radius: 4px;
                    }
                    .scrollable-container::-webkit-scrollbar-thumb {
                        background: #888;
                        border-radius: 4px;
                    }
                    .scrollable-container::-webkit-scrollbar-thumb:hover {
                        background: #555;
                    }
                </style>
            """)

            # Category selection handlers
            def update_category_visibility(category):
                return {
                    quick_tasks_container: gr.update(visible=category == "Quick Tasks"),
                    advanced_tasks_container: gr.update(visible=category == "Advanced Workflows"),
                    multi_step_container: gr.update(visible=category == "Multi-Step Tasks"),
                    quick_tasks_btn: gr.update(variant="primary" if category == "Quick Tasks" else "secondary"),
                    multi_step_btn: gr.update(variant="primary" if category == "Multi-Step Tasks" else "secondary"),
                    advanced_btn: gr.update(variant="primary" if category == "Advanced Workflows" else "secondary"),
                    examples_box: gr.update(visible=True)
                }

            # Set up category button click handlers
            quick_tasks_btn.click(
                fn=lambda: update_category_visibility("Quick Tasks"),
                outputs=[
                    quick_tasks_container, advanced_tasks_container, multi_step_container,
                    quick_tasks_btn, multi_step_btn, advanced_btn, examples_box
                ]
            )
            
            multi_step_btn.click(
                fn=lambda: update_category_visibility("Multi-Step Tasks"),
                outputs=[
                    quick_tasks_container, advanced_tasks_container, multi_step_container,
                    quick_tasks_btn, multi_step_btn, advanced_btn, examples_box
                ]
            )
            
            advanced_btn.click(
                fn=lambda: update_category_visibility("Advanced Workflows"),
                outputs=[
                    quick_tasks_container, advanced_tasks_container, multi_step_container,
                    quick_tasks_btn, multi_step_btn, advanced_btn, examples_box
                ]
            )

    return [
        task_input, refine_prompt_btn, share_prompt, max_steps, max_actions,
        run_button, stop_button, result_output, terminal_output
    ]

def create_automations_tab(app_instance) -> List[gr.components.Component]:
    with gr.Row():
        with gr.Column(scale=2):
            automation_name = gr.Textbox(
                label="Automation Name",
                placeholder="Enter automation name"
            )
            automation_description = gr.Textbox(
                label="Description",
                placeholder="Enter automation description",
                lines=2
            )
            add_automation_btn = gr.Button("Add Automation", variant="primary")
            
            automation_list = gr.Dropdown(
                label="Select Automation",
                choices=list(app_instance.automations.keys()),
                interactive=True
            )
            
            agent_prompt = gr.Textbox(
                label="Agent Prompt",
                placeholder="Enter agent prompt",
                lines=3,
                interactive=True
            )
            
            with gr.Row():
                add_agent_btn = gr.Button("Add Agent", variant="primary")
                remove_agent_btn = gr.Button("Remove Selected Agent", variant="stop")
            
            run_automation_btn = gr.Button("Run Automation", variant="primary")
            
        with gr.Column(scale=3):
            agents_list = gr.List(
                label="Agents in Flow",
                headers=["#", "Prompt"],
                type="array",
                interactive=True,
                col_count=2
            )
            automation_output = gr.Textbox(
                label="Automation Output",
                lines=25,
                interactive=False,
                autoscroll=True
            )
    
    return [
        automation_name, automation_description, add_automation_btn,
        automation_list, agent_prompt, add_agent_btn, remove_agent_btn,
        run_automation_btn, agents_list, automation_output
    ]

def create_configuration_tab(app_instance) -> List[gr.components.Component]:
    # Get saved provider and model from preferences, or use defaults
    default_provider = app_instance.preferences.get("llm_provider", "OpenAI")
    
    llm_provider = gr.Dropdown(
        choices=list(app_instance.llm_models.keys()),
        label="LLM Provider",
        value=default_provider
    )
    
    # Get the models for the current provider
    available_models = app_instance.llm_models.get(default_provider, [])
    default_model = app_instance.preferences.get("llm_model", available_models[0] if available_models else None)
    
    llm_model = gr.Dropdown(
        choices=available_models,
        label="Model",
        value=default_model
    )
    
    api_key = gr.Textbox(
        label="API Key",
        type="password",
        placeholder="Enter your API key",
        value=app_instance.get_saved_api_key(default_provider)
    )
    
    # Add sharing preferences section
    gr.Markdown("### Sharing Settings")
    
    share_terminal = gr.Checkbox(
        label="Share terminal output anonymously",
        value=app_instance.preferences.get("share_terminal", True),
        info="Sharing terminal output helps us understand how the agent performs tasks."
    )
    
    return [llm_provider, llm_model, api_key, share_terminal] 