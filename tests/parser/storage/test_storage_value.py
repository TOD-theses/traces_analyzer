from traces_analyzer.parser.storage.storage_value import StorageByteGroup
from traces_analyzer.utils.hexstring import HexString


def test_storage_byte_group_empty():
    group = StorageByteGroup()

    assert len(group) == 0
    assert group.get_hexstring() == ""


def test_storage_byte_group_from_hexstring():
    hexstring = HexString("abcdef")

    group = StorageByteGroup.from_hexstring(hexstring, 1)

    assert group.get_hexstring() == hexstring


def test_storage_byte_group_concats_hexstrings():
    a = StorageByteGroup.from_hexstring(HexString("abcd"), 1)
    b = StorageByteGroup.from_hexstring(HexString("1234"), 1)

    merged = a + b

    assert merged.get_hexstring() == HexString("abcd1234")


def test_storage_byte_group_slice_hexstrings():
    group = StorageByteGroup.from_hexstring(HexString("abcd1234"), 1)

    group_slice = group[1:3]

    assert group_slice.get_hexstring() == HexString("cd12")


def test_storage_byte_group_assign_slice_hexstrings():
    group = StorageByteGroup.from_hexstring(HexString("abcd1234"), 1)

    group[1:3] = StorageByteGroup.from_hexstring(HexString("11"), 1)

    assert group.get_hexstring() == HexString("ab1134")


def test_storage_byte_group_iterate_bytes():
    group = StorageByteGroup.from_hexstring(HexString("abcd"), 1)

    assert all(b.created_at_step_index == 1 for b in group)
