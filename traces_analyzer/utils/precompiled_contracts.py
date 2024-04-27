from traces_analyzer.utils.hexstring import HexString

_ADDR_TO_NAME = {
    1: "ecRecover",
    2: "SHA2-256",
    3: "RIPEMD-160",
    4: "identity",
    5: "modexp",
    6: "ecAdd",
    7: "ecMul",
    8: "ecPairing",
    9: "blake2f",
}


def is_precompiled_contract(addr: HexString) -> bool:
    return addr_to_precompiled_contract_name(addr) is not None


def addr_to_precompiled_contract_name(addr: HexString, default: str | None = None) -> str | None:
    return _ADDR_TO_NAME.get(addr.as_int(), default)
