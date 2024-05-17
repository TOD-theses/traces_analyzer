from abc import ABC, abstractmethod
from typing import Callable, Generic, TypeVar

from typing_extensions import Self, override

from traces_analyzer.parser.environment.call_context import CallContext


class Storage(ABC):
    def on_call_enter(
        self, current_call_context: CallContext, next_call_context: CallContext
    ):
        pass

    def on_call_exit(
        self, current_call_context: CallContext, next_call_context: CallContext
    ):
        pass

    def on_revert(
        self, current_call_context: CallContext, next_call_context: CallContext
    ):
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
    def on_call_enter(
        self, current_call_context: CallContext, next_call_context: CallContext
    ):
        super().on_call_enter(current_call_context, next_call_context)
        self._content_stack.append(self._factory())

    @override
    def on_call_exit(
        self, current_call_context: CallContext, next_call_context: CallContext
    ):
        super().on_call_exit(current_call_context, next_call_context)
        self._call_exit()

    @override
    def on_revert(
        self, current_call_context: CallContext, next_call_context: CallContext
    ):
        super().on_revert(current_call_context, next_call_context)
        self._call_exit()

    def _call_exit(self):
        self._content_stack.pop()

    def current(self) -> StorageContent:
        return self._content_stack[-1]


class CloneableStorage(Storage):
    @abstractmethod
    def clone(self) -> Self:
        pass


CloneableStorageType = TypeVar("CloneableStorageType", bound=CloneableStorage)


class RevertableStorage(Storage, Generic[CloneableStorageType]):
    """Maintain one storage snapshot of each parent call context and restore snapshot on revert"""

    def __init__(self, storage: CloneableStorageType) -> None:
        super().__init__()
        self._storage = storage
        # invariant: len(snapshots) + 1 == depth
        self._snapshots: list[CloneableStorageType] = []

    @override
    def on_call_enter(
        self, current_call_context: CallContext, next_call_context: CallContext
    ):
        super().on_call_enter(current_call_context, next_call_context)
        self._snapshots.append(self._storage.clone())

    @override
    def on_call_exit(
        self, current_call_context: CallContext, next_call_context: CallContext
    ):
        super().on_call_exit(current_call_context, next_call_context)
        self._snapshots.pop()

    @override
    def on_revert(
        self, current_call_context: CallContext, next_call_context: CallContext
    ):
        super().on_revert(current_call_context, next_call_context)
        self._storage = self._snapshots.pop()

    def current(self) -> CloneableStorageType:
        return self._storage
