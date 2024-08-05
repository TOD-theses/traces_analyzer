from copy import deepcopy
from tests.test_utils.test_utils import _test_call
from traces_parser.datatypes.storage_byte_group import HexString

from traces_analyzer.evaluation.securify_properties_evaluation import (
    check_securify_properties,
)

calls = {
    (HexString("0xabcd"), 10): [_test_call("0xabcd", 10, "0xa", "0xbbbb")],
    (HexString("0xabcd"), 12): [
        _test_call("0xabcd", 12, "0xa", "0xbbbb"),
        _test_call("0xabcd", 12, "0xa", "0xcccc"),
    ],
    (HexString("0xefef"), 1234): [_test_call("0xefef", 1234, "0xa", "0xbbbb")],
}


def test_no_property_holds_with_identical_calls():
    calls_normal = deepcopy(calls)
    calls_reverse = deepcopy(calls)

    properties = check_securify_properties(calls_normal, calls_reverse)

    all(not prop for prop in properties.values())


def test_tod_transfer_different_calls():
    calls_normal = deepcopy(calls)
    calls_normal[(HexString("0xabcd"), 12)].pop()
    calls_reverse = deepcopy(calls)

    properties = check_securify_properties(calls_normal, calls_reverse)

    assert properties["TOD_Transfer"]


def test_tod_amount_different_amounts():
    calls_normal = deepcopy(calls)
    # set higher value
    calls_normal[(HexString("0xabcd"), 12)][1] = _test_call(
        "0xabcd", 12, "0xaaaaaa", "0xcccc"
    )
    calls_reverse = deepcopy(calls)

    properties = check_securify_properties(calls_normal, calls_reverse)

    assert properties["TOD_Amount"]


def test_tod_receiver_different_receiver():
    calls_normal = deepcopy(calls)
    # change receiver to 0xdddd
    calls_normal[(HexString("0xabcd"), 12)][1] = _test_call(
        "0xabcd", 12, "0xa", "0xdddd"
    )
    calls_reverse = deepcopy(calls)

    properties = check_securify_properties(calls_normal, calls_reverse)

    assert properties["TOD_Receiver"]
