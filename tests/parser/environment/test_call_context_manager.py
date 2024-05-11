from typing import Callable
import pytest
from tests.test_utils.test_utils import _test_group, _test_hash_addr, _test_root, _test_child, _test_child_of
from traces_analyzer.parser.environment.call_context import CallContext, HaltType
from traces_analyzer.parser.environment.call_context_manager import (
    ExpectedDepthChange,
    UnexpectedDepthChange,
    build_call_tree,
    update_call_context,
)
from traces_analyzer.parser.information_flow.information_flow_spec import Flow
from traces_analyzer.parser.instructions.instruction import Instruction
from traces_analyzer.parser.instructions.instructions import (
    ADD,
    CALL,
    CALLCODE,
    CREATE,
    CREATE2,
    DELEGATECALL,
    RETURN,
    REVERT,
    SELFDESTRUCT,
    STATICCALL,
    STOP,
)
from traces_analyzer.parser.storage.storage_writes import CalldataWrite, StorageAccesses, StorageWrites
from traces_analyzer.utils.hexstring import HexString


def flow_with_calldata() -> Flow:
    return Flow(accesses=StorageAccesses(), writes=StorageWrites(calldata=CalldataWrite(_test_group("11111111"))))


get_add: Callable[[CallContext], Instruction] = lambda call_context: ADD(
    ADD.opcode, "ADD", 1, 1, call_context, (1, 2), (3), None, None
)
get_call: Callable[[CallContext, HexString], Instruction] = lambda call_context, address: CALL(
    CALL.opcode,
    "CALL",
    1,
    1,
    call_context,
    (
        HexString("0x1234"),
        address,
        HexString("0x1"),
        HexString("0x0"),
        HexString("0x4"),
        HexString("0x0"),
        HexString("0x0"),
    ),
    (),
    HexString("11111111"),
    None,
    flow_with_calldata(),
)
get_staticcall: Callable[[CallContext, HexString], Instruction] = lambda call_context, address: STATICCALL(
    STATICCALL.opcode,
    "STATICCALL",
    1,
    1,
    call_context,
    (HexString("0x1234"), address, HexString("0x0"), HexString("0x4"), HexString("0x0"), HexString("0x0")),
    (),
    HexString("11111111"),
    None,
    flow_with_calldata(),
)
get_delegate_call: Callable[[CallContext, HexString], Instruction] = lambda call_context, address: DELEGATECALL(
    DELEGATECALL.opcode,
    "DELEGATECALL",
    1,
    1,
    call_context,
    (HexString("0x1234"), address, HexString("0x0"), HexString("0x4"), HexString("0x0"), HexString("0x0")),
    (),
    HexString("11111111"),
    None,
    flow_with_calldata(),
)
get_callcode: Callable[[CallContext, HexString], Instruction] = lambda call_context, address: CALLCODE(
    CALLCODE.opcode,
    "CALLCODE",
    1,
    1,
    call_context,
    (
        HexString("0x1234"),
        address,
        HexString("0x1"),
        HexString("0x0"),
        HexString("0x4"),
        HexString("0x0"),
        HexString("0x0"),
    ),
    (),
    HexString("11111111"),
    None,
    flow_with_calldata(),
)
get_create: Callable[[CallContext], Instruction] = lambda call_context: CREATE(
    CREATE.opcode,
    "CREATE",
    1,
    1,
    call_context,
    (HexString("0x0"), HexString("0x0"), HexString("0x4")),
    (),
    HexString("11111111"),
    None,
)
get_create2: Callable[[CallContext], Instruction] = lambda call_context: CREATE(
    CREATE2.opcode,
    "CREATE2",
    1,
    1,
    call_context,
    (HexString("0x0"), HexString("0x0"), HexString("0x4"), HexString("0x0")),
    (),
    HexString("11111111"),
    None,
)
get_stop: Callable[[CallContext], Instruction] = lambda call_context: STOP(
    STOP.opcode, "STOP", 1, 1, call_context, (), (), None, None
)
get_return: Callable[[CallContext], Instruction] = lambda call_context: RETURN(
    RETURN.opcode, "RETURN", 1, 1, call_context, (HexString("0x0"), HexString("0x0")), (), None, None
)
get_revert: Callable[[CallContext], Instruction] = lambda call_context: REVERT(
    REVERT.opcode, "REVERT", 1, 1, call_context, (HexString("0x0"), HexString("0x0")), (), None, None
)
get_selfdestruct: Callable[[CallContext], Instruction] = lambda call_context: SELFDESTRUCT(
    SELFDESTRUCT.opcode, "SELFDESTRUCT", 1, 1, call_context, ("0x0"), (), "", ""
)


def test_call_context_manager_does_not_update_on_add():
    root = _test_root()
    add = get_add(root)

    next_call_context = update_call_context(root, add, root.depth)

    assert next_call_context == root
    assert not root.reverted


def test_call_context_managers_does_not_enter_without_depth_change():
    """For instance when the call only sends ether, we don't want to dont enter a new call context"""
    root = _test_root()
    call = get_call(root, "0xtarget")

    next_call_context = update_call_context(root, call, root.depth)

    assert next_call_context == root


