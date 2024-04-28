from dataclasses import dataclass

from traces_analyzer.parser.environment.call_context import CallContext
from traces_analyzer.parser.storage.memory import Memory
from traces_analyzer.parser.storage.stack import Stack
from traces_analyzer.parser.storage.storage import ContextSpecificStorage
from traces_analyzer.utils.hexstring import HexString


class ParsingEnvironment:
    def __init__(self, root_call_context: CallContext) -> None:
        self.current_call_context = root_call_context
        self.current_step_index = 0
        self._stack_storage = ContextSpecificStorage(Stack)
        self._memory_storage = ContextSpecificStorage(Memory)

    def on_call_enter(self, new_call_context: CallContext):
        self.current_call_context = new_call_context
        self._stack_storage.on_call_enter()
        self._memory_storage.on_call_enter()

    def on_call_exit(self, new_call_context: CallContext):
        self.current_call_context = new_call_context
        self._stack_storage.on_call_exit()
        self._memory_storage.on_call_exit()

    @property
    def stack(self) -> Stack:
        return self._stack_storage.current()

    @property
    def memory(self) -> Memory:
        return self._memory_storage.current()


@dataclass
class InstructionOutputOracle:
    """Output data we know from the trace. Oracle, because we can peek one step into the future with this"""

    stack: list[HexString]
    memory: HexString
    depth: int | None
