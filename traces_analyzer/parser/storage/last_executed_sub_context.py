from typing_extensions import override

from traces_analyzer.parser.environment.call_context import CallContext
from traces_analyzer.parser.storage.storage import Storage


class LastExecutedSubContextStorage(Storage):
    """Maintain one storage content per call context.
    When entering a new context, the factory is used to create a new content"""

    def __init__(self) -> None:
        super().__init__()
        self._last_executed_sub_context_stack: list[CallContext | None] = [None]

    @override
    def on_call_enter(self, current_call_context: CallContext, next_call_context: CallContext):
        super().on_call_enter(current_call_context, next_call_context)
        self._last_executed_sub_context_stack.append(None)

    @override
    def on_call_exit(self, current_call_context: CallContext, next_call_context: CallContext):
        super().on_call_exit(current_call_context, next_call_context)
        self._call_exit(current_call_context)

    @override
    def on_revert(self, current_call_context: CallContext, next_call_context: CallContext):
        super().on_revert(current_call_context, next_call_context)
        self._call_exit(current_call_context)

    def _call_exit(self, current_call_context: CallContext):
        self._last_executed_sub_context_stack.pop()
        self._last_executed_sub_context_stack[-1] = current_call_context

    def current(self) -> CallContext | None:
        return self._last_executed_sub_context_stack[-1]
