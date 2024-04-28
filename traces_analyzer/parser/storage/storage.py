from abc import ABC
from typing import Callable, Generic, TypeVar

from typing_extensions import override


class Storage(ABC):
    """
    Types of storage:
    - stack, memory => current call context as key (or stack based)
    - persistent/transient storage => address as key
    - balance, code => address as key
    - calldata, call value, return data => current or previous call context as a key
    """

    def on_call_enter(self):
        pass

    def on_call_exit(self):
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
    def on_call_enter(self):
        super().on_call_enter()
        self._content_stack.append(self._factory())

    @override
    def on_call_exit(self):
        super().on_call_exit()
        self._content_stack.pop()

    def current(self) -> StorageContent:
        return self._content_stack[-1]
