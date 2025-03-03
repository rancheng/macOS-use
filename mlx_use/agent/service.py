from __future__ import annotations

import asyncio
import base64
import io
import json
import logging
import os
import platform
import textwrap
import uuid
from io import BytesIO
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar

from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
	BaseMessage,
	SystemMessage,
)
from lmnr import observe
from openai import RateLimitError
from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel, ValidationError

from mlx_use.agent.message_manager.service import MessageManager
from mlx_use.agent.prompts import AgentMessagePrompt, SystemPrompt
from mlx_use.agent.views import (
	ActionResult,
	AgentError,
	AgentHistory,
	AgentHistoryList,
	AgentOutput,
	AgentStepInfo,
)
from mlx_use.controller.registry.views import ActionModel
from mlx_use.controller.service import Controller
from mlx_use.mac.tree import MacUITreeBuilder
from mlx_use.telemetry.service import ProductTelemetry
from mlx_use.telemetry.views import (
	AgentEndTelemetryEvent,
	AgentRunTelemetryEvent,
	AgentStepTelemetryEvent,
)
from mlx_use.utils import time_execution_async

load_dotenv()
logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class Agent:
	def __init__(
		self,
		task: str,
		llm: BaseChatModel,
		controller: Controller = Controller(),
		use_vision: bool = True,
		save_conversation_path: Optional[str] = None,
		save_conversation_path_encoding: Optional[str] = 'utf-8',
		max_failures: int = 5,
		retry_delay: int = 10,
		system_prompt_class: Type[SystemPrompt] = SystemPrompt,
		max_input_tokens: int = 128000,
		validate_output: bool = False,
		generate_gif: bool | str = True,
		include_attributes: list[str] = [
			'title',
			'type',
			'name',
			'role',
			'tabindex',
			'aria-label',
			'placeholder',
			'value',
			'alt',
			'aria-expanded',
		],
		max_error_length: int = 400,
		max_actions_per_step: int = 10,
		initial_actions: Optional[List[Dict[str, Dict[str, Any]]]] = None,
		# Cloud Callbacks
		register_new_step_callback: Callable[['str', 'AgentOutput', int], None] | None = None,
		register_done_callback: Callable[['AgentHistoryList'], None] | None = None,
		tool_calling_method: Optional[str] = 'auto',
	):
		self.agent_id = str(uuid.uuid4())  # unique identifier for the agent

		self.task = task
		self.use_vision = use_vision
		self.llm = llm
		self.save_conversation_path = save_conversation_path
		self.save_conversation_path_encoding = save_conversation_path_encoding
		self._last_result = None
		self.include_attributes = include_attributes
		self.max_error_length = max_error_length
		self.generate_gif = generate_gif

		self.mac_tree_builder = MacUITreeBuilder()
		# Controller setup
		self.controller = controller
		self.max_actions_per_step = max_actions_per_step

		self.system_prompt_class = system_prompt_class

		# Telemetry setup
		self.telemetry = ProductTelemetry()

		# Action and output models setup
		self._setup_action_models()
		self._set_version_and_source()
		self.max_input_tokens = max_input_tokens

		self._set_model_names()

		self.tool_calling_method = self.set_tool_calling_method(tool_calling_method)

		self.message_manager = MessageManager(
			llm=self.llm,
			task=self.task,
			action_descriptions=self.controller.registry.get_prompt_description(),
			system_prompt_class=self.system_prompt_class,
			max_input_tokens=self.max_input_tokens,
			include_attributes=self.include_attributes,
			max_error_length=self.max_error_length,
			max_actions_per_step=self.max_actions_per_step,
		)

		# Step callback
		self.register_new_step_callback = register_new_step_callback
		self.register_done_callback = register_done_callback

		# Tracking variables
		self.history: AgentHistoryList = AgentHistoryList(history=[])
		self.n_steps = 1
		self.consecutive_failures = 0
		self.max_failures = max_failures
		self.retry_delay = retry_delay
		self.validate_output = validate_output
		self.initial_actions = self._convert_initial_actions(initial_actions) if initial_actions else None
		if save_conversation_path:
			logger.info(f'Saving conversation to {save_conversation_path}')

		self._paused = False
		self._stopped = False

	def _set_version_and_source(self) -> None:
		version = '0.0.1'
		source = 'mlx-use'
		logger.debug(f'Version: {version}, Source: {source}')
		self.version = version
		self.source = source

	def _set_model_names(self) -> None:
		self.chat_model_library = self.llm.__class__.__name__
		if hasattr(self.llm, 'model_name'):
			self.model_name = self.llm.model_name  # type: ignore
		elif hasattr(self.llm, 'model'):
			self.model_name = self.llm.model  # type: ignore
		else:
			self.model_name = 'Unknown'

	def _setup_action_models(self) -> None:
		"""Setup dynamic action models from controller's registry"""
		# Get the dynamic action model from controller's registry
		self.ActionModel = self.controller.registry.create_action_model()
		# Create output model with the dynamic actions
		self.AgentOutput = AgentOutput.type_with_custom_actions(self.ActionModel)

	def set_tool_calling_method(self, tool_calling_method: Optional[str]) -> Optional[str]:
		if tool_calling_method == 'auto':
			if self.chat_model_library == 'ChatGoogleGenerativeAI':
				return None
			elif self.chat_model_library == 'ChatOpenAI':
				return 'function_calling'
			elif self.chat_model_library == 'AzureChatOpenAI':
				return 'function_calling'
			else:
				return None

	def get_last_pid(self) -> Optional[int]:
		"""Get the last pid from the last result"""
		latest_pid = None
		if self._last_result:
			for r in self._last_result:
				if r.current_app_pid:
					latest_pid = r.current_app_pid
		return latest_pid

	@time_execution_async("--step")
	async def step(self, step_info: Optional[AgentStepInfo] = None) -> None:
		await asyncio.sleep(1)
		"""Execute one step of the task"""
		logger.info(f"\n📍 Step {self.n_steps}")
		state = None
		model_output = None
		result: list[ActionResult] = []

		try:
			if not self.get_last_pid():
				state = "Starting new task - no app is currently open. Please use open_app action to begin."

			root = await self.mac_tree_builder.build_tree(self.get_last_pid())
			if root:
				state = root.get_clickable_elements_string()
				# print the ui tree 
				logger.debug(f"\n\nstep {self.n_steps} \nState: {state}\n\n")
				
				# consider adding the full ui tree details, much more tokens!
				# state = (
				# 	"Interactive Elements:\n" + root.get_clickable_elements_string() +
				# 	"\n\nFull UI Tree Details:\n" + root.get_detailed_string()
				# )

			self.message_manager.add_state_message(state, self._last_result, step_info)
			input_messages = self.message_manager.get_messages()

			try:
				model_output = await self.get_next_action(input_messages)

				if self.register_new_step_callback:
					self.register_new_step_callback(state, model_output, self.n_steps)

				self._save_conversation(input_messages, model_output)
				self.message_manager._remove_last_state_message()
				self.message_manager.add_model_output(model_output)
			except Exception as e:
				self.message_manager._remove_last_state_message()
				raise e

			result: list[ActionResult] = await self.controller.multi_act(model_output.action, self.mac_tree_builder)
			self._last_result = result

			if len(result) > 0 and result[-1].is_done:
				logger.info(f"📄 Result: {result[-1].extracted_content}")

			self.consecutive_failures = 0

		except Exception as e:
			result = await self._handle_step_error(e)
			self._last_result = result

		finally:
			actions = [a.model_dump(exclude_unset=True) for a in model_output.action] if model_output else []
			self.telemetry.capture(
				AgentStepTelemetryEvent(
					agent_id=self.agent_id,
					step=self.n_steps,
					actions=actions,
					consecutive_failures=self.consecutive_failures,
					step_error=[r.error for r in result if r.error] if result else ["No result"],
				)
			)
			if not result:
				return

			if state:
				self._make_history_item(model_output, state, result)

	async def _handle_step_error(self, error: Exception) -> list[ActionResult]:
		"""Handle all types of errors that can occur during a step"""
		include_trace = logger.isEnabledFor(logging.DEBUG)
		error_msg = AgentError.format_error(error, include_trace=include_trace)
		prefix = f'❌ Result failed {self.consecutive_failures + 1}/{self.max_failures} times:\n '

		if isinstance(error, (ValidationError, ValueError)):
			logger.error(f'{prefix}{error_msg}')
			if 'Max token limit reached' in error_msg:
				# cut tokens from history
				self.message_manager.max_input_tokens = self.max_input_tokens - 500
				logger.info(f'Cutting tokens from history - new max input tokens: {self.message_manager.max_input_tokens}')
				self.message_manager.cut_messages()
			elif 'Could not parse response' in error_msg:
				# give model a hint how output should look like
				error_msg += '\n\nReturn a valid JSON object with the required fields.'

			self.consecutive_failures += 1
		elif isinstance(error, RateLimitError):
			logger.warning(f'{prefix}{error_msg}')
			await asyncio.sleep(self.retry_delay)
			self.consecutive_failures += 1
		else:
			logger.error(f'{prefix}{error_msg}')
			self.consecutive_failures += 1

		return [ActionResult(error=error_msg, include_in_memory=True)]

	def _make_history_item(
		self,
		model_output: AgentOutput | None,
		state: str,
		result: list[ActionResult],
	) -> None:
		"""Create and store history item"""
		logger.debug("Adding history item: state=%s, model_output=%s, result=%s",
					 state, model_output.json() if model_output else None, [r.model_dump() for r in result])

		interacted_element = None
		len_result = len(result)

		interacted_elements = [None]

		history_item = AgentHistory(model_output=model_output, result=result, state=state)

		self.history.history.append(history_item)

	@time_execution_async('--get_next_action')
	async def get_next_action(self, input_messages: list[BaseMessage]) -> AgentOutput:
		"""Get next action from LLM based on current state"""
		if self.tool_calling_method is None:
			structured_llm = self.llm.with_structured_output(self.AgentOutput, include_raw=True)
		else:
			structured_llm = self.llm.with_structured_output(self.AgentOutput, include_raw=True, method=self.tool_calling_method)

		response: dict[str, Any] = await structured_llm.ainvoke(input_messages)  # type: ignore

		parsed: AgentOutput | None = response['parsed']
		if parsed is None:
			raise ValueError('Could not parse response.')

		# cut the number of actions to max_actions_per_step
		parsed.action = parsed.action[: self.max_actions_per_step]
		self._log_response(parsed)
		self.n_steps += 1

		return parsed

	def _log_response(self, response: AgentOutput) -> None:
		"""Log the model's response"""
		if 'Success' in response.current_state.evaluation_previous_goal:
			emoji = '👍'
		elif 'Failed' in response.current_state.evaluation_previous_goal:
			emoji = '⚠'
		else:
			emoji = '🤷'

		logger.info(f'{emoji} Eval: {response.current_state.evaluation_previous_goal}')
		logger.info(f'🧠 Memory: {response.current_state.memory}')
		logger.info(f'🎯 Next goal: {response.current_state.next_goal}')
		for i, action in enumerate(response.action):
			logger.info(f'🛠️  Action {i + 1}/{len(response.action)}: {action.model_dump_json(exclude_unset=True)}')

	def _save_conversation(self, input_messages: list[BaseMessage], response: Any) -> None:
		"""Save conversation history to file if path is specified"""
		if not self.save_conversation_path:
			return

		# create folders if not exists
		os.makedirs(os.path.dirname(self.save_conversation_path), exist_ok=True)

		with open(
			self.save_conversation_path + f'_{self.n_steps}.txt',
			'w',
			encoding=self.save_conversation_path_encoding,
		) as f:
			self._write_messages_to_file(f, input_messages)
			self._write_response_to_file(f, response)

	def _write_messages_to_file(self, f: Any, messages: list[BaseMessage]) -> None:
		"""Write messages to conversation file"""
		for message in messages:
			f.write(f' {message.__class__.__name__} \n')

			if isinstance(message.content, list):
				for item in message.content:
					if isinstance(item, dict) and item.get('type') == 'text':
						f.write(item['text'].strip() + '\n')
			elif isinstance(message.content, str):
				try:
					content = json.loads(message.content)
					f.write(json.dumps(content, indent=2) + '\n')
				except json.JSONDecodeError:
					f.write(message.content.strip() + '\n')

			f.write('\n')

	def _write_response_to_file(self, f: Any, response: Any) -> None:
		"""Write model response to conversation file"""
		f.write(' RESPONSE\n')
		f.write(json.dumps(json.loads(response.model_dump_json(exclude_unset=True)), indent=2))

	def _log_agent_run(self) -> None:
		"""Log the agent run"""
		logger.info(f'🚀 Starting task: {self.task}')

		logger.debug(f'Version: {self.version}, Source: {self.source}')
		self.telemetry.capture(
			AgentRunTelemetryEvent(
				agent_id=self.agent_id,
				use_vision=self.use_vision,
				task=self.task,
				model_name=self.model_name,
				chat_model_library=self.chat_model_library,
				version=self.version,
				source=self.source,
			)
		)

	@observe(name='agent.run')
	async def run(self, max_steps: int = 100) -> AgentHistoryList:
		"""Execute the task with maximum number of steps"""
		try:
			self._log_agent_run()

			# Execute initial actions if provided
			if self.initial_actions:
				result = await self.controller.multi_act(
					self.initial_actions, self.mac_tree_builder, check_for_new_elements=False
				)
				self._last_result = result

			for step in range(max_steps):
				if self._too_many_failures():
					break

				# Check control flags before each step
				if not await self._handle_control_flags():
					break

				await self.step()

				if self.history.is_done():
					logger.info('✅ Task completed successfully')
					if self.register_done_callback:
						self.register_done_callback(self.history)
					break
			else:
				logger.info('❌ Failed to complete task in maximum steps')

			return self.history
		finally:
			self.telemetry.capture(
				AgentEndTelemetryEvent(
					agent_id=self.agent_id,
					success=self.history.is_done(),
					steps=self.n_steps,
					max_steps_reached=self.n_steps >= max_steps,
					errors=self.history.errors(),
				)
			)

	def _too_many_failures(self) -> bool:
		"""Check if we should stop due to too many failures"""
		if self.consecutive_failures >= self.max_failures:
			logger.error(f'❌ Stopping due to {self.max_failures} consecutive failures')
			return True
		return False

	async def _handle_control_flags(self) -> bool:
		"""Handle pause and stop flags. Returns True if execution should continue."""
		if self._stopped:
			logger.info('Agent stopped')
			return False

		while self._paused:
			await asyncio.sleep(0.2)  # Small delay to prevent CPU spinning
			if self._stopped:  # Allow stopping while paused
				return False

		return True

	def save_history(self, file_path: Optional[str | Path] = None) -> None:
		"""Save the history to a file"""
		if not file_path:
			file_path = 'AgentHistory.json'
		self.history.save_to_file(file_path)

	def _convert_initial_actions(self, actions: List[Dict[str, Dict[str, Any]]]) -> List[ActionModel]:
		"""Convert dictionary-based actions to ActionModel instances"""
		converted_actions = []
		action_model = self.ActionModel
		for action_dict in actions:
			# Each action_dict should have a single key-value pair
			action_name = next(iter(action_dict))
			params = action_dict[action_name]

			# Get the parameter model for this action from registry
			action_info = self.controller.registry.registry.actions[action_name]
			param_model = action_info.param_model

			# Create validated parameters using the appropriate param model
			validated_params = param_model(**params)

			# Create ActionModel instance with the validated parameters
			action_model = self.ActionModel(**{action_name: validated_params})
			converted_actions.append(action_model)

		return converted_actions
