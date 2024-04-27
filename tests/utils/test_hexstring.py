from traces_analyzer.utils.hexstring import HexString


def test_hexstring_equals_str():
    assert "abcd" == HexString("abcd")


def test_hexstring_with_prefix_equals_str():
    assert "abcd" == HexString("0xabcd")


def test_hexstring_is_lower_case():
    assert "abcd" == HexString("ABCD")


def test_hexstring_from_int_equals_str():
    assert "abcd" == HexString.from_int(0xABCD)


def test_hexstring_with_prefix():
    assert "0xabcd" == HexString("abcd").with_prefix()


def test_hexstring_without_prefix():
    assert "abcd" == HexString("0xabcd").without_prefix()


def test_hexstring_add():
    assert "abcd" == HexString("ab") + HexString("cd")


def test_hexstring_slice():
    assert "bc" == HexString("abcd")[1:3]


def test_hexstring_lsb():
    assert "cd" == HexString("abcd").lsb()


def test_hexstring_lsb_padding_1():
    assert "0d" == HexString("d").lsb()


def test_hexstring_lsb_padding_2():
    assert "00" == HexString("").lsb()
