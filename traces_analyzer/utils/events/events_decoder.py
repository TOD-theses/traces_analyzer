from typing import Sequence

from traces_parser.datatypes.hexstring import HexString

from traces_analyzer.utils.events.event import Event


class EventDecodingException(Exception):
    pass


class EventsDecoder:
    def __init__(self, events: Sequence[type[Event]]) -> None:
        self._events = events

    def decode_event(
        self, topics: Sequence[HexString], data: HexString, storage_address: HexString
    ):
        if not topics:
            raise EventDecodingException("Can not decode event without any topic")
        for event in self._events:
            if event.can_decode(topics, data):
                return event.decode(topics, data, storage_address)
