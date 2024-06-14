"""CLI interface for traces_analyzer project."""

import json
from argparse import ArgumentParser, BooleanOptionalAction
from pathlib import Path
from typing import Iterable

from networkx import ancestors
from tqdm import tqdm

from traces_analyzer.evaluation.evaluation import Evaluation
from traces_analyzer.evaluation.instruction_differences_evaluation import (
    InstructionDifferencesEvaluation,
)
from traces_analyzer.evaluation.instruction_usage_evaluation import (
    InstructionUsageEvaluation,
)
from traces_analyzer.evaluation.tod_source_evaluation import TODSourceEvaluation
from traces_analyzer.features.extractors.instruction_differences import (
    InstructionDifferencesFeatureExtractor,
)
from traces_analyzer.features.extractors.instruction_usages import (
    InstructionUsagesFeatureExtractor,
)
from traces_analyzer.features.extractors.tod_source import TODSourceFeatureExtractor
from traces_analyzer.features.feature_extraction_runner import (
    FeatureExtractionRunner,
    RunInfo,
)
from traces_analyzer.features.feature_extractor import (
    SingleToDoubleInstructionFeatureExtractor,
)
from traces_analyzer.loader.directory_loader import DirectoryLoader
from traces_analyzer.loader.loader import PotentialAttack
from traces_parser.parser.environment.call_context import CallContext
from traces_parser.parser.events_parser import parse_events
from traces_parser.parser.information_flow.information_flow_graph import (
    build_information_flow_graph,
)
from traces_parser.parser.instructions.instructions import (
    CALL,
    LOG0,
    LOG1,
    LOG2,
    LOG3,
    STATICCALL,
)
from traces_parser.parser.instructions_parser import (
    TransactionParsingInfo,
    parse_transaction,
)
from traces_parser.datatypes import HexString
from traces_analyzer.utils.signatures.signature_registry import SignatureRegistry


def main():  # pragma: no cover
    parser = ArgumentParser(description="Analyze bundles of transaction traces")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("out"),
        help="The directory where the reports should be saved",
    )
    parser.add_argument(
        "--bundles",
        type=Path,
        nargs="+",
        required=True,
        help="The directory path(s) that contain a metadata.json that describes what should be analyzed",
    )
    parser.add_argument("--verbose", action=BooleanOptionalAction, required=False)

    args = parser.parse_args()

    out = args.out
    bundles = args.bundles
    verbose = bool(args.verbose)

    out.mkdir(exist_ok=True)

    for path in (bar := tqdm(bundles, dynamic_ncols=True)):
        with DirectoryLoader(path) as bundle:
            bar.set_postfix_str(bundle.id)
            analyze_transactions_in_dir(bundle, out, verbose)


def analyze_transactions_in_dir(bundle: PotentialAttack, out_dir: Path, verbose: bool):
    evaluations_victim = compare_traces(
        bundle.tx_victim.hash,
        bundle.tx_victim.caller,
        bundle.tx_victim.to,
        bundle.tx_victim.calldata,
        bundle.tx_victim.value,
        (bundle.tx_victim.trace_actual, bundle.tx_victim.trace_reverse),
        verbose,
    )

    save_evaluations(
        evaluations_victim, out_dir / f"{bundle.id}_{bundle.tx_victim.hash}.json"
    )

    if verbose:
        print(f"Transaction: {bundle.tx_victim.hash}")
        for evaluation in evaluations_victim:
            print(evaluation.cli_report())


