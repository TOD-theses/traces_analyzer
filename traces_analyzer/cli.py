"""CLI interface for traces_analyzer project."""

import sys
import time
from pathlib import Path
from typing import Iterable

from traces_analyzer.analysis.analysis_runner import AnalysisRunner, RunInfo
from traces_analyzer.analysis.tod_source_analyzer import TODSourceAnalyzer
from traces_analyzer.evaluation.evaluation import Evaluation
from traces_analyzer.evaluation.tod_source_evaluation import TODSourceEvaluation
from traces_analyzer.loader.directory_loader import DirectoryLoader


def main():  # pragma: no cover
    if not len(sys.argv) > 1:
        print("Please provide the directory path")
        quit()

    directory_path = Path(sys.argv[1]).resolve()

    analyze_transactions_in_dir(directory_path)


def analyze_transactions_in_dir(dir: Path):
    bundle = DirectoryLoader(dir).load()

    compare_traces(bundle.tx_victim.hash, (bundle.tx_victim.trace_one, bundle.tx_victim.trace_two))
    compare_traces(bundle.tx_attack.hash, (bundle.tx_attack.trace_one, bundle.tx_attack.trace_two))


def compare_traces(tx_hash: str, traces: tuple[Iterable[str], Iterable[str]]):
    print(f"Comparing traces for {tx_hash}")

    tod_source_analyzer = TODSourceAnalyzer()

    start = time.time()
    runner = AnalysisRunner(
        RunInfo(
            analyzers=[tod_source_analyzer],
            traces_jsons=traces,
        )
    )
    runner.run()

    print(f"Finished analysis in {int((time.time() - start) * 1000)}ms")

    print("Results:\n")

    evaluations: list[Evaluation] = [TODSourceEvaluation(tod_source_analyzer.get_tod_source())]

    for evaluation in evaluations:
        print(evaluation.cli_report())
