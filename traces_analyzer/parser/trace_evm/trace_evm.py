from dataclasses import dataclass

from traces_analyzer.parser.environment.call_context import CallContext
from traces_analyzer.parser.environment.call_context_manager import (
    exit_call_context,
    makes_exceptional_halt,
    update_call_context,
)
from traces_analyzer.parser.environment.parsing_environment import (
    InstructionOutputOracle,
    ParsingEnvironment,
)
from traces_analyzer.parser.instructions.instruction import Instruction
from traces_analyzer.parser.instructions.instructions import (
    CallInstruction,
    get_instruction_class,
)
from traces_analyzer.parser.storage.storage_value import StorageByteGroup
from traces_analyzer.parser.storage.storage_writes import StorageWrites
from traces_analyzer.utils.hexstring import HexString
from traces_analyzer.utils.mnemonics import opcode_to_name


@dataclass
class InstructionMetadata:
    opcode: int
    pc: int


class TraceEVM:
    def __init__(self, env: ParsingEnvironment, verify_storages: bool) -> None:
        self.env = env
        self._should_verify_storages = verify_storages

    def step(
        self,
        instruction_metadata: InstructionMetadata,
        output_oracle: InstructionOutputOracle,
    ) -> Instruction:
        self._check_exceptional_halt(instruction_metadata, output_oracle)

        instruction = parse_instruction(self.env, instruction_metadata, output_oracle)

        self.env.current_step_index += 1
        self._update_storages(instruction, output_oracle)
        self._check_call_context_changes(instruction, output_oracle)
        # we apply balance transfers after potential call context changes
        # such that they are not part of state snapshots and can be reverted properly
        self._apply_balance_transfers(instruction, output_oracle)

        if self._should_verify_storages:
            self._verify_storage(instruction, output_oracle)

        return instruction

    def _update_storages(
        self, instruction: Instruction, output_oracle: InstructionOutputOracle
    ):
        # NOTE: memory expansion on access is done by the io flow parsing. Maybe it should also be moved here.
        self._apply_storage_writes(instruction.get_writes(), instruction, output_oracle)

        if isinstance(instruction, CallInstruction) and not self._changes_depth(
            output_oracle
        ):
            self._apply_storage_writes(
                instruction.get_immediate_return_writes(self.env, output_oracle),
                instruction,
                output_oracle,
            )

    def _changes_depth(self, output_oracle: InstructionOutputOracle) -> bool:
        return self.env.current_call_context.depth != output_oracle.depth

    def _check_exceptional_halt(
        self,
        instruction_metadata: InstructionMetadata,
        output_oracle: InstructionOutputOracle,
    ):
        if not output_oracle.depth:
            return
        if makes_exceptional_halt(
            instruction_metadata.opcode,
            self.env.current_call_context.depth,
            output_oracle.depth,
        ):
            next_call_context = exit_call_context(
                self.env.current_call_context,
                instruction_metadata.opcode,
                output_oracle.depth,
            )
            call = self.env.current_call_context.initiating_instruction
            assert call is not None
            self._update_call_context(next_call_context)
            self.env.stack.push(
                StorageByteGroup.from_hexstring(
                    HexString("0").as_size(32), call.step_index
                )
            )

    def _check_call_context_changes(
        self, instruction: Instruction, output_oracle: InstructionOutputOracle
    ):
        next_call_context = update_call_context(
            self.env.current_call_context, instruction, output_oracle.depth
        )

        if next_call_context.depth > self.env.current_call_context.depth:
            self.env.on_call_enter(next_call_context)
        elif next_call_context.depth < self.env.current_call_context.depth:
            current_call_context = self.env.current_call_context
            self._update_call_context(next_call_context)
            call = current_call_context.initiating_instruction
            # update stack and memory
            if isinstance(call, CallInstruction):
                return_writes = call.get_return_writes(self.env, output_oracle)
                self._apply_storage_writes(return_writes, call, output_oracle)
            else:
                # for CREATE and CREATE2 and exceptional halts
                self._apply_stack_oracle(output_oracle)

    def _update_call_context(self, next_call_context: CallContext):
        if self.env.current_call_context.reverted:
            self.env.on_revert(next_call_context)
        else:
            self.env.on_call_exit(next_call_context)

    def _apply_stack_oracle(self, output_oracle: InstructionOutputOracle):
        self.env.stack.clear()
        self.env.stack.push_all(
            [StorageByteGroup.from_hexstring(val, -1) for val in output_oracle.stack]
        )

    def _apply_storage_writes(
        self,
        storage_writes: StorageWrites,
        instruction: Instruction,
        output_oracle: InstructionOutputOracle,
    ):
        for _ in storage_writes.stack_pops:
            self.env.stack.pop()
        for stack_push in storage_writes.stack_pushes:
            self.env.stack.push(stack_push.value)
        for stack_set in storage_writes.stack_sets:
            self.env.stack.set(stack_set.index, stack_set.value)
        for mem_write in storage_writes.memory:
            self.env.memory.set(
                mem_write.offset, mem_write.value, instruction.step_index
            )
        if storage_writes.return_data:
            self.env.current_call_context.return_data = storage_writes.return_data.value

    def _apply_balance_transfers(
        self, instruction: Instruction, output_oracle: InstructionOutputOracle
    ):
        for transfer in instruction.get_writes().balance_transfers:
            self.env.balances.modified_at_step_index(
                transfer.address_to.get_hexstring(), instruction.step_index
            )

    def _verify_storage(
        self, instruction: Instruction, output_oracle: InstructionOutputOracle
    ):
        """Verify that current storages match the output oracle"""
        """
        TODO also check for trailing zeros
            currently I ignore those, as I'm not sure if there is a bug in my implementation or the trace
            traces_analyzer --bundles traces/benchmark_traces/62a876599363fc9f281b2768
        """
        # ignore the last instruction, as we don't have an output oracle for it
        if output_oracle.depth is None:
            return
        current_depth = self.env.current_call_context.depth
        if current_depth != output_oracle.depth:
            raise Exception(
                f"The environments depth does not match the output_oracles depth after {instruction}:\n"
                f"Environment: {current_depth}\n"
                f"Oracle:      {output_oracle.depth}"
            )

        memory = self.env.memory.get_all().get_hexstring().without_prefix().strip("0")
        oracle_memory = output_oracle.memory.without_prefix().strip("0")

        if memory != oracle_memory:
            raise Exception(
                f"The environments memory does not match the output_oracles memory after {instruction}:\n"
                f"Environment: {memory}\n"
                f"Oracle:      {oracle_memory}"
            )

        stack = [x.get_hexstring().as_int() for x in self.env.stack.get_all()]
        oracle_stack = [x.as_int() for x in output_oracle.stack]

        if stack != oracle_stack:
            raise Exception(
                f"The environments stack does not match the output_oracles stack after {instruction}:\n"
                f"Environment: {stack}\n"
                f"Oracle:      {oracle_stack}"
            )


def parse_instruction(
    env: ParsingEnvironment,
    instruction_metadata: InstructionMetadata,
    output_oracle: InstructionOutputOracle,
) -> Instruction:
    opcode = instruction_metadata.opcode
    name = opcode_to_name(opcode) or "UNKNOWN"

    cls = get_instruction_class(opcode) or Instruction
    flow = cls.parse_flow(env, output_oracle)

    return cls(
        opcode,
        name,
        instruction_metadata.pc,
        env.current_step_index,
        env.current_call_context,
        flow,
    )