def compare_traces(
    hash: HexString,
    sender: HexString,
    to: HexString,
    calldata: HexString,
    value: HexString,
    traces: tuple[Iterable[str], Iterable[str]],
    verbose: bool,
) -> list[Evaluation]:
    tod_source_analyzer = TODSourceFeatureExtractor()
    instruction_changes_analyzer = InstructionDifferencesFeatureExtractor()
    instruction_usage_analyzers = SingleToDoubleInstructionFeatureExtractor(
        InstructionUsagesFeatureExtractor(), InstructionUsagesFeatureExtractor()
    )

    transaction_one = parse_transaction(
        TransactionParsingInfo(sender, to, calldata, value), parse_events(traces[0])
    )
    transaction_two = parse_transaction(
        TransactionParsingInfo(sender, to, calldata, value), parse_events(traces[1])
    )

    runner = FeatureExtractionRunner(
        RunInfo(
            feature_extractors=[
                tod_source_analyzer,
                instruction_changes_analyzer,
                instruction_usage_analyzers,
            ],
            transactions=(transaction_one, transaction_two),
        )
    )
    runner.run()

    information_flow_graph_one = build_information_flow_graph(
        transaction_one.instructions
    )
    information_flow_graph_two = build_information_flow_graph(
        transaction_two.instructions
    )

    if verbose:
        call_tree_normal, call_tree_reverse = runner.get_call_trees()
        print(f"Transaction: {hash}")
        print("Call tree actual")
        print(call_tree_normal)
        print("Call tree reverse")
        print(call_tree_reverse)

        print("Source to Sink")
        print()
        all_instructions = transaction_one.instructions
        tod_source_instruction = tod_source_analyzer.get_tod_source().instruction_one
        changed_instructions = (
            instruction_changes_analyzer.get_instructions_with_different_inputs()
        )
        # only memory input changes for CALL/LOGs
        potential_sinks = [
            i
            for i in changed_instructions
            if i.opcode
            in [CALL.opcode, LOG0.opcode, LOG1.opcode, LOG2.opcode, LOG3.opcode]
            and i.memory_input_change
        ]
        potential_sink_instructions = [
            change.instruction_one for change in potential_sinks
        ]

        tod_source_instruction_index = all_instructions.index(tod_source_instruction)
        potential_sink_instruction_indexes = [
            all_instructions.index(instr) for instr in potential_sink_instructions
        ]
        sink_instruction_index = min(potential_sink_instruction_indexes)
        sink_instruction = all_instructions[sink_instruction_index]

        print(information_flow_graph_one)
        print(information_flow_graph_two)
        print(list(ancestors(information_flow_graph_one, sink_instruction.step_index)))

        source_to_sink_contexts: list[CallContext] = []

        # NOTE: call contexts will go up and down and repeat themselves
        for instr in all_instructions[
            tod_source_instruction_index : sink_instruction_index + 1
        ]:
            if (
                not source_to_sink_contexts
                or instr.call_context is not source_to_sink_contexts[-1]
            ):
                source_to_sink_contexts.append(instr.call_context)

        """
        TODO:
        - the source instruction is not necessarily related to the sink
            -> should display all source instructions and the human can match it
        - with information flow analysis, we could check which instruction is responsible for the change.
            However, this would need to include stack, memory, tcache, calldata, returndata, and storage writes+reads
        """
        signature_lookup = SignatureRegistry("http://localhost:8000")
        min_depth = min(context.depth for context in source_to_sink_contexts)
        source_indent = "  " * (tod_source_instruction.call_context.depth - min_depth)
        sink_indent = "  " * (sink_instruction.call_context.depth - min_depth)
        print(f"{source_indent}> {tod_source_instruction}")
        for context in source_to_sink_contexts:
            # print(context)
            signature = (
                signature_lookup.lookup_by_hex(context.calldata[:8].get_hexstring())
                or context.calldata[:8]
            )
            indent = "  " * (context.depth - min_depth)
            print(f"{indent}> {context.code_address}.{signature}")
        print(f"{sink_indent}> {sink_instruction}")

    evaluations: list[Evaluation] = [
        TODSourceEvaluation(tod_source_analyzer.get_tod_source()),
        InstructionDifferencesEvaluation(
            occurrence_changes=instruction_changes_analyzer.get_instructions_only_executed_by_one_trace(),
            input_changes=instruction_changes_analyzer.get_instructions_with_different_inputs(),
        ),
        InstructionUsageEvaluation(
            instruction_usage_analyzers.one.get_used_opcodes_per_contract(),
            instruction_usage_analyzers.two.get_used_opcodes_per_contract(),
            filter_opcodes=[CALL.opcode, STATICCALL.opcode],
        ),
    ]

    return evaluations


def save_evaluations(evaluations: list[Evaluation], path: Path):
    reports = {}

    for evaluation in evaluations:
        dict_report = evaluation.dict_report()
        reports[dict_report["evaluation_type"]] = dict_report["report"]

    path.write_text(json.dumps(reports, indent=2))
