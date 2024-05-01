from abc import ABC
from typing import Callable, Generic, TypeVar

from typing_extensions import override

from traces_analyzer.parser.environment.call_context import CallContext


class Storage(ABC):
    """
    Types of storage:
    - stack, memory => current call context as key (or stack based)
    - persistent/transient storage => address as key
    - balance, code => address as key
    - calldata, call value, return data => current or previous call context as a key
    """

    def on_call_enter(self, current_call_context: CallContext, next_call_context: CallContext):
        pass

    def on_call_exit(self, current_call_context: CallContext, next_call_context: CallContext):
        pass


StorageContent = TypeVar("StorageContent")


class ContextSpecificStorage(Storage, Generic[StorageContent]):
    """Maintain one storage content per call context.
    When entering a new context, the factory is used to create a new content"""

    def __init__(self, content_factory: Callable[[], StorageContent]) -> None:
        super().__init__()
        self._factory = content_factory
        self._content_stack: list[StorageContent] = [content_factory()]

    @override
    def on_call_enter(self, current_call_context: CallContext, next_call_context: CallContext):
        super().on_call_enter(current_call_context, next_call_context)
        self._content_stack.append(self._factory())

    @override
    def on_call_exit(self, current_call_context: CallContext, next_call_context: CallContext):
        super().on_call_exit(current_call_context, next_call_context)
        self._content_stack.pop()

    def current(self) -> StorageContent:
        return self._content_stack[-1]
