from dataclasses import dataclass

from typing_extensions import Self


@dataclass
class CallFrame:
    parent: Self | None
    depth: int
    msg_sender: str
    code_address: str
    storage_address: str
