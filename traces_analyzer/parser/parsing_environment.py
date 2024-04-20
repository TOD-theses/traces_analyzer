from dataclasses import dataclass
from typing import Sequence

from traces_analyzer.parser.call_context import CallContext


@dataclass
class ParsingEnvironment:
    current_call_context: CallContext
    current_stack: Sequence[str] = ()
    current_memory: str | None = None
    current_step_index = 0
