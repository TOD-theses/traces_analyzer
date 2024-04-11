from typing_extensions import override

from traces_analyzer.evaluation.evaluation import Evaluation
from traces_analyzer.features.extractors.tod_source import TODSource


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
                    "address": self._tod_source.instruction_one.call_context.code_address,
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
        instr_one, instr_two = self._tod_source.instruction_one, self._tod_source.instruction_two

        return (
            f"{instr_one.name} at {instr_one.call_context.code_address}:{instr_one.program_counter}\n"
            f"> output first trace:   {instr_one.stack_outputs} | {instr_one.memory_output}\n"
            f"> output second trace:  {instr_two.stack_outputs} | {instr_two.memory_output}"
        )
