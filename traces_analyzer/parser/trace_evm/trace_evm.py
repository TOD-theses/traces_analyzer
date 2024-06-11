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
from traces_analyzer.parser.storage.storage_writes import StorageAccesses, StorageWrites
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
        instruction = parse_instruction(self.env, instruction_metadata, output_oracle)

        made_exceptional_halt = self._check_exceptional_halt(
            instruction_metadata, output_oracle
        )
        if not made_exceptional_halt:
            self._update_storages(instruction)
            self._check_call_context_changes(instruction, output_oracle)
            # we apply balance transfers after potential call context changes
            # such that they are not part of state snapshots and can be reverted properly
            self._apply_balance_transfers(instruction)

        if self._should_verify_storages:
            self._verify_storage(instruction, output_oracle)

        self.env.current_step_index += 1

        return instruction

    def _update_storages(self, instruction: Instruction):
        self._apply_storage_accesses(instruction.get_accesses(), instruction)
        self._apply_storage_writes(instruction.get_writes(), instruction)

    def _changes_depth(self, output_oracle: InstructionOutputOracle) -> bool:
        return self.env.current_call_context.depth != output_oracle.depth

    def _check_exceptional_halt(
        self,
        instruction_metadata: InstructionMetadata,
        output_oracle: InstructionOutputOracle,
    ) -> bool:
        """Return True if it is an exceptional halt"""
        if not output_oracle.depth:
            return False
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
            self._update_call_context_on_exit(next_call_context)
            self.env.stack.push(
                StorageByteGroup.from_hexstring(
                    HexString("0").as_size(32), call.step_index
                )
            )
            return True
        return False

    def _check_call_context_changes(
        self, instruction: Instruction, output_oracle: InstructionOutputOracle
    ):
        # TODO: refactor, maybe return an enum for the type of call change
        # and in a second call actually get the call context?
        current_call_context = self.env.current_call_context
        next_call_context = update_call_context(
            self.env.current_call_context, instruction, output_oracle.depth
        )

        if next_call_context is current_call_context:
            return

        assert output_oracle.depth

        if output_oracle.depth > current_call_context.depth:
            self.env.on_call_enter(next_call_context)
        elif output_oracle.depth < current_call_context.depth:
            self._update_call_context_on_exit(next_call_context)
            call = current_call_context.initiating_instruction
            # update stack and memory
            if isinstance(call, CallInstruction):
                return_writes = call.get_return_writes(self.env, output_oracle)
                self._apply_storage_writes(return_writes, call)
            else:
                # for CREATE and CREATE2
                # TODO: do not replace the whole stack when returning from CREATE(2)
                self._apply_stack_oracle(instruction, output_oracle)
        else:
            # immediate call exit (call to EOA or precompiled contract)
            # we create new call frames so that returndata will point to this call
            # and it shows up in the call tree
            self.env.on_call_enter(next_call_context)
            self._update_call_context_on_exit(current_call_context)
            # update stack and memory
            if isinstance(instruction, CallInstruction):
                return_writes = instruction.get_immediate_return_writes(
                    self.env, output_oracle
                )
                self._apply_storage_writes(return_writes, instruction)
            else:
                # for CREATE and CREATE2
                self._apply_stack_oracle(instruction, output_oracle)

    def _update_call_context_on_exit(self, next_call_context: CallContext):
        if self.env.current_call_context.reverted:
            self.env.on_revert(next_call_context)
        else:
            self.env.on_call_exit(next_call_context)

    def _apply_stack_oracle(
        self, instruction: Instruction, output_oracle: InstructionOutputOracle
    ):
        # TODO: remove this method, as it overwrites all the data flow info we previously had
        self.env.stack.clear()
        self.env.stack.push_all(
            [
                StorageByteGroup.from_hexstring(val, instruction.step_index)
                for val in output_oracle.stack
            ]
        )

    def _apply_storage_accesses(
        self,
        storage_accesses: StorageAccesses,
        instruction: Instruction,
    ):
        for mem_access in storage_accesses.memory:
            self.env.memory.check_expansion(
                mem_access.offset, len(mem_access.value), instruction.step_index
            )

    def _apply_storage_writes(
        self,
        storage_writes: StorageWrites,
        instruction: Instruction,
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

    def _apply_balance_transfers(self, instruction: Instruction):
        for transfer in instruction.get_writes().balance_transfers:
            self.env.balances.modified_at_step_index(
                transfer.address_to.get_hexstring(), instruction.step_index
            )

    def _verify_storage(
        self, instruction: Instruction, output_oracle: InstructionOutputOracle
    ):
        """Verify that current storages match the output oracle"""
        # ignore the last instruction, as we don't have an output oracle for it
        if output_oracle.depth is None:
            return

        self._verify_depth(instruction, output_oracle.depth)
        self._verify_stack(instruction, output_oracle.stack)
        self._verify_memory(instruction, output_oracle.memory)

    def _verify_depth(self, instruction: Instruction, depth_oracle: int):
        depth = self.env.current_call_context.depth
        if depth != depth_oracle:
            raise Exception(
                f"The environments depth does not match the output_oracles depth after {instruction}:\n"
                f"Environment: {depth}\n"
                f"Oracle:      {depth_oracle}"
            )

    def _verify_stack(self, instruction: Instruction, stack_oracle: list[HexString]):
        stack_int = [x.get_hexstring().as_int() for x in self.env.stack.get_all()]
        stack_oracle_int = [x.as_int() for x in stack_oracle]

        if stack_int != stack_oracle_int:
            raise Exception(
                f"The environments stack does not match the output_oracles stack after {instruction}:\n"
                f"Environment: {stack_int}\n"
                f"Oracle:      {stack_oracle_int}"
            )

    def _verify_memory(self, instruction: Instruction, memory_oracle: HexString):
        memory = self.env.memory.get_all().get_hexstring()
        oracle_memory = memory_oracle

        if memory != oracle_memory:
            raise Exception(
                f"The environments memory does not match the output_oracles memory after {instruction}:\n"
                f"Environment: {memory}\n"
                f"Oracle:      {oracle_memory}"
            )


def parse_instruction(
    env: ParsingEnvironment,
    instruction_metadata: InstructionMetadata,
    output_oracle: InstructionOutputOracle,
) -> Instruction:
    opcode = instruction_metadata.opcode
    name = opcode_to_name(opcode) or "UNKNOWN"

    cls = get_instruction_class(opcode) or Instruction

    try:
        flow = cls.parse_flow(env, output_oracle)
    except Exception as e:
        raise Exception(
            f"Could not parse {name} flow at step {env.current_step_index}: {instruction_metadata}"
        ) from e

    return cls(
        opcode,
        name,
        instruction_metadata.pc,
        env.current_step_index,
        env.current_call_context,
        flow,
    )
