from typing import TypedDict


class CURRENCY_TYPE:
    ETHER = "ETHER"
    ERC20 = "ERC-20"
    ERC721 = "ERC-721"
    ERC777 = "ERC-777"
    ERC1155 = "ERC-1155"


class CurrencyChange(TypedDict):
    type: str
    """Type of the currency, e.g. ETHER or ERC-20, ..."""
    currency_identifier: str
    """ID for the currency. For Ether this is None, for tokens this is the storage address that emitted the LOG and potentially a token id"""
    owner: str
    """Address for which a change occurred"""
    change: int
    """Positive or negative change"""
