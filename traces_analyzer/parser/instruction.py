from dataclasses import dataclass
from typing import ClassVar

from typing_extensions import Mapping

from traces_analyzer.parser.environment.call_context import CallContext
from traces_analyzer.parser.environment.parsing_environment import InstructionOutputOracle, ParsingEnvironment
from traces_analyzer.parser.instruction_io import InstructionIOSpec, parse_instruction_io


@dataclass(frozen=True, repr=False)
class Instruction:
    opcode: int
    name: str
    program_counter: int
    step_index: int
    call_context: CallContext
    stack_inputs: tuple[str, ...]
    stack_outputs: tuple[str, ...]
    memory_input: str | None
    memory_output: str | None
    io_specification: ClassVar[InstructionIOSpec] = InstructionIOSpec()

    def get_data(self) -> Mapping[str, object]:
        """Return formatted instruction data, depending on the instruction type"""
        return {}

    @classmethod
    def parse_io(cls, env: ParsingEnvironment, output_oracle: InstructionOutputOracle):
        return parse_instruction_io(
            cls.io_specification,
            env.stack.current_stack(),
            env.memory,
            output_oracle.stack,
            output_oracle.memory,
        )

    def __str__(self) -> str:
        return f"<{self.name}@{self.call_context.code_address}:{self.program_counter} {self.get_data()}>"

    def __repr__(self) -> str:
        return self.__str__()
