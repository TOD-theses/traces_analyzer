from dataclasses import dataclass
from enum import Enum

from typing_extensions import Self


class HaltType(Enum):
    NORMAL = "normal"
    EXCEPTIONAL = "exceptional"


@dataclass
class CallFrame:
    parent: Self | None
    calldata: str
    depth: int
    msg_sender: str
    code_address: str
    storage_address: str
    reverted: bool = False
    halt_type: HaltType | None = None
