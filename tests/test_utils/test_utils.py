from traces_analyzer.utils.hexstring import HexString


def _test_addr(name: str) -> HexString:
    return HexString.from_int(hash(name)).as_address()
