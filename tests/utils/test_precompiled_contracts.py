from traces_analyzer.utils.hexstring import HexString
from traces_analyzer.utils.precompiled_contracts import (
    addr_to_precompiled_contract_name,
    is_precompiled_contract,
)


def test_addr_to_precompiled_contract_name():
    assert addr_to_precompiled_contract_name(HexString("0x1")) == "ecRecover"
    assert (
        addr_to_precompiled_contract_name(
            HexString("0x0000000000000000000000000000000000000001")
        )
        == "ecRecover"
    )

    assert addr_to_precompiled_contract_name(HexString("0x12")) is None
    assert (
        addr_to_precompiled_contract_name(HexString("0x12"), "Not found") == "Not found"
    )
    assert (
        addr_to_precompiled_contract_name(
            HexString("0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF")
        )
        is None
    )


def test_is_precompiled_contract():
    assert is_precompiled_contract(HexString("0x1"))
    assert is_precompiled_contract(
        HexString("0x0000000000000000000000000000000000000001")
    )

    assert not is_precompiled_contract(HexString("0x12"))
    assert not is_precompiled_contract(
        HexString("0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF")
    )
