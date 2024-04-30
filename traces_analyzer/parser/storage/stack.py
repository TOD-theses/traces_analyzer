from typing import Sequence

from traces_analyzer.parser.storage.storage_value import StorageByteGroup
from traces_analyzer.utils.hexstring import HexString


class Stack:
    def __init__(self) -> None:
        self._stack: list[StorageByteGroup] = []

    def peek(self, index: int) -> StorageByteGroup:
        """Get the nth element from the top of the stack (0-indexed)"""
        return self._stack[-index - 1]

    def push(self, value: StorageByteGroup):
        """Push a single value to the top of the stack"""
        if len(value.get_hexstring()) != 64:
            padding = StorageByteGroup.deprecated_from_hexstring(HexString("0" * (64 - len(value.get_hexstring()))))
            value = padding + value
        self._stack.append(value)

    def push_all(self, values: Sequence[StorageByteGroup]):
        """Push multiple values. First one will be on top of the stack"""
        for value in reversed(values):
            self.push(value)

    def get_all(self) -> Sequence[StorageByteGroup]:
        """Get all values. First one will be the top of the stack"""
        return [self.peek(i) for i in range(self.size())]

    def pop(self) -> StorageByteGroup:
        result = self.peek(0)
        self._stack.pop()
        return result

    def clear(self):
        self._stack = []

    def size(self):
        return len(self._stack)
