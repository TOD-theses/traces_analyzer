from itertools import zip_longest
from traces_analyzer.analysis.analyzer import AnalysisStepDoubleTrace
from traces_analyzer.analysis.tod_source_analyzer import TODSourceAnalyzer
from traces_analyzer.preprocessing.instructions import POP, PUSH0, SLOAD
from traces_analyzer.preprocessing.instructions_parser import parse_instructions
from traces_analyzer.preprocessing.events_parser import TraceEvent, parse_events


def test_tod_source_analyzer_with_traces(sample_traces_path):
    trace_normal_path = (
        sample_traces_path
        / "62a8b9ece30161692b68cbb5"
        / "trace_normal"
        / "0x5bc779188a1a4f701c33980a97e902fc097dc48393a01c61f363fce09f33e4a0.jsonl"
    )
    trace_attack_path = (
        sample_traces_path
        / "62a8b9ece30161692b68cbb5"
        / "trace_attack"
        / "0x5bc779188a1a4f701c33980a97e902fc097dc48393a01c61f363fce09f33e4a0.jsonl"
    )

    with open(trace_normal_path) as trace_normal_file, open(trace_attack_path) as trace_attack_file:
        trace_normal_events = list(parse_events(trace_normal_file))
        trace_attack_events = list(parse_events(trace_attack_file))

        instructions_normal = list(parse_instructions(trace_normal_events))
        instructions_attack = list(parse_instructions(trace_attack_events))

        analyzer = TODSourceAnalyzer()

        for instr_a, instr_b, event_a, event_b in zip_longest(
            instructions_normal,
            instructions_attack,
            trace_normal_events,
            trace_attack_events,
        ):
            analyzer.on_analysis_step(
                AnalysisStepDoubleTrace(
                    trace_event_one=event_a,
                    trace_event_two=event_b,
                    instruction_one=instr_a,
                    instruction_two=instr_b,
                )
            )

        tod_source = analyzer.get_tod_source()
        assert tod_source.found

        tod_source_first = tod_source.instruction_one
        tod_source_second = tod_source.instruction_two

        # instructions should be equal, except for the outcome
        assert tod_source_first and tod_source_second
        assert isinstance(tod_source_first, SLOAD) and isinstance(tod_source_second, SLOAD)
        assert tod_source_first.opcode == tod_source_second.opcode == SLOAD.opcode
        assert tod_source_first.program_counter == tod_source_second.program_counter == 2401
        assert (
            tod_source_first.call_frame.code_address
            == tod_source_second.call_frame.code_address
            == "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
        )
        assert (
            tod_source_first.key
            == tod_source_second.key
            == "0x5e950c03214daf5e318e3c0401e87e5c3b14177b9a9993d2e5f6176bb0f752a"
        )

        # output of SLOAD is different, depending on the contracts storage
        assert tod_source_first.result == "0x64fdf635bcd1c5108c9"
        assert tod_source_second.result == "0x64e25040f3af9826109"


def test_tod_source_analyzer():

    common_trace_events = [
        TraceEvent(0x1, PUSH0.opcode, [], 1, []),
        TraceEvent(0x2, SLOAD.opcode, ["0x0"], 1, []),
    ]

    trace_events_one = common_trace_events + [TraceEvent(0x3, POP.opcode, ["0x1234"], 1, [])]
    trace_events_two = common_trace_events + [TraceEvent(0x3, POP.opcode, ["0x5678"], 1, [])]
    instructions_one = parse_instructions(trace_events_one)
    instructions_two = parse_instructions(trace_events_two)

    analyzer = TODSourceAnalyzer()

    for instruction_one, instruction_two, event_one, event_two in zip_longest(
        instructions_one, instructions_two, trace_events_one, trace_events_two
    ):
        analyzer.on_analysis_step(AnalysisStepDoubleTrace(event_one, instruction_one, event_two, instruction_two))

    tod_source = analyzer.get_tod_source()

    assert tod_source.found

    assert tod_source.instruction_one.program_counter == 0x2
    assert tod_source.instruction_one.opcode == SLOAD.opcode
    assert tod_source.instruction_one.stack_outputs == ("0x1234",)

    assert tod_source.instruction_two.program_counter == 0x2
    assert tod_source.instruction_two.opcode == SLOAD.opcode
    assert tod_source.instruction_two.stack_outputs == ("0x5678",)
