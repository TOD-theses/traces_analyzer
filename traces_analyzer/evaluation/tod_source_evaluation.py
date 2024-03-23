from typing_extensions import override

from traces_analyzer.analysis.tod_source_analyzer import TODSource
from traces_analyzer.evaluation.evaluation import Evaluation


class TODSourceEvaluation(Evaluation):
    _type_key = "tod_source"
    _type_name = "TOD source"

    def __init__(self, tod_source: TODSource):
        super().__init__()
        self._tod_source = tod_source

    @override
    def _dict_report(self) -> dict:
        source = None

        if self._tod_source.found:
            source = {
                "location": {
                    "address": self._tod_source.instruction_one.call_frame.address,
                    "pc": self._tod_source.instruction_one.program_counter,
                },
                "instruction": {
                    "opcode": self._tod_source.instruction_one.opcode,
                },
            }

        return {
            "found": self._tod_source.found,
            "source": source,
        }

    @override
    def _cli_report(self) -> str:
        if not self._tod_source.found:
            return "TOD source not found."
        return (
            "Instruction\n"
            f"> opcode: {hex(self._tod_source.instruction_one.opcode)}\n"
            "\n"
            "Location: \n"
            f"> address: {self._tod_source.instruction_one.call_frame.address}\n"
            f"> pc: {self._tod_source.instruction_one.program_counter}\n"
        )
