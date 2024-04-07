import json
from collections.abc import Iterable
from dataclasses import dataclass


@dataclass
class TraceEvent:
    pc: int
    op: int
    stack: list[str]
    depth: int
    memory: str | None = None

    def mem_at(self, offset_bytes: int, size_bytes: int) -> str | None:
        """Return the specified memory slice. If memory is not set, return None."""
        if not self.memory:
            return None
        start = 2 * offset_bytes
        end = 2 * (offset_bytes + size_bytes)
        return self.memory[start:end]


def parse_events(lines: Iterable[str]) -> Iterable[TraceEvent]:
    for line in lines:
        obj = json.loads(line)
        if "pc" not in obj:
            continue
        memory = None
        if "memory" in obj:
            memory = obj["memory"].removeprefix("0x")
        yield TraceEvent(
            pc=obj["pc"],
            op=obj["op"],
            stack=obj["stack"],
            memory=memory,
            depth=obj["depth"],
        )
