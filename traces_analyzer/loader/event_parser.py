from abc import ABC, abstractmethod
import json
from typing import Generic, Iterable, TypeVar
from typing_extensions import override

from traces_parser.parser.events_parser import (
    TraceEvent,
    parse_events_eip3155,
    parse_events_struct_logs,
)

T = TypeVar("T")


class EventsParser(ABC, Generic[T]):
    @abstractmethod
    def parse(self, lines: T) -> Iterable[TraceEvent]:
        pass


class EIP3155EventsParser(EventsParser):
    """Parse a EIP-3155 traces where each step is passed as a separate JSON string"""

    @override
    def parse(self, lines: Iterable[str]) -> Iterable[TraceEvent]:
        return parse_events_eip3155(lines)


class VmTraceEventsParser(EventsParser):
    """Parse a vm trace, where the whole iterable is a single JSON string"""

    @override
    def parse(self, lines: Iterable[str]) -> Iterable[TraceEvent]:
        json_str = "".join(lines)
        return parse_events_struct_logs(json.loads(json_str)["structLogs"])


class VmTraceDictEventsParser(EventsParser):
    """Parse a vm trace, where the whole iterable is a single JSON string"""

    @override
    def parse(self, lines: dict) -> Iterable[TraceEvent]:
        return parse_events_struct_logs(lines["structLogs"])
