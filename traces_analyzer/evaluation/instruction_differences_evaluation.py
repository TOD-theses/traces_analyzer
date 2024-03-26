from dataclasses import asdict

from typing_extensions import override

from traces_analyzer.analysis.instruction_input_analyzer import InstructionExecution, InstructionInputChange
from traces_analyzer.evaluation.evaluation import Evaluation
from traces_analyzer.preprocessing.instructions import CALL, STATICCALL


class InstructionDifferencesEvaluation(Evaluation):
    _type_key = "instruction_differences"
    _type_name = "Instruction differences"
    _CLI_REPORTED_OPCODES = [CALL.opcode, STATICCALL.opcode]

    def __init__(
        self,
        occurrence_changes: tuple[list[InstructionExecution], list[InstructionExecution]],
        input_changes: list[InstructionInputChange],
    ):
        super().__init__()
        self._only_first = occurrence_changes[0]
        self._only_second = occurrence_changes[1]
        self._input_changes = input_changes

    @override
    def _dict_report(self) -> dict:
        return {
            "input_changes": [instruction_input_change_to_dict(c) for c in self._input_changes],
            "occurrence_changes": {
                "only_in_first_trace": [occurence_change_to_dict(c) for c in self._only_first],
                "only_in_second_trace": [occurence_change_to_dict(c) for c in self._only_second],
            },
        }

    @override
    def _cli_report(self) -> str:
        relevant_input_changes = [c for c in self._input_changes if c.opcode in self._CLI_REPORTED_OPCODES]
        relevant_only_first = [c for c in self._only_first if c.opcode in self._CLI_REPORTED_OPCODES]
        relevant_only_second = [c for c in self._only_second if c.opcode in self._CLI_REPORTED_OPCODES]

        relevant_opcodes_note = "NOTE: for clarity the CLI only reports following opcodes:" + ",".join(
            [hex(op).upper() for op in self._CLI_REPORTED_OPCODES]
        )

        input_changes_report = self._cli_report_input_changes(relevant_input_changes)
        only_first_report = self._cli_report_occurrence_changes(relevant_only_first)
        only_second_report = self._cli_report_occurrence_changes(relevant_only_second)

        return (
            f"{relevant_opcodes_note}\n\n"
            f"Instructions with changed inputs: {len(relevant_input_changes)}\n\n"
            f"{input_changes_report}\n"
            f"Instructions only executed in the first trace: {len(relevant_only_first)}\n"
            f"{only_first_report}\n"
            f"Instructions only executed in the second trace: {len(relevant_only_second)}\n"
            f"{only_second_report}\n"
        )

    def _cli_report_input_changes(self, changes: list[InstructionInputChange]) -> str:
        result = ""
        for change in changes:
            result += (
                "Instruction:\n"
                f"> opcode: {hex(change.opcode)}\n"
                "Location:\n"
                f"> address: {change.address}\n"
                f"> pc: {change.program_counter}\n"
                "Change:\n"
            )
            if change.memory_input_change:
                result += f'> memory: "{change.first_memory_input}" vs "{change.second_memory_input}"\n'
            if change.stack_input_changes:
                result += "> stack: " + str(change.stack_input_changes) + "\n"
        return result

    def _cli_report_occurrence_changes(self, changes: list[InstructionExecution]) -> str:
        result = ""
        for change in changes:
            result += (
                "Instruction:\n"
                f"> opcode: {hex(change.opcode)}\n"
                "Location:\n"
                f"> address: {change.address}\n"
                f"> pc: {change.program_counter}\n"
            )
        return result


def occurence_change_to_dict(occurrence_change: InstructionExecution) -> dict:
    return {
        "location": {
            "address": occurrence_change.address,
            "pc": occurrence_change.program_counter,
        },
        "instruction": {
            "opcode": occurrence_change.opcode,
            "stack_inputs": occurrence_change.stack_inputs,
        },
    }


def instruction_input_change_to_dict(input_change: InstructionInputChange) -> dict:
    return {
        "location": {
            "address": input_change.address,
            "pc": input_change.program_counter,
        },
        "instruction": {
            "opcode": input_change.opcode,
        },
        "inputs": [
            {"stack": input_change.first_stack_input, "memory": input_change.first_memory_input},
            {"stack": input_change.second_stack_input, "memory": input_change.second_memory_input},
        ],
        "stack_input_changes": [asdict(change) for change in input_change.stack_input_changes],
        "memory_input_change": asdict(input_change.memory_input_change) if input_change.memory_input_change else None,
    }
