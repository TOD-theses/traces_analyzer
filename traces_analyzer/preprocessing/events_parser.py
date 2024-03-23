import json
from collections.abc import Iterable
from dataclasses import dataclass


@dataclass
class TraceEvent:
    pc: int
    op: int
    stack: list[str]
    depth: int


def parse_events(lines: Iterable[str]) -> Iterable[TraceEvent]:
    for line in lines:
        obj = json.loads(line)
        if "pc" not in obj:
            continue
        yield TraceEvent(
            pc=obj["pc"],
            op=obj["op"],
            stack=obj["stack"],
            depth=obj["depth"],
        )
