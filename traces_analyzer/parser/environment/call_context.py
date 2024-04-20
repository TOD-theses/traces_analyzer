from dataclasses import dataclass, field
from enum import Enum

from typing_extensions import Self


class HaltType(Enum):
    NORMAL = "normal"
    EXCEPTIONAL = "exceptional"


@dataclass
class CallContext:
    parent: Self | None = field(repr=False)
    calldata: str
    depth: int
    msg_sender: str
    code_address: str
    storage_address: str
    reverted: bool = False
    halt_type: HaltType | None = None
    is_contract_initialization: bool = False
