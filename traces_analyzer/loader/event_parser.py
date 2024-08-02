from abc import ABC, abstractmethod
import json
from typing import Iterable
from typing_extensions import override

from traces_parser.parser.events_parser import (
    TraceEvent,
    parse_events_eip3155,
    parse_events_struct_logs,
)


class EventsParser(ABC):
    @abstractmethod
    def parse(self, lines: Iterable[str]) -> Iterable[TraceEvent]:
        pass


class EIP3155EventsParser(EventsParser):
    @override
    def parse(self, lines: Iterable[str]) -> Iterable[TraceEvent]:
        return parse_events_eip3155(lines)


class StructLogEventsParser(EventsParser):
    @override
    def parse(self, lines: Iterable[str]) -> Iterable[TraceEvent]:
        json_str = "".join(lines)
        return parse_events_struct_logs(json.loads(json_str)["structLogs"])
