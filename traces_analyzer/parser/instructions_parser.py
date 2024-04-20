from collections.abc import Iterable
from dataclasses import dataclass
from typing import Sequence

from traces_analyzer.parser.environment.call_context import CallContext
from traces_analyzer.parser.environment.call_context_manager import CallContextManager, CallTree
from traces_analyzer.parser.events_parser import TraceEvent
from traces_analyzer.parser.instruction import Instruction
from traces_analyzer.parser.instruction_io import parse_instruction_io
from traces_analyzer.parser.instructions import get_instruction_class
from traces_analyzer.parser.environment.parsing_environment import ParsingEnvironment
from traces_analyzer.parser.environment.storage import MemoryValue
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


def _parse_instructions(
    events: Iterable[TraceEvent],
    env: ParsingEnvironment,
    call_context_manager: CallContextManager,
) -> Iterable[Instruction]:
    events_iterator = events.__iter__()
    try:
        current_event = next(events_iterator)
    except StopIteration:
        # no events to parse
        return []
    call_context = call_context_manager.get_current_call_context()
    env.current_stack = current_event.stack
    env.memory.set(0, MemoryValue(current_event.memory or ""))

    for next_event in events_iterator:
        instruction = parse_instruction(env, current_event.op, current_event.pc, next_event.stack, next_event.memory)
        call_context_manager.on_step(instruction, next_event.depth)
        env.current_step_index += 1
        env.current_stack = next_event.stack
        env.memory.set(0, MemoryValue(next_event.memory or ""))
        current_event = next_event
        call_context = call_context_manager.get_current_call_context()

        if call_context.depth > env.current_call_context.depth:
            env.on_call_enter(call_context)
        elif call_context.depth < env.current_call_context.depth:
            env.on_call_exit(call_context)

        yield instruction

    # NOTE: for the last event, we pass None instead of next_event
    # if this breaks something in the future (eg if the last TraceEvent is a SLOAD
    # that tries to read the stack for the result), we'll need to change this
    yield parse_instruction(env, current_event.op, current_event.pc, [], None)


def parse_instruction(
    env: ParsingEnvironment,
    opcode: int,
    program_counter: int,
    next_stack: Sequence[str],
    next_memory: str | None,
) -> Instruction:
    name = opcode_to_name(opcode) or "UNKNOWN"

    cls = get_instruction_class(opcode) or Instruction
    spec = cls.io_specification

    io = parse_instruction_io(
        spec,
        env.current_stack,
        env.memory,
        next_stack,
        next_memory,
    )
    return cls(
        opcode,
        name,
        program_counter,
        env.current_step_index,
        env.current_call_context,
        io.inputs_stack,
        io.outputs_stack,
        io.input_memory,
        io.output_memory,
    )
