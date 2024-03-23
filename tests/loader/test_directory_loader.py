from pathlib import Path

from traces_analyzer.loader.directory_loader import DirectoryLoader


def test_directory_loader(sample_traces_path: Path):
    id = "62a8b9ece30161692b68cbb5"
    dir = sample_traces_path / id

    directory_loader = DirectoryLoader(dir)

    bundle = directory_loader.load()

    assert bundle.id == id

    assert bundle.tx_victim.hash == "0x5bc779188a1a4f701c33980a97e902fc097dc48393a01c61f363fce09f33e4a0"
    assert bundle.tx_victim.caller == "0x822bEB1Cd1bD7148d07e4107b636fd15118913bC"
    assert bundle.tx_victim.to == "0x11111112542D85B3EF69AE05771c2dCCff4fAa26"

    assert len(list(bundle.tx_victim.trace_one)) == 3106
    assert len(list(bundle.tx_victim.trace_two)) == 3284

    assert bundle.tx_attack.hash == "0xb8fbee3430ed8cfb8793407b61c4d801e61b48c08123ceaed4137643aa9c79a6"
    assert bundle.tx_attack.caller == "0x8591204047dC7D6EDc782fa3cc8eE29e2bDD61e5"
    assert bundle.tx_attack.to == "0xDEF171Fe48CF0115B1d80b88dc8eAB59176FEe57"

    assert len(list(bundle.tx_attack.trace_one)) == 91389
    assert len(list(bundle.tx_attack.trace_two)) == 91211
