from typing_extensions import override

from traces_analyzer.evaluation.evaluation import Evaluation
from traces_analyzer.features.extractors.tod_source import TODSource
from traces_parser.parser.instructions.instruction import Instruction
from traces_parser.datatypes import HexString


class TODSourceEvaluation(Evaluation):
    @property
    @override
    def _type_key(self):
        return "tod_source"

    @property
    @override
    def _type_name(self):
        return "TOD source"

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
        instr_one, instr_two = (
            self._tod_source.instruction_one,
            self._tod_source.instruction_two,
        )

        return (
            f"{instr_one.name} at {instr_one.call_context.code_address}:{instr_one.program_counter}\n"
            f"> output first trace:   {prepare_stack_output(instr_one)} | {prepare_mem_output(instr_one)}\n"
            f"> output second trace:  {prepare_stack_output(instr_two)} | {prepare_mem_output(instr_two)}"
        )


def prepare_stack_output(instr: Instruction) -> tuple[HexString, ...]:
    return tuple(x.value.get_hexstring() for x in instr.get_accesses().stack)


def prepare_mem_output(instr: Instruction) -> HexString | None:
    mem_writes = instr.get_writes().memory
    if mem_writes:
        return mem_writes[0].value.get_hexstring()
    return None
