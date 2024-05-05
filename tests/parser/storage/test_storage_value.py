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

    assert all(b._created_at_step_index == 1 for b in group)


def test_storage_byte_group_depends_on_instruction_indexes():
    group = StorageByteGroup.from_hexstring(HexString("abcd1234"), 1)
    group[1:3] = StorageByteGroup.from_hexstring(HexString("11"), 2)
    group += StorageByteGroup.from_hexstring(HexString("ef"), 3)

    assert group.depends_on_instruction_indexes() == {1, 2, 3}


def test_storage_byte_group_split_by_dependencies():
    group = StorageByteGroup.from_hexstring(HexString("abcd"), 1)
    group += StorageByteGroup.from_hexstring(HexString("11"), 2)
    group += StorageByteGroup.from_hexstring(HexString("ef"), 1)

    groups = list(group.split_by_dependencies())

    assert len(groups) == 3
    assert groups[0].get_hexstring() == "abcd"
    assert groups[1].get_hexstring() == "11"
    assert groups[2].get_hexstring() == "ef"
    assert groups[0].depends_on_instruction_indexes() == {1}
    assert groups[1].depends_on_instruction_indexes() == {2}
    assert groups[2].depends_on_instruction_indexes() == {1}
