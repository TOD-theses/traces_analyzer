from traces_analyzer.utils.hexstring import HexString


class StorageByte:
    def __init__(self, byte: bytes, created_at_step_index: int) -> None:
        self._byte = byte
        self._created_at_step_index = created_at_step_index
        # self.touched_at_step_indexes: list[int] = []

    def __str__(self) -> str:
        return self._byte.decode("utf-8")

    def __repr__(self) -> str:
        return f'<{self._byte.decode("utf-8")},{self._created_at_step_index}>'


class StorageByteGroup:
    def __init__(
        self, hexstring: HexString = HexString(""), step_indexes: list[int] = []
    ) -> None:
        if hexstring.size() != len(step_indexes):
            raise Exception(
                f"The hexstring size does not match the step_indexes length: {hexstring.size()} vs {len(step_indexes)}"
            )

        self._hexstring = hexstring
        self._step_indexes = step_indexes

    def get_hexstring(self) -> HexString:
        return self._hexstring

    def depends_on_instruction_indexes(self) -> set[int]:
        return set(self._step_indexes)

    def split_by_dependencies(self) -> list["StorageByteGroup"]:
        if not (size := len(self)):
            return []
        groups: list["StorageByteGroup"] = []
        current_start_index = 0
        current_step_index = self._step_indexes[0]
        for i in range(size):
            if self._step_indexes[i] != current_step_index:
                groups.append(self[current_start_index:i])
                current_start_index = i
                current_step_index = self._step_indexes[i]
        if current_start_index < size:
            groups.append(self[current_start_index:])

        return groups

    @staticmethod
    def from_hexstring(hexstring: HexString, creation_step_index: int):
        return StorageByteGroup(
            hexstring, [creation_step_index for _ in range(hexstring.size())]
        )

    def clone(self) -> "StorageByteGroup":
        return StorageByteGroup(self._hexstring, list(self._step_indexes))

    def __add__(self, other: "StorageByteGroup") -> "StorageByteGroup":
        return StorageByteGroup(
            self._hexstring + other._hexstring, self._step_indexes + other._step_indexes
        )

    def __getitem__(self, index: slice) -> "StorageByteGroup":
        start, stop = slice_to_start_stop(index, len(self))
        if isinstance(index.step, int):
            raise NotImplementedError()
        hexstring_slice = self._hexstring[start * 2 : stop * 2]
        step_indexes_slice = self._step_indexes[start:stop]
        return StorageByteGroup(hexstring_slice, step_indexes_slice)

    def __setitem__(self, index: slice, value: "StorageByteGroup") -> None:
        start, stop = slice_to_start_stop(index, len(self))
        self._hexstring = (
            self._hexstring[: start * 2]
            + value._hexstring
            + self._hexstring[stop * 2 :]
        )
        self._step_indexes[start:stop] = value._step_indexes

    def __len__(self) -> int:
        return self._hexstring.size()

    def __eq__(self, value: object) -> bool:
        return (
            isinstance(value, StorageByteGroup) and self._hexstring == value._hexstring
            # and self._step_indexes == value._step_indexes
        )

    def __str__(self) -> str:
        groups = self.split_by_dependencies()
        return (
            "<"
            + ",".join(
                f"({group._hexstring}|#{group._step_indexes[0]})" for group in groups
            )
            + ">"
        )

    def __repr__(self) -> str:
        return str(self)


def slice_to_start_stop(slice: slice, len: int) -> tuple[int, int]:
    if isinstance(slice.step, int):
        raise NotImplementedError()
    start = slice.start if isinstance(slice.start, int) else 0
    stop = slice.stop if isinstance(slice.stop, int) else len
    return start, stop
