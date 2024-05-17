import json
from pathlib import Path
from typing import Iterable

from traces_analyzer.loader.loader import PotentialAttack, TraceLoader, TraceBundle
from traces_analyzer.utils.hexstring import HexString


class DirectoryLoader(TraceLoader):
    METADATA_FILENAME = "metadata.json"

    def __init__(self, dir: Path) -> None:
        super().__init__()
        self._dir = dir

    def load(self) -> PotentialAttack:
        with open(self._dir / self.METADATA_FILENAME) as metadata_file:
            metadata = json.load(metadata_file)

            id = metadata["id"]
            transactions_actual = metadata["transaction_replays"]["actual"][
                "transactions"
            ]
            transactions_reverse = metadata["transaction_replays"]["reverse"][
                "transactions"
            ]
            return self._load_trace_bundle(
                id, transactions_actual, transactions_reverse
            )

    def _load_trace_bundle(
        self, id: str, transactions_actual: list[dict], transactions_reverse: list[dict]
    ) -> PotentialAttack:
        return PotentialAttack(
            id=id,
            tx_attack=self._load_transaction_bundle(
                transactions_actual[0], transactions_reverse[1]
            ),
            tx_victim=self._load_transaction_bundle(
                transactions_actual[1], transactions_reverse[0]
            ),
        )

    def _load_transaction_bundle(
        self, tx_actual: dict, tx_reverse: dict
    ) -> TraceBundle:
        assert (
            tx_actual["hash"] == tx_reverse["hash"]
        ), f"Tried to compare traces with different transaction hashes: {tx_actual['hash']} {tx_reverse['hash']}"
        tx = tx_actual["tx"]
        hash = HexString(tx["hash"])

        return TraceBundle(
            hash=hash,
            caller=HexString(tx["from"]),
            to=HexString(tx["to"]),
            calldata=HexString(tx["input"]),
            value=HexString(tx["value"]),
            trace_actual=lazy_load_file(
                self._dir / "actual" / (hash.with_prefix() + ".jsonl")
            ),
            trace_reverse=lazy_load_file(
                self._dir / "reverse" / (hash.with_prefix() + ".jsonl")
            ),
        )


# TODO: implement a cleaner solution (maybe making the class closable?)
# I think this does not close except if everything in the file was read
# Hence, it does not close on errors
def lazy_load_file(path: Path) -> Iterable[str]:
    with open(path) as file:
        for line in file:
            yield line
