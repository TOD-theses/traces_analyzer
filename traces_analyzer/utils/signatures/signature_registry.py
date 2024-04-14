"""A client for the ethereum-function-signature-registry"""

import requests

from traces_analyzer.utils.signatures.signature_lookup import SignatureLookup


class SignatureRegistry(SignatureLookup):
    def __init__(self, base_url: str) -> None:
        super().__init__()
        self._base_url = base_url

    def lookup_by_hex(self, signature_hex: str) -> str | None:
        # using ordering to get the earliest first (which is likely the best one)
        url = f"{self._base_url}/api/v1/signatures/?ordering=created_at&hex_signature={signature_hex}"
        try:
            res = requests.get(url)
        except requests.exceptions.ConnectionError:
            return None

        if not res.ok:
            return None
        data = res.json()
        if data["count"] == 0:
            return None
        return data["results"][0]["text_signature"]