# TODO: are there other instructions that create a new call context? eg CREATE?
@pytest.mark.parametrize(
    "call",
    [get_call(_test_root(), _test_hash_addr("0xtarget")), get_staticcall(_test_root(), _test_hash_addr("0xtarget"))],
)
def test_call_context_manager_enters_with_code_and_storage(call):
    root = _test_root()

    next_call_context = update_call_context(root, call, root.depth + 1)

    assert next_call_context.depth == 2
    if isinstance(call, DELEGATECALL):
        assert next_call_context.msg_sender == root.msg_sender
    else:
        assert next_call_context.msg_sender == root.storage_address
    assert next_call_context.code_address == _test_hash_addr("0xtarget")
    assert next_call_context.storage_address == _test_hash_addr("0xtarget")
    assert next_call_context.calldata.get_hexstring() == "11111111"
    assert not next_call_context.is_contract_initialization


@pytest.mark.parametrize(
    "call",
    [
        get_delegate_call(_test_root(), _test_hash_addr("0xtarget")),
        get_callcode(_test_root(), _test_hash_addr("0xtarget")),
    ],
)
def test_call_context_manager_enters_only_with_code_address(call):
    root = _test_root()

    next_call_context = update_call_context(root, call, root.depth + 1)

    assert next_call_context.depth == 2
    if isinstance(call, DELEGATECALL):
        assert next_call_context.msg_sender == root.msg_sender
    else:
        assert next_call_context.msg_sender == root.storage_address
    assert next_call_context.code_address == _test_hash_addr("0xtarget")
    assert next_call_context.storage_address == root.storage_address
    assert next_call_context.calldata.get_hexstring() == "11111111"
    assert not next_call_context.is_contract_initialization


@pytest.mark.parametrize("create", [get_create(_test_root()), get_create2(_test_root())])
def test_call_context_manager_enters_on_contract_creation(create):
    root = _test_root()

    next_call_context = update_call_context(root, create, root.depth + 1)

    assert next_call_context.depth == 2
    assert next_call_context.msg_sender == root.code_address
    # NOTE: the manager DOES NOT compute the correct addresses for the created contracts
    # TODO: should we bother to compute the correct addresses (also depending on CREATE/CREATE2)?
    assert next_call_context.code_address == next_call_context.storage_address
    assert next_call_context.calldata.get_hexstring() == ""
    assert next_call_context.is_contract_initialization


def test_call_context_manager_throws_on_stop_without_depth_change():
    child = _test_child()
    stop = get_stop(child)

    with pytest.raises(ExpectedDepthChange):
        update_call_context(child, stop, child.depth)


def test_call_context_manager_throws_on_too_large_depth_change():
    child = _test_child()
    stop = get_stop(child)

    with pytest.raises(UnexpectedDepthChange):
        update_call_context(child, stop, child.depth - 2)


def test_call_context_manager_throws_when_attempting_to_stop_at_root():
    root = _test_root()
    stop = get_stop(root)

    with pytest.raises(UnexpectedDepthChange):
        update_call_context(root, stop, root.depth - 1)


@pytest.mark.parametrize("ret", [get_stop(_test_child()), get_return(_test_child()), get_selfdestruct(_test_child())])
def test_call_context_manager_returns_normal(ret):
    root = _test_root()
    child = _test_child()

    next_call_context = update_call_context(child, ret, child.depth - 1)

    assert next_call_context == root
    assert not child.reverted
    assert child.halt_type == HaltType.NORMAL


def test_call_context_manager_does_not_return_at_root():
    root = _test_root()
    ret = get_return(root)

    next_call_context = update_call_context(root, ret, None)

    assert next_call_context == root


def test_call_context_manager_reverts():
    root = _test_root()
    child = _test_child()
    revert = get_revert(child)

    next_call_context = update_call_context(child, revert, child.depth - 1)

    assert next_call_context == root
    assert child.reverted
    assert child.halt_type == HaltType.NORMAL


def test_call_context_manager_makes_exceptional_halt():
    root = _test_root()
    child = _test_child()
    add = get_add(child)

    next_call_context = update_call_context(child, add, child.depth - 1)

    assert next_call_context == root
    assert child.reverted
    assert child.halt_type == HaltType.EXCEPTIONAL


def test_build_call_tree():
    root = _test_root()
    first = _test_child_of(root, _test_hash_addr("0xfirst"))
    first_nested = _test_child_of(first, _test_hash_addr("0xfirst_nested"))
    second = _test_child_of(root, _test_hash_addr("0xsecond"))
    third = _test_child_of(root, _test_hash_addr("0xthird"))

    instructions = [
        get_add(root),
        get_add(root),
        get_add(first),
        get_add(first_nested),
        get_add(first_nested),
        get_add(second),
        get_add(third),
    ]

    tree = build_call_tree(root, instructions)

    # correct structure
    assert tree.call_context == root
    assert len(tree.children) == 3
    first, second, third = tree.children
    assert len(first.children) == 1
    first_nested = first.children[0]

    # correct addresses
    assert first.call_context.code_address == _test_hash_addr("0xfirst")
    assert first_nested.call_context.code_address == _test_hash_addr("0xfirst_nested")
    assert second.call_context.code_address == _test_hash_addr("0xsecond")
    assert third.call_context.code_address == _test_hash_addr("0xthird")
