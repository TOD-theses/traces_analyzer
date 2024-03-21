from abc import ABC, abstractmethod
from dataclasses import dataclass

from traces_analyzer.call_frame import CallFrame
from traces_analyzer.trace_reader import TraceEvent


@dataclass
class Instruction(ABC):
    op: int

    @staticmethod
    @abstractmethod
    def from_event(event: TraceEvent, next_event: TraceEvent, call_frame: CallFrame):
        pass


@dataclass
class Unknown(Instruction):
    @staticmethod
    def from_event(event: TraceEvent, next_event: TraceEvent, call_frame: CallFrame):
        return Unknown(op=event.op)


@dataclass
class CALL(Instruction):
    gas: str
    address: str
    value: str
    argsOffset: str
    argsSize: str
    retOffset: str
    retSize: str
    op = 0xF1

    @staticmethod
    def from_event(event: TraceEvent, next_event: TraceEvent, call_frame: CallFrame):
        stack = event.stack

        return CALL(
            op=CALL.op,
            gas=stack[-1],
            address=stack[-2],
            value=stack[-3],
            argsOffset=stack[-4],
            argsSize=stack[-5],
            retOffset=stack[-6],
            retSize=stack[-7],
        )


@dataclass
class STATICCALL(Instruction):
    gas: str
    address: str
    argsOffset: str
    argsSize: str
    retOffset: str
    retSize: str
    op = 0xFA

    @staticmethod
    def from_event(event: TraceEvent, next_event: TraceEvent, call_frame: CallFrame):
        stack = event.stack

        return STATICCALL(
            op=STATICCALL.op,
            gas=stack[-1],
            address=stack[-2],
            argsOffset=stack[-3],
            argsSize=stack[-4],
            retOffset=stack[-5],
            retSize=stack[-6],
        )


@dataclass
class STOP(Instruction):
    op = 0x0

    @staticmethod
    def from_event(event: TraceEvent, next_event: TraceEvent, call_frame: CallFrame):
        return STOP(op=STOP.op)


@dataclass
class RETURN(Instruction):
    op = 0xF3

    @staticmethod
    def from_event(event: TraceEvent, next_event: TraceEvent, call_frame: CallFrame):
        return RETURN(op=RETURN.op)


@dataclass
class SLOAD(Instruction):
    key: str
    result: str | None
    op = 0x54

    @staticmethod
    def from_event(event: TraceEvent, next_event: TraceEvent, call_frame: CallFrame):
        return SLOAD(
            op=SLOAD.op,
            key=event.stack[-1],
            result=next_event.stack[-1],
        )
