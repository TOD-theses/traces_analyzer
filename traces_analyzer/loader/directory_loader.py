from io import TextIOWrapper
import json
from pathlib import Path
from typing_extensions import override

from traces_analyzer.loader.loader import PotentialAttack, TraceLoader, TraceBundle
from traces_analyzer.utils.hexstring import HexString


class DirectoryLoader(TraceLoader):
    METADATA_FILENAME = "metadata.json"

    def __init__(self, dir: Path) -> None:
        super().__init__()
        self._dir = dir
        self._files: list[TextIOWrapper] = []

    @override
    def __enter__(self):
        with open(self._dir / self.METADATA_FILENAME) as metadata_file:
            metadata = json.load(metadata_file)

            id = metadata["id"]
            victim_tx_hash: str = metadata["transactions_order"][-1]
            victim_tx: dict[str, str] = metadata["transactions"][victim_tx_hash]
            metadata["transaction_replays"]["actual"]
            metadata["transaction_replays"]["reverse"]
            return self._load_potential_attack(
                id,
                victim_tx,
            )

    @override
    def __exit__(self, exc_type, exc_value, traceback):
        for file in self._files:
            if not file.closed:
                file.close()

    def _lazy_load_file(self, path: Path):
        file = open(path)
        self._files.append(file)
        for line in file:
            yield line

    def _load_potential_attack(
        self, id: str, victim_tx: dict[str, str]
    ) -> PotentialAttack:
        return PotentialAttack(
            id=id,
            tx_victim=self._load_transaction_bundle(victim_tx),
        )

    def _load_transaction_bundle(self, tx: dict[str, str]) -> TraceBundle:
        hash = HexString(tx["hash"])

        return TraceBundle(
            hash=hash,
            caller=HexString(tx["from"]),
            to=HexString(tx["to"]),
            calldata=HexString(tx["input"]),
            value=HexString(tx["value"]),
            trace_actual=self._lazy_load_file(
                self._dir / "actual" / (hash.with_prefix() + ".jsonl")
            ),
            trace_reverse=self._lazy_load_file(
                self._dir / "reverse" / (hash.with_prefix() + ".jsonl")
            ),
        )
