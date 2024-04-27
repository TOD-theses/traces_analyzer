from dataclasses import dataclass, field
from typing import ClassVar

from typing_extensions import Mapping

from traces_analyzer.parser.environment.call_context import CallContext
from traces_analyzer.parser.environment.parsing_environment import InstructionOutputOracle, ParsingEnvironment
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
    io_specification: ClassVar[InstructionIOSpec] = InstructionIOSpec()

    def get_accesses(self) -> StorageAccesses:
        return StorageAccesses()

    def get_writes(self) -> StorageWrites:
        return StorageWrites()

    def get_data(self) -> Mapping[str, object]:
        """Return formatted instruction data, depending on the instruction type"""
        return {}

    @classmethod
    def parse_io(cls, env: ParsingEnvironment, output_oracle: InstructionOutputOracle) -> InstructionIO:
        return parse_instruction_io(
            cls.io_specification,
            env.stack.current_stack(),
            env.memory,
            output_oracle.stack,
            output_oracle.memory,
        )

    def __str__(self) -> str:
        return (
            f"<{self.name}@{self.call_context.code_address}:{self.program_counter}#{self.step_index} "
            f"{self.get_data()}>"
        )

    def __repr__(self) -> str:
        return self.__str__()
