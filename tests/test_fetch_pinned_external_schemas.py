import hashlib
import json

import pytest

from scripts.fetch_pinned_external_schemas import _raw_url, fetch_schema


class Response:
    def __init__(self, raw):
        self.raw = raw

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.raw


def test_fetch_schema_verifies_raw_bytes_without_persisting_source():
    raw = json.dumps({"type": "object", "additionalProperties": False}).encode()
    digest = hashlib.sha256(raw).hexdigest()

    def opener(request, timeout):
        assert request.full_url.startswith("https://raw.githubusercontent.com/")
        assert timeout == 30
        return Response(raw)

    assert (
        fetch_schema(
            url="https://raw.githubusercontent.com/o/r/c/s.json", expected_sha256=digest, opener=opener
        )
        == raw
    )
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        fetch_schema(
            url="https://raw.githubusercontent.com/o/r/c/s.json", expected_sha256="0" * 64, opener=opener
        )


def test_raw_url_rejects_parent_traversal():
    assert _raw_url("owner", "repo", "a" * 40, "contracts/schema.json").endswith("/contracts/schema.json")
    with pytest.raises(ValueError, match="relative POSIX"):
        _raw_url("owner", "repo", "a" * 40, "../schema.json")
