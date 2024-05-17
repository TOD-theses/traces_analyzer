from traces_analyzer.utils.mnemonics import (
    _OPCODE_TO_NAME,
    _NAME_TO_OPCODE,
    name_to_opcode,
    opcode_to_name,
)

NUMBER_OF_OPCODES = 149


def test_mnemonics_opcode_to_name():
    assert len(_OPCODE_TO_NAME) == NUMBER_OF_OPCODES

    assert opcode_to_name(241) == "CALL"
    assert opcode_to_name(12345) is None
    assert opcode_to_name(12345, "UNKNOWN") == "UNKNOWN"


def test_mnemonics_name_to_opcode():
    assert len(_NAME_TO_OPCODE) == NUMBER_OF_OPCODES

    assert name_to_opcode("CALL") == 241
    assert name_to_opcode("call") == 241
    assert name_to_opcode("abc") is None
    assert name_to_opcode("abc", -1) == -1
