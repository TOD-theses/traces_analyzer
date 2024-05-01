import json
from collections.abc import Iterable
from dataclasses import dataclass

from traces_analyzer.utils.hexstring import HexString


@dataclass(frozen=True)
class TraceEvent:
    pc: int
    op: int
    stack: list[HexString]
    depth: int
    memory: HexString | None = None


def parse_events(lines: Iterable[str]) -> Iterable[TraceEvent]:
    for line in lines:
        obj = json.loads(line)
        if "pc" not in obj:
            continue
        memory = None
        if "memory" in obj:
            memory = HexString(obj["memory"])
        yield TraceEvent(
            pc=obj["pc"],
            op=obj["op"],
            stack=[HexString(val).as_size(32) for val in reversed(obj["stack"])],
            memory=memory,
            depth=obj["depth"],
        )
