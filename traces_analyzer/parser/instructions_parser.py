from collections.abc import Iterable
from dataclasses import dataclass
from typing import Sequence

from traces_analyzer.parser.environment.call_context import CallContext
from traces_analyzer.parser.environment.call_context_manager import CallContextManager, CallTree
from traces_analyzer.parser.environment.parsing_environment import ParsingEnvironment
from traces_analyzer.parser.environment.storage import MemoryValue, StackValue
from traces_analyzer.parser.events_parser import TraceEvent
from traces_analyzer.parser.instruction import Instruction
from traces_analyzer.parser.instruction_io import parse_instruction_io
from traces_analyzer.parser.instructions import get_instruction_class
from traces_analyzer.utils.mnemonics import opcode_to_name


@dataclass
class TransactionParsingInfo:
    sender: str
    to: str
    calldata: str


@dataclass
class ParsedTransaction:
    instructions: Sequence[Instruction]
    call_tree: CallTree


def parse_instructions(parsing_info: TransactionParsingInfo, trace_events: Iterable[TraceEvent]) -> ParsedTransaction:
    call_context_manager = _setup_call_context_manager(parsing_info.sender, parsing_info.to, parsing_info.calldata)
    env = ParsingEnvironment(call_context_manager.get_current_call_context())

    instructions = list(_parse_instructions(trace_events, env, call_context_manager))

    return ParsedTransaction(instructions, call_context_manager.get_call_tree())


def _setup_call_context_manager(sender: str, to: str, calldata: str) -> CallContextManager:
    return CallContextManager(
        CallContext(
            parent=None,
            calldata=calldata,
            depth=1,
            msg_sender=sender,
            code_address=to,
            storage_address=to,
        )
    )


@dataclass
class InstructionMetadata:
    opcode: int
    pc: int


@dataclass
class InstructionOutputOracle:
    """Output data we know from the trace. Oracle, because we can peek one step into the future with this"""

    stack: list[str]
    memory: str
    depth: int | None


def _parse_instructions(
    events: Iterable[TraceEvent],
    env: ParsingEnvironment,
    call_context_manager: CallContextManager,
) -> Iterable[Instruction]:
    tracer_evm = TracerEVM(env, call_context_manager)
    events_iterator = events.__iter__()
    try:
        current_event = next(events_iterator)
    except StopIteration:
        # no events to parse
        return []

    for next_event in events_iterator:
        yield tracer_evm.step(
            instruction_metadata=InstructionMetadata(current_event.op, current_event.pc),
            output_oracle=InstructionOutputOracle(next_event.stack, next_event.memory or "", next_event.depth),
        )
        current_event = next_event

    yield tracer_evm.step(
        instruction_metadata=InstructionMetadata(current_event.op, current_event.pc),
        output_oracle=InstructionOutputOracle([], "", None),
    )


class TracerEVM:
    def __init__(self, env: ParsingEnvironment, call_context_manager: CallContextManager) -> None:
        self.env = env
        self.call_context_manager = call_context_manager

    def step(self, instruction_metadata: InstructionMetadata, output_oracle: InstructionOutputOracle) -> Instruction:
        instruction = self._parse_instruction(instruction_metadata, output_oracle)

        self.env.current_step_index += 1
        self._update_storages(instruction, output_oracle)
        self._update_call_context(instruction, output_oracle)

        return instruction

    def _update_storages(self, instruction: Instruction, output_oracle: InstructionOutputOracle):
        self.env.stack.clear()
        self.env.stack.push(StackValue(output_oracle.stack))
        self.env.memory.set(0, MemoryValue(output_oracle.memory))

    def _update_call_context(self, instruction: Instruction, output_oracle: InstructionOutputOracle):
        self.call_context_manager.on_step(instruction, output_oracle.depth)
        call_context = self.call_context_manager.get_current_call_context()

        if call_context.depth > self.env.current_call_context.depth:
            self.env.on_call_enter(call_context)
        elif call_context.depth < self.env.current_call_context.depth:
            self.env.on_call_exit(call_context)

    def _parse_instruction(
        self, instruction_metadata: InstructionMetadata, output_oracle: InstructionOutputOracle
    ) -> Instruction:
        opcode = instruction_metadata.opcode
        name = opcode_to_name(opcode) or "UNKNOWN"

        cls = get_instruction_class(opcode) or Instruction
        spec = cls.io_specification

        io = parse_instruction_io(
            spec,
            self.env.stack.current_stack(),
            self.env.memory,
            output_oracle.stack,
            output_oracle.memory,
        )
        return cls(
            opcode,
            name,
            instruction_metadata.pc,
            self.env.current_step_index,
            self.env.current_call_context,
            io.inputs_stack,
            io.outputs_stack,
            io.input_memory,
            io.output_memory,
        )
