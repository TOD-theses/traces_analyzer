"""CLI interface for traces_analyzer project."""

import json
from argparse import ArgumentParser, BooleanOptionalAction
from pathlib import Path
from typing import Iterable

from tqdm import tqdm

from traces_analyzer.analysis.analysis_runner import AnalysisRunner, RunInfo
from traces_analyzer.analysis.analyzer import SingleToDoubleInstructionAnalyzer
from traces_analyzer.analysis.instruction_input_analyzer import InstructionInputAnalyzer
from traces_analyzer.analysis.instruction_usage_analyzer import InstructionUsageAnalyzer
from traces_analyzer.analysis.tod_source_analyzer import TODSourceAnalyzer
from traces_analyzer.evaluation.evaluation import Evaluation
from traces_analyzer.evaluation.instruction_differences_evaluation import InstructionDifferencesEvaluation
from traces_analyzer.evaluation.instruction_usage_evaluation import InstructionUsageEvaluation
from traces_analyzer.evaluation.tod_source_evaluation import TODSourceEvaluation
from traces_analyzer.loader.directory_loader import DirectoryLoader
from traces_analyzer.loader.loader import TraceBundle
from traces_analyzer.preprocessing.instructions import CALL, STATICCALL, op_from_class


def main():  # pragma: no cover
    parser = ArgumentParser(description="Analyze bundles of transaction traces")
    parser.add_argument("--out", type=Path, default=Path("out"), help="The directory where the reports should be saved")
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
        bundle = DirectoryLoader(path).load()
        bar.set_postfix_str(bundle.id)
        analyze_transactions_in_dir(bundle, out, verbose)


def analyze_transactions_in_dir(bundle: TraceBundle, out_dir: Path, print_evaluations: bool):
    evaluations_victim = compare_traces(
        bundle.tx_victim.caller,
        bundle.tx_victim.to,
        bundle.tx_victim.calldata,
        (bundle.tx_victim.trace_actual, bundle.tx_victim.trace_reverse),
        print_evaluations,
    )
    evaluations_attacker = compare_traces(
        bundle.tx_attack.caller,
        bundle.tx_attack.to,
        bundle.tx_attack.calldata,
        (bundle.tx_attack.trace_actual, bundle.tx_attack.trace_reverse),
        print_evaluations,
    )

    save_evaluations(evaluations_victim, out_dir / f"{bundle.id}_{bundle.tx_victim.hash}.json")
    save_evaluations(evaluations_attacker, out_dir / f"{bundle.id}_{bundle.tx_attack.hash}.json")

    if print_evaluations:
        for evaluation in evaluations_victim:
            print(evaluation.cli_report())
        for evaluation in evaluations_attacker:
            print(evaluation.cli_report())


def compare_traces(
    sender: str,
    to: str,
    calldata: str,
    traces: tuple[Iterable[str], Iterable[str]],
    print_call_trees: bool,
) -> list[Evaluation]:
    tod_source_analyzer = TODSourceAnalyzer()
    instruction_changes_analyzer = InstructionInputAnalyzer()
    instruction_usage_analyzers = SingleToDoubleInstructionAnalyzer(
        InstructionUsageAnalyzer(), InstructionUsageAnalyzer()
    )

    runner = AnalysisRunner(
        RunInfo(
            analyzers=[tod_source_analyzer, instruction_changes_analyzer, instruction_usage_analyzers],
            traces_jsons=traces,
            sender=sender,
            to=to,
            calldata=calldata,
        )
    )
    runner.run()

    if print_call_trees:
        call_tree_normal, call_tree_reverse = runner.get_call_trees()
        print("Call tree actual")
        print(call_tree_normal)
        print("Call tree reverse")
        print(call_tree_reverse)

    evaluations: list[Evaluation] = [
        TODSourceEvaluation(tod_source_analyzer.get_tod_source()),
        InstructionDifferencesEvaluation(
            occurrence_changes=instruction_changes_analyzer.get_instructions_only_executed_by_one_trace(),
            input_changes=instruction_changes_analyzer.get_instructions_with_different_inputs(),
        ),
        InstructionUsageEvaluation(
            instruction_usage_analyzers.one.get_used_opcodes_per_contract(),
            instruction_usage_analyzers.two.get_used_opcodes_per_contract(),
            filter_opcodes=[op_from_class(CALL), op_from_class(STATICCALL)],
        ),
    ]

    return evaluations


def save_evaluations(evaluations: list[Evaluation], path: Path):
    reports = {}

    for evaluation in evaluations:
        dict_report = evaluation.dict_report()
        reports[dict_report["evaluation_type"]] = dict_report["report"]

    path.write_text(json.dumps(reports, indent=2))
