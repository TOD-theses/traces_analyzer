from dataclasses import dataclass

from traces_analyzer.parser.environment.call_context import CallContext
from traces_analyzer.parser.storage.balances import Balances, BalancesStorage
from traces_analyzer.parser.storage.last_executed_sub_context import LastExecutedSubContextStorage
from traces_analyzer.parser.storage.memory import Memory
from traces_analyzer.parser.storage.stack import Stack
from traces_analyzer.parser.storage.storage import ContextSpecificStorage, Storage
from traces_analyzer.utils.hexstring import HexString


class ParsingEnvironment:
    def __init__(self, root_call_context: CallContext) -> None:
        self.current_call_context = root_call_context
        self.current_step_index = 0
        self._stack_storage = ContextSpecificStorage(Stack)
        self._memory_storage = ContextSpecificStorage(Memory)
        self._balances_storage = BalancesStorage()
        self._last_executed_sub_context = LastExecutedSubContextStorage()

    def on_call_enter(self, next_call_context: CallContext):
        for storage in self._storages():
            storage.on_call_enter(self.current_call_context, next_call_context)
        self.current_call_context = next_call_context

    def on_call_exit(self, next_call_context: CallContext):
        for storage in self._storages():
            storage.on_call_exit(self.current_call_context, next_call_context)
        self.current_call_context = next_call_context

    def _storages(self) -> list[Storage]:
        return [self._last_executed_sub_context, self._stack_storage, self._memory_storage, self._balances_storage]

    @property
    def stack(self) -> Stack:
        return self._stack_storage.current()

    @property
    def memory(self) -> Memory:
        return self._memory_storage.current()

    @property
    def balances(self) -> Balances:
        return self._balances_storage.current()

    @property
    def last_executed_sub_context(self) -> CallContext | None:
        return self._last_executed_sub_context.current()


@dataclass
class InstructionOutputOracle:
    """Output data we know from the trace. Oracle, because we can peek one step into the future with this"""

    stack: list[HexString]
    memory: HexString
    depth: int | None
