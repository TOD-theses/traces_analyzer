import json
from pathlib import Path
from typing import Iterable

from traces_analyzer.loader.loader import TraceBundle, TraceLoader, TransactionBundle
from traces_analyzer.utils.hexstring import HexString


class DirectoryLoader(TraceLoader):
    METADATA_FILENAME = "metadata.json"

    def __init__(self, dir: Path) -> None:
        super().__init__()
        self._dir = dir

    def load(self) -> TraceBundle:
        with open(self._dir / self.METADATA_FILENAME) as metadata_file:
            metadata = json.load(metadata_file)

            id = metadata["id"]
            traces_actual = metadata["transaction_replays"]["actual"]["transactions"]
            traces_reverse = metadata["transaction_replays"]["reverse"]["transactions"]
            return self._load_trace_bundle(id, traces_actual, traces_reverse)

    def _load_trace_bundle(self, id: str, traces_actual: list[dict], traces_reverse: list[dict]) -> TraceBundle:
        return TraceBundle(
            id=id,
            tx_attack=self._load_transaction_bundle(traces_actual[0], traces_reverse[1]),
            tx_victim=self._load_transaction_bundle(traces_actual[1], traces_reverse[0]),
        )

    def _load_transaction_bundle(self, tx_actual: dict, tx_reverse: dict) -> TransactionBundle:
        assert (
            tx_actual["hash"] == tx_reverse["hash"]
        ), f"Tried to compare traces with different transaction hashes: {tx_actual['hash']} {tx_reverse['hash']}"
        hash = HexString(tx_actual["hash"])

        return TransactionBundle(
            hash=hash,
            caller=HexString(tx_actual["from"]),
            to=HexString(tx_actual["to"]),
            # TODO: remove get when it is implemented in the metadata
            calldata=HexString(tx_actual.get("calldata", "")),
            trace_actual=lazy_load_file(self._dir / "actual" / (hash.with_prefix() + ".jsonl")),
            trace_reverse=lazy_load_file(self._dir / "reverse" / (hash.with_prefix() + ".jsonl")),
        )


# TODO: implement a cleaner solution (maybe making the class closable?)
# I think this does not close except if everything in the file was read
# Hence, it does not close on errors
def lazy_load_file(path: Path) -> Iterable[str]:
    with open(path) as file:
        for line in file:
            yield line
