from io import TextIOWrapper
import json
from pathlib import Path
from typing_extensions import override

from traces_analyzer.loader.event_parser import EventsParser
from traces_analyzer.loader.loader import TxInBothScenarios, TraceLoader, TraceBundle

from traces_parser.datatypes import HexString


class DirectoryLoader(TraceLoader):
    METADATA_FILENAME = "metadata.json"

    def __init__(self, dir: Path, file_parser: EventsParser) -> None:
        super().__init__()
        self._dir = dir
        self._files: list[TextIOWrapper] = []
        self._file_parser = file_parser

    @override
    def __enter__(self):
        with open(self._dir / self.METADATA_FILENAME) as metadata_file:
            metadata = json.load(metadata_file)

            id = metadata["id"]
            tx_hash: str = metadata["transactions_order"][-1]
            tx: dict[str, str] = metadata["transactions"][tx_hash]
            return self._load(id, tx)

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

    def _load(self, id: str, tx: dict[str, str]) -> TxInBothScenarios:
        return TxInBothScenarios(
            id=id,
            tx=self._load_transaction_bundle(tx),
        )

    def _load_transaction_bundle(self, tx: dict[str, str]) -> TraceBundle:
        hash = HexString(tx["hash"])

        file_extensions = ["json", "jsonl"]
        path_normal = None
        path_reverse = None
        for ext in file_extensions:
            path_normal = self._dir / "actual" / f"{hash.with_prefix()}.{ext}"
            path_reverse = self._dir / "reverse" / f"{hash.with_prefix()}.{ext}"
            if path_normal.exists() and path_reverse.exists():
                break

        traces_normal_file = self._lazy_load_file(path_normal)  # type: ignore
        traces_reverse_file = self._lazy_load_file(path_reverse)  # type: ignore

        return TraceBundle(
            hash=hash,
            caller=HexString(tx["from"]),
            to=HexString(tx["to"]),
            calldata=HexString(tx["input"]),
            value=HexString(tx["value"]),
            events_normal=self._file_parser.parse(traces_normal_file),
            events_reverse=self._file_parser.parse(traces_reverse_file),
        )
