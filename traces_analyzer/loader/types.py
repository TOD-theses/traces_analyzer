from typing import TypedDict


TxData = TypedDict(
    "TxData",
    {
        "from": str,
        "to": str,
        "hash": str,
        "input": str,
        "value": str,
    },
)
