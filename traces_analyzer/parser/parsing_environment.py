from dataclasses import dataclass
from typing import Sequence

from traces_analyzer.parser.call_context import CallContext
from traces_analyzer.parser.storage import MemoryStorage


@dataclass
class ParsingEnvironment:
    current_call_context: CallContext
    current_stack: Sequence[str] = ()
    memory = MemoryStorage()
    current_step_index = 0

    def on_call_enter(self, new_call_context: CallContext):
        self.current_call_context = new_call_context
        self.memory.on_call_enter()

    def on_call_exit(self, new_call_context: CallContext):
        self.current_call_context = new_call_context
        self.memory.on_call_exit()
