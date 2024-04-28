from collections.abc import Iterable
from dataclasses import dataclass
from typing import Sequence

from traces_analyzer.parser.environment.call_context import CallContext
from traces_analyzer.parser.environment.call_context_manager import CallTree, build_call_tree, update_call_context
from traces_analyzer.parser.environment.parsing_environment import InstructionOutputOracle, ParsingEnvironment
from traces_analyzer.parser.events_parser import TraceEvent
from traces_analyzer.parser.instructions.instruction import Instruction
from traces_analyzer.parser.instructions.instructions import CallInstruction, get_instruction_class
from traces_analyzer.parser.storage.storage_value import HexStringStorageValue
from traces_analyzer.parser.storage.storage_writes import StorageAccesses, StorageWrites
from traces_analyzer.utils.hexstring import HexString
from traces_analyzer.utils.mnemonics import opcode_to_name


@dataclass
class TransactionParsingInfo:
    sender: HexString
    to: HexString
    calldata: HexString
    verify_storages: bool = True


@dataclass
class ParsedTransaction:
    instructions: Sequence[Instruction]
    call_tree: CallTree


def parse_instructions(parsing_info: TransactionParsingInfo, trace_events: Iterable[TraceEvent]) -> ParsedTransaction:
    root_call_context = _create_root_call_context(parsing_info.sender, parsing_info.to, parsing_info.calldata)

    instructions = _parse_instructions(trace_events, root_call_context, parsing_info.verify_storages)
    call_tree = build_call_tree(root_call_context, instructions)

    return ParsedTransaction(instructions, call_tree)


def _create_root_call_context(sender: HexString, to: HexString, calldata: HexString) -> CallContext:
    return CallContext(
        parent=None,
        calldata=calldata,
        depth=1,
        msg_sender=sender,
        code_address=to,
        storage_address=to,
    )


@dataclass
class InstructionMetadata:
    opcode: int
    pc: int


def _parse_instructions(
    events: Iterable[TraceEvent], root_call_context: CallContext, verify_storages: bool
) -> Sequence[Instruction]:
    tracer_evm = TracerEVM(root_call_context, verify_storages)
    events_iterator = events.__iter__()
    try:
        current_event = next(events_iterator)
    except StopIteration:
        # no events to parse
        return []

    instructions = []
    for next_event in events_iterator:
        instructions.append(
            tracer_evm.step(
                instruction_metadata=InstructionMetadata(current_event.op, current_event.pc),
                output_oracle=InstructionOutputOracle(
                    next_event.stack, next_event.memory or HexString(""), next_event.depth
                ),
            )
        )
        current_event = next_event

    instructions.append(
        tracer_evm.step(
            instruction_metadata=InstructionMetadata(current_event.op, current_event.pc),
            output_oracle=InstructionOutputOracle([], HexString(""), None),
        )
    )
    return instructions


class TracerEVM:
    def __init__(self, root_call_context: CallContext, verify_storages: bool) -> None:
        self.env = ParsingEnvironment(root_call_context)
        self._should_verify_storages = verify_storages

    def step(self, instruction_metadata: InstructionMetadata, output_oracle: InstructionOutputOracle) -> Instruction:
        instruction = parse_instruction(self.env, instruction_metadata, output_oracle)

        self.env.current_step_index += 1
        self._update_storages(instruction, output_oracle)
        self._update_call_context(instruction, output_oracle)
        self._apply_stack_oracle(output_oracle)

        if self._should_verify_storages:
            self._verify_storage(instruction, output_oracle)

        return instruction

    def _update_storages(self, instruction: Instruction, output_oracle: InstructionOutputOracle):
        self._apply_storage_writes(instruction.get_writes(), instruction, output_oracle)
        if isinstance(instruction, CallInstruction):
            self._apply_storage_writes(
                instruction.get_immediate_return_writes(output_oracle), instruction, output_oracle
            )

    def _update_call_context(self, instruction: Instruction, output_oracle: InstructionOutputOracle):
        current_call_context = self.env.current_call_context
        next_call_context = update_call_context(self.env.current_call_context, instruction, output_oracle.depth)

        if next_call_context.depth > self.env.current_call_context.depth:
            self.env.on_call_enter(next_call_context)
        elif next_call_context.depth < self.env.current_call_context.depth:
            self.env.on_call_exit(next_call_context)
            call = current_call_context.initiating_instruction
            if call is not None:
                return_writes = call.get_return_writes(current_call_context)
                self._apply_storage_writes(return_writes, call, output_oracle)

    def _apply_stack_oracle(self, output_oracle: InstructionOutputOracle):
        # at least currently, we always overwrite the stack with the oracle
        # in the future, we should use the instructions stack outputs instead (pops and pushes)
        self.env.stack.clear()
        self.env.stack.push_all([HexStringStorageValue(val) for val in reversed(output_oracle.stack)])

    def _apply_storage_accesses(self, storage_accesses: StorageAccesses):
        for mem_access in storage_accesses.memory:
            self.env.memory.check_expansion(mem_access.offset, len(mem_access.value.get_hexstring()) // 2)

    def _apply_storage_writes(
        self, storage_writes: StorageWrites, instruction: Instruction, output_oracle: InstructionOutputOracle
    ):
        for mem_write in storage_writes.memory:
            self.env.memory.set(mem_write.offset, mem_write.value)
        if storage_writes.return_data:
            self.env.current_call_context.return_data = storage_writes.return_data.value.get_hexstring()

    def _verify_storage(self, instruction: Instruction, output_oracle: InstructionOutputOracle):
        """Verify that current storages match the output oracle"""
        """
        TODO also check for trailing zeros
            currently I ignore those, as I'm not sure if there is a bug in my implementation or the trace
            traces_analyzer --bundles traces/benchmark_traces/62a876599363fc9f281b2768
        """
        if not output_oracle.memory:
            return

        memory = self.env.memory.get_all().get_hexstring().strip("0")
        oracle_memory = output_oracle.memory.strip("0")

        if memory != oracle_memory:
            raise Exception(
                f"The environments memory does not match the output_oracles memory after {instruction}:\n"
                f"Environment: {memory}\n"
                f"Oracle:      {oracle_memory}"
            )
        stack = [x.get_hexstring().as_size(32) for x in reversed(self.env.stack.get_all())]
        oracle_stack = [x.as_size(32) for x in output_oracle.stack]

        if stack != oracle_stack:
            raise Exception(
                f"The environments stack does not match the output_oracles stack after {instruction}:\n"
                f"Environment: {stack}\n"
                f"Oracle:      {oracle_stack}"
            )


def parse_instruction(
    env, instruction_metadata: InstructionMetadata, output_oracle: InstructionOutputOracle
) -> Instruction:
    opcode = instruction_metadata.opcode
    name = opcode_to_name(opcode) or "UNKNOWN"

    cls = get_instruction_class(opcode) or Instruction
    if cls.io_specification:
        io = cls.parse_io(env, output_oracle)
        flow = None
    else:
        io, flow = cls.parse_flow(env, output_oracle)

    return cls(
        opcode,
        name,
        instruction_metadata.pc,
        env.current_step_index,
        env.current_call_context,
        io.inputs_stack,
        io.outputs_stack,
        io.input_memory,
        io.output_memory,
        flow,
    )
