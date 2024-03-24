"""CLI interface for traces_analyzer project."""

import json
import sys
import time
from pathlib import Path
from typing import Iterable

from traces_analyzer.analysis.analysis_runner import AnalysisRunner, RunInfo
from traces_analyzer.analysis.instruction_input_analyzer import InstructionInputAnalyzer
from traces_analyzer.analysis.tod_source_analyzer import TODSourceAnalyzer
from traces_analyzer.evaluation.evaluation import Evaluation
from traces_analyzer.evaluation.instruction_differences_evaluation import InstructionDifferencesEvaluation
from traces_analyzer.evaluation.tod_source_evaluation import TODSourceEvaluation
from traces_analyzer.loader.directory_loader import DirectoryLoader


def main():  # pragma: no cover
    if not len(sys.argv) > 1:
        print("Please provide the directory path")
        quit()

    directory_path = Path(sys.argv[1]).resolve()
    out_dir = Path("out")
    out_dir.mkdir(exist_ok=True)

    analyze_transactions_in_dir(directory_path, out_dir)


def analyze_transactions_in_dir(dir: Path, out_dir):
    bundle = DirectoryLoader(dir).load()

    compare_traces(bundle.tx_victim.hash, (bundle.tx_victim.trace_one, bundle.tx_victim.trace_two), out_dir)
    compare_traces(bundle.tx_attack.hash, (bundle.tx_attack.trace_one, bundle.tx_attack.trace_two), out_dir)


def compare_traces(tx_hash: str, traces: tuple[Iterable[str], Iterable[str]], out_dir: Path):
    print(f"Comparing traces for {tx_hash}")

    tod_source_analyzer = TODSourceAnalyzer()
    instruction_changes_analyzer = InstructionInputAnalyzer()

    start = time.time()
    runner = AnalysisRunner(
        RunInfo(
            analyzers=[tod_source_analyzer, instruction_changes_analyzer],
            traces_jsons=traces,
        )
    )
    runner.run()

    print(f"Finished analysis in {int((time.time() - start) * 1000)}ms")

    print("Results:\n")

    evaluations: list[Evaluation] = [
        TODSourceEvaluation(tod_source_analyzer.get_tod_source()),
        InstructionDifferencesEvaluation(
            occurrence_changes=instruction_changes_analyzer.get_instructions_only_executed_by_one_trace(),
            input_changes=instruction_changes_analyzer.get_instructions_with_different_inputs(),
        ),
    ]

    reports = {}

    for evaluation in evaluations:
        print(evaluation.cli_report())
        dict_report = evaluation.dict_report()
        reports[dict_report["evaluation_type"]] = dict_report["report"]
    out_file_path = out_dir / (tx_hash + ".json")
    out_file_path.write_text(json.dumps(reports, indent=2))
    print(f"Saved report to {out_file_path}")
