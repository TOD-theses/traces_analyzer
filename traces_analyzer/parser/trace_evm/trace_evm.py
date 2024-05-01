from dataclasses import dataclass

from traces_analyzer.parser.environment.call_context_manager import update_call_context
from traces_analyzer.parser.environment.parsing_environment import InstructionOutputOracle, ParsingEnvironment
from traces_analyzer.parser.instructions.instruction import Instruction
from traces_analyzer.parser.instructions.instructions import CallInstruction, get_instruction_class
from traces_analyzer.parser.storage.storage_value import StorageByteGroup
from traces_analyzer.parser.storage.storage_writes import StorageWrites
from traces_analyzer.utils.mnemonics import opcode_to_name


@dataclass
class InstructionMetadata:
    opcode: int
    pc: int


class TraceEVM:
    def __init__(self, env: ParsingEnvironment, verify_storages: bool) -> None:
        self.env = env
        self._should_verify_storages = verify_storages

    def step(self, instruction_metadata: InstructionMetadata, output_oracle: InstructionOutputOracle) -> Instruction:
        instruction = parse_instruction(self.env, instruction_metadata, output_oracle)

        self.env.current_step_index += 1
        self._update_storages(instruction, output_oracle)
        self._update_call_context(instruction, output_oracle)
        # for those, where we did not model the stack wrties, simply overwrite it with the oracle
        if not instruction.implemented_flow():
            self._apply_stack_oracle(instruction, output_oracle)

        if self._should_verify_storages:
            self._verify_storage(instruction, output_oracle)

        return instruction

    def _update_storages(self, instruction: Instruction, output_oracle: InstructionOutputOracle):
        # NOTE: memory expansion on access is done by the io flow parsing. Maybe it should also be moved here.
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
            self._apply_stack_oracle(instruction, output_oracle)
        elif next_call_context.depth < self.env.current_call_context.depth:
            self.env.on_call_exit(next_call_context)
            self._apply_stack_oracle(instruction, output_oracle)
            call = current_call_context.initiating_instruction
            if call is not None:
                return_writes = call.get_return_writes(current_call_context)
                self._apply_storage_writes(return_writes, call, output_oracle)

    def _apply_stack_oracle(self, instruction: Instruction, output_oracle: InstructionOutputOracle):
        self.env.stack.clear()
        self.env.stack.push_all([StorageByteGroup.from_hexstring(val, -1) for val in output_oracle.stack])

    def _apply_storage_writes(
        self, storage_writes: StorageWrites, instruction: Instruction, output_oracle: InstructionOutputOracle
    ):
        for _ in storage_writes.stack_pops:
            self.env.stack.pop()
        for stack_push in storage_writes.stack_pushes:
            self.env.stack.push(stack_push.value)
        for stack_set in storage_writes.stack_sets:
            self.env.stack.set(stack_set.index, stack_set.value)
        for mem_write in storage_writes.memory:
            self.env.memory.set(mem_write.offset, mem_write.value, self.env.current_step_index)
        if storage_writes.return_data:
            self.env.current_call_context.return_data = storage_writes.return_data.value

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
        oracle_memory = output_oracle.memory.without_prefix().strip("0")

        if memory != oracle_memory:
            raise Exception(
                f"The environments memory does not match the output_oracles memory after {instruction}:\n"
                f"Environment: {memory}\n"
                f"Oracle:      {oracle_memory}"
            )
        stack = [x.get_hexstring() for x in self.env.stack.get_all()]
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
    if cls.implemented_flow():
        io, flow = cls.parse_flow(env, output_oracle)
    else:
        io = cls.parse_io(env, output_oracle)
        flow = None

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
