from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

from typing_extensions import Self

if TYPE_CHECKING:
    from traces_analyzer.parser.instructions.instructions import CREATE, CREATE2, CallInstruction


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
    initiating_instruction: CallInstruction | CREATE | CREATE2 | None = field(default=None, compare=False, hash=False)
    return_data: str | None = None
    reverted: bool = False
    halt_type: HaltType | None = None
    is_contract_initialization: bool = False
