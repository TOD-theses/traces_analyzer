from dataclasses import dataclass

from traces_analyzer.parser.environment.call_context import CallContext
from traces_analyzer.parser.environment.storage import MemoryStorage, StackStorage


@dataclass
class ParsingEnvironment:
    current_call_context: CallContext
    stack = StackStorage()
    memory = MemoryStorage()
    current_step_index = 0

    def on_call_enter(self, new_call_context: CallContext):
        self.current_call_context = new_call_context
        self.stack.on_call_enter()
        self.memory.on_call_enter()

    def on_call_exit(self, new_call_context: CallContext):
        self.current_call_context = new_call_context
        self.stack.on_call_exit()
        self.memory.on_call_exit()
