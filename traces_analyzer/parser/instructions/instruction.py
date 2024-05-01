from dataclasses import dataclass, field
from typing import ClassVar, cast

from typing_extensions import Mapping

from traces_analyzer.parser.environment.call_context import CallContext
from traces_analyzer.parser.environment.parsing_environment import InstructionOutputOracle, ParsingEnvironment
from traces_analyzer.parser.information_flow.information_flow_dsl import FlowSpec, noop
from traces_analyzer.parser.information_flow.information_flow_dsl_implementation import Flow
from traces_analyzer.parser.instructions.instruction_io import InstructionIO, InstructionIOSpec, parse_instruction_io
from traces_analyzer.parser.storage.storage_writes import StorageAccesses, StorageWrites
from traces_analyzer.utils.hexstring import HexString


@dataclass(frozen=True, repr=False)
class Instruction:
    opcode: int
    name: str
    program_counter: int
    step_index: int
    call_context: CallContext = field(compare=False, hash=False)
    stack_inputs: tuple[HexString, ...]
    stack_outputs: tuple[HexString, ...]
    memory_input: HexString | None
    memory_output: HexString | None
    flow: Flow | None = None
    io_specification: ClassVar[InstructionIOSpec | None] = None
    flow_spec: ClassVar[FlowSpec] = noop()

    def get_accesses(self) -> StorageAccesses:
        if self.flow is not None:
            return self.flow.accesses
        return StorageAccesses()

    def get_writes(self) -> StorageWrites:
        if self.flow is not None:
            return self.flow.writes
        return StorageWrites()

    def get_data(self) -> Mapping[str, object]:
        """Return formatted instruction data, depending on the instruction type"""
        return {}

    @classmethod
    def implemented_flow(cls) -> bool:
        return cls.io_specification is None

    @classmethod
    def parse_io(cls, env: ParsingEnvironment, output_oracle: InstructionOutputOracle) -> InstructionIO:
        return cls._parse_from_io_spec(cast(InstructionIOSpec, cls.io_specification), env, output_oracle)

    @classmethod
    def parse_flow(cls, env: ParsingEnvironment, output_oracle: InstructionOutputOracle) -> tuple[InstructionIO, Flow]:
        return cls._parse_from_flow_spec(cls.flow_spec, env, output_oracle)

    @staticmethod
    def _parse_from_io_spec(
        io_spec: InstructionIOSpec, env: ParsingEnvironment, output_oracle: InstructionOutputOracle
    ) -> InstructionIO:
        return parse_instruction_io(
            io_spec,
            env.stack,
            env.memory,
            output_oracle.stack,
            output_oracle.memory,
        )

    @staticmethod
    def _parse_from_flow_spec(
        flow_spec: FlowSpec, env: ParsingEnvironment, output_oracle: InstructionOutputOracle
    ) -> tuple[InstructionIO, Flow]:
        flow = flow_spec.compute(env, output_oracle)

        stack_inputs: list[HexString] = []
        stack_outputs: list[HexString] = []
        mem_input: HexString | None = None
        mem_output: HexString | None = None

        for access_stack in flow.accesses.stack:
            stack_inputs.append(access_stack.value.get_hexstring())
        for access_mem in flow.accesses.memory:
            mem_input = mem_input or access_mem.value.get_hexstring()
        for stack_push in flow.writes.stack_pushes:
            stack_outputs.append(stack_push.value.get_hexstring())
        for stack_set in flow.writes.stack_sets:
            stack_outputs.append(stack_set.value.get_hexstring())
        for mem_write in flow.writes.memory:
            mem_output = mem_output or mem_write.value.get_hexstring()

        io = InstructionIO(tuple(stack_inputs), tuple(stack_outputs), mem_input, mem_output)
        return io, flow

    def __str__(self) -> str:
        return (
            f"<{self.name}@{self.call_context.code_address}:{self.program_counter}#{self.step_index} "
            f"{self.get_data()}>"
        )

    def __repr__(self) -> str:
        return self.__str__()
