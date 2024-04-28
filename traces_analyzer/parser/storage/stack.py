from dataclasses import replace
from typing import Sequence

from traces_analyzer.parser.storage.storage_value import HexStringStorageValue
from traces_analyzer.utils.hexstring import HexString


class Stack:
    def __init__(self) -> None:
        self._stack: list[HexString] = []

    def peek(self, index: int) -> HexStringStorageValue:
        """Get the nth element from the top of the stack (0-indexed)"""
        return HexStringStorageValue(self._stack[-index - 1])

    def push(self, value: HexStringStorageValue):
        """Push a single value to the top of the stack"""
        if len(value.get_hexstring()) != 64:
            value = replace(value, hexstring=value.get_hexstring().rjust(64, "0"))
        self._stack.append(value.get_hexstring())

    def push_all(self, values: Sequence[HexStringStorageValue]):
        """Push multiple values. First one will be on top of the stack"""
        for value in reversed(values):
            self.push(value)

    def get_all(self) -> Sequence[HexStringStorageValue]:
        """Get all values. First one will be the top of the stack"""
        return [self.peek(i) for i in range(self.size())]

    def pop(self) -> HexStringStorageValue:
        result = self.peek(0)
        self._stack.pop()
        return result

    def clear(self):
        self._stack = []

    def size(self):
        return len(self._stack)
