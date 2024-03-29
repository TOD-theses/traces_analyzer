from pathlib import Path

from traces_analyzer.loader.directory_loader import DirectoryLoader


def test_directory_loader(sample_traces_path: Path):
    id = "62a8b9ece30161692b68cbb5"
    dir = sample_traces_path / id

    directory_loader = DirectoryLoader(dir)

    bundle = directory_loader.load()

    assert bundle.id == id

    assert bundle.tx_attack.hash.lower() == "0x5bc779188a1a4f701c33980a97e902fc097dc48393a01c61f363fce09f33e4a0"
    assert bundle.tx_attack.caller.lower() == "0x822beb1cd1bd7148d07e4107b636fd15118913bc"
    assert bundle.tx_attack.to.lower() == "0x11111112542d85b3ef69ae05771c2dccff4faa26"

    assert len(list(bundle.tx_attack.trace_actual)) == 3284
    assert len(list(bundle.tx_attack.trace_reverse)) == 3106

    assert bundle.tx_victim.hash.lower() == "0xb8fbee3430ed8cfb8793407b61c4d801e61b48c08123ceaed4137643aa9c79a6"
    assert bundle.tx_victim.caller.lower() == "0x8591204047dc7d6edc782fa3cc8ee29e2bdd61e5"
    assert bundle.tx_victim.to.lower() == "0xdef171fe48cf0115b1d80b88dc8eab59176fee57"

    assert len(list(bundle.tx_victim.trace_actual)) == 91211
    assert len(list(bundle.tx_victim.trace_reverse)) == 91389
