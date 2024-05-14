from traces_analyzer.parser.information_flow.information_flow_dsl_implementation import (
    CombineNode,
    FlowNode,
    FlowNodeWithResult,
    FlowSpec,
    NoopNode,
    WritingFlowNode,
    _balance_of_node,
    _balance_transfer_node,
    _calldata_range_node,
    _calldata_size_node,
    _calldata_write_node,
    _callvalue_node,
    _current_storage_address_node,
    _mem_range_node,
    _mem_write_node,
    _oracle_stack_peek_node,
    _return_data_range_node,
    _return_data_size_node,
    _return_data_write_node,
    _selfdestruct_node,
    _stack_arg_node,
    _stack_peek_node,
    _stack_push_node,
    _stack_set_node,
    _to_size_node,
)


def stack_arg(index: int) -> FlowNodeWithResult:
    """Get stack value and pop"""
    return _stack_arg_node(index)


def stack_peek(index: int) -> FlowNodeWithResult:
    """Get stack value without pop"""
    return _stack_peek_node(index)


def stack_push(value: FlowNodeWithResult | str) -> WritingFlowNode:
    return _stack_push_node(value)


def stack_set(index: FlowNodeWithResult | int, value: FlowNodeWithResult | str) -> WritingFlowNode:
    return _stack_set_node(index, value)


def oracle_stack_peek(index: int) -> FlowNodeWithResult:
    return _oracle_stack_peek_node(index)


def mem_range(offset: FlowNodeWithResult | int, size: FlowNodeWithResult | int) -> FlowNodeWithResult:
    return _mem_range_node(offset, size)


def mem_write(offset: FlowNodeWithResult | int, value: FlowNodeWithResult | str) -> WritingFlowNode:
    return _mem_write_node(offset, value)


def to_size(value: FlowNodeWithResult, bytes_size: int) -> FlowNodeWithResult:
    return _to_size_node(value, bytes_size)


def current_storage_address() -> FlowNodeWithResult:
    return _current_storage_address_node()


def balance_of(value: FlowNodeWithResult) -> FlowNodeWithResult:
    return _balance_of_node(value)


def balance_transfer(
    from_addr: FlowNodeWithResult, to_addr: FlowNodeWithResult | str, value: FlowNodeWithResult
) -> WritingFlowNode:
    return _balance_transfer_node(from_addr, to_addr, value)


def selfdestruct(from_addr: FlowNodeWithResult, to_addr: FlowNodeWithResult) -> WritingFlowNode:
    return _selfdestruct_node(from_addr, to_addr)


def calldata_range(offset: FlowNodeWithResult | int, size: FlowNodeWithResult | int) -> FlowNodeWithResult:
    return _calldata_range_node(offset, size)


def calldata_write(value: FlowNodeWithResult) -> WritingFlowNode:
    return _calldata_write_node(value)


def calldata_size() -> FlowNodeWithResult:
    return _calldata_size_node()


def callvalue() -> FlowNodeWithResult:
    return _callvalue_node()


def return_data_range(offset: FlowNodeWithResult | int, size: FlowNodeWithResult) -> FlowNodeWithResult:
    return _return_data_range_node(offset, size)


def return_data_write(value: FlowNodeWithResult) -> WritingFlowNode:
    return _return_data_write_node(value)


def return_data_size() -> FlowNodeWithResult:
    return _return_data_size_node()


def noop() -> FlowSpec:
    return NoopNode()


def combine(*inputs: FlowNode) -> FlowSpec:
    return CombineNode(inputs)
