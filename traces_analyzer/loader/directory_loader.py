import json
from pathlib import Path
from typing import Iterable

from traces_analyzer.loader.loader import TraceBundle, TraceLoader, TransactionBundle


class DirectoryLoader(TraceLoader):
    METADATA_FILENAME = "metadata.json"

    def __init__(self, dir: Path) -> None:
        super().__init__()
        self._dir = dir

    def load(self) -> TraceBundle:
        with open(self._dir / self.METADATA_FILENAME) as metadata_file:
            metadata = json.load(metadata_file)

            tx_one = metadata["transactions"][0]
            tx_two = metadata["transactions"][1]
            directories = metadata["directories"]["actual"], metadata["directories"]["reverse"]

            return TraceBundle(
                id=metadata["id"],
                tx_victim=self._load_transaction_bundle(tx_one, directories),
                tx_attack=self._load_transaction_bundle(tx_two, directories),
            )

    def _load_transaction_bundle(self, tx: dict, directories: tuple[str, str]) -> TransactionBundle:
        hash = tx["hash"]
        trace_actual_path = self._dir / directories[0] / (hash + ".jsonl")
        trace_reverse_path = self._dir / directories[1] / (hash + ".jsonl")

        return TransactionBundle(
            caller=tx["from"],
            to=tx["to"],
            hash=tx["hash"],
            trace_one=lazy_load_file(trace_actual_path),
            trace_two=lazy_load_file(trace_reverse_path),
        )


# TODO: implement a cleaner solution (maybe making the class closable?)
# I think this does not close except if everything in the file was read
# Hence, it does not close on errors
def lazy_load_file(path: str) -> Iterable[str]:
    with open(path) as file:
        for line in file:
            yield line
