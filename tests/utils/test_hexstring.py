from traces_analyzer.utils.hexstring import HexString


def test_hexstring_equals_str():
    assert "abcd" == HexString("abcd")


def test_hexstring_with_prefix_equals_str():
    assert "abcd" == HexString("0xabcd")


def test_hexstring_is_lower_case():
    assert "abcd" == HexString("ABCD")


def test_hexstring_from_int_equals_str():
    assert "abcd" == HexString.from_int(0xABCD)


def test_hexstring_as_int_equals_int():
    assert 0xABCD == HexString("abcd").as_int()


def test_hexstring_with_prefix():
    assert "0xabcd" == HexString("abcd").with_prefix()


def test_hexstring_without_prefix():
    assert "abcd" == HexString("0xabcd").without_prefix()


def test_hexstring_add():
    assert "abcd" == HexString("ab") + HexString("cd")


def test_hexstring_slice():
    assert "bc" == HexString("abcd")[1:3]


def test_hexstring_last_bytes():
    assert "efgh" == HexString("abcdefgh").as_size(2)


def test_hexstring_last_bytes_padding():
    assert "00abcd" == HexString("abcd").as_size(3)


def test_hexstring_iter_bytes_empty():
    assert [] == list(HexString("").iter_bytes())


def test_hexstring_iter_bytes_single():
    assert ["aa"] == list(HexString("aa").iter_bytes())


def test_hexstring_iter_bytes():
    assert ["ab", "cd", "ef"] == list(HexString("abcdef").iter_bytes())
