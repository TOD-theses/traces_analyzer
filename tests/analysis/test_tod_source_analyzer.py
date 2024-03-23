from itertools import zip_longest
from traces_analyzer.analysis.analyzer import AnalysisStepDoubleTrace
from traces_analyzer.analysis.tod_source_analyzer import TODSourceAnalyzer
from traces_analyzer.instructions import SLOAD
from traces_analyzer.parser import parse_events
from traces_analyzer.trace_reader import read_trace_file


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
        trace_normal_events = list(read_trace_file(trace_normal_file))
        trace_attack_events = list(read_trace_file(trace_attack_file))

        instructions_normal = list(parse_events(trace_normal_events))
        instructions_attack = list(parse_events(trace_attack_events))

        analyzer = TODSourceAnalyzer()

        # for both traces, take current instructions, and current+next trace events
        for instr_a, instr_b, events_a, events_b in zip_longest(
            instructions_normal,
            instructions_attack,
            zip_longest(trace_normal_events, trace_normal_events[1:]),
            zip_longest(trace_attack_events, trace_attack_events[1:]),
        ):
            analyzer.on_analysis_step(
                AnalysisStepDoubleTrace(
                    trace_events_one=events_a,
                    trace_events_two=events_b,
                    instruction_one=instr_a,
                    instruction_two=instr_b,
                )
            )

        tod_source_first, tod_source_second = analyzer.get_tod_source()

        # instructions should be equal, except for the outcome
        assert tod_source_first and tod_source_second
        assert isinstance(tod_source_first, SLOAD) and isinstance(tod_source_second, SLOAD)
        assert tod_source_first.opcode == tod_source_second.opcode == SLOAD.opcode
        assert tod_source_first.program_counter == tod_source_second.program_counter == 2401
        assert (
            tod_source_first.call_frame.address
            == tod_source_second.call_frame.address
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
