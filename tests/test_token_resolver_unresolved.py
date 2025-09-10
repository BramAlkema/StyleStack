import pytest
import sys
from pathlib import Path

# Ensure repository root is in path for imports
sys.path.append(str(Path(__file__).resolve().parents[1]))

from tools.token_resolver import TokenResolver


def test_detect_circular_reference():
    resolver = TokenResolver()
    tokens = {"a": "{b}", "b": "{a}"}
    with pytest.raises(ValueError) as exc:
        resolver.resolve_token_references(tokens)
    assert "Circular token reference" in str(exc.value)


def test_report_unresolved_tokens():
    resolver = TokenResolver()
    tokens = {"a": "{missing}"}
    with pytest.raises(ValueError) as exc:
        resolver.resolve_token_references(tokens)
    message = str(exc.value)
    assert "Unresolved token references" in message
    assert "a" in message or "missing" in message
