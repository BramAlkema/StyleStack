import json
import shutil
from pathlib import Path

import pytest
from jsonschema import ValidationError

import sys

# Ensure repository root is in path for imports
sys.path.append(str(Path(__file__).resolve().parents[1]))

from tools.token_resolver import TokenResolver


def _prepare_schema(tmp_tokens_dir: Path) -> None:
    schema_src = Path(__file__).resolve().parents[1] / "tokens" / "schema" / "design-tokens.schema.json"
    schema_dst_dir = tmp_tokens_dir / "schema"
    schema_dst_dir.mkdir(parents=True)
    shutil.copy(schema_src, schema_dst_dir / "design-tokens.schema.json")


def test_load_core_tokens_valid(tmp_path: Path) -> None:
    tokens_dir = tmp_path
    _prepare_schema(tokens_dir)
    core_dir = tokens_dir / "core"
    core_dir.mkdir()
    valid_tokens = {
        "$schema": "https://stylestack.dev/schemas/design-tokens.schema.json",
        "colors": {
            "primary": {
                "value": "#FFFFFF",
                "type": "color",
                "description": "White color",
            }
        },
    }
    with open(core_dir / "valid.json", "w") as f:
        json.dump(valid_tokens, f)

    resolver = TokenResolver()
    loaded = resolver.load_core_tokens(tokens_dir)
    assert loaded["colors"]["primary"]["value"] == "#FFFFFF"


def test_load_core_tokens_invalid(tmp_path: Path) -> None:
    tokens_dir = tmp_path
    _prepare_schema(tokens_dir)
    core_dir = tokens_dir / "core"
    core_dir.mkdir()
    invalid_tokens = {
        "$schema": "https://stylestack.dev/schemas/design-tokens.schema.json",
        "colors": {
            "primary": {
                "value": "#FFFFFF"
                # Missing required 'type'
            }
        },
    }
    with open(core_dir / "invalid.json", "w") as f:
        json.dump(invalid_tokens, f)

    resolver = TokenResolver()
    with pytest.raises(ValidationError):
        resolver.load_core_tokens(tokens_dir)

