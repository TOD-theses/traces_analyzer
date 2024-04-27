"""

mload:
    spec = [stack.push(mem.range(stack.arg(0), const(32)))]

instr_io = mload.parse_io(env, oracle)
accesses = instr_io.accesses
writes = instr_io.writes

for mem_write in writes.memory:
    env.memory.set(mem_write.offset, mem_write.value, instr)

-> where do we want to link the instruction to the accesses and writes?
    it would be convenient when creating the values of accesses and writes
    but there we likely don't yet have the instruction to reference

    we could do it at instruction construction

    or we do it in a separate information flow tracking layer?
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from traces_analyzer.parser.environment.parsing_environment import InstructionOutputOracle, ParsingEnvironment
from traces_analyzer.parser.storage.storage_writes import StorageAccesses, StorageWrites


@dataclass(frozen=True)
class InformationFlow:
    accesses: StorageAccesses
    writes: StorageWrites


class InformationFlowSpecification(ABC):
    @abstractmethod
    def parse_flow(self, env: ParsingEnvironment, output_oracle: InstructionOutputOracle) -> InformationFlow:
        pass
