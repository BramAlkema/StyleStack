import pytest
import jsonschema
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "tools"))
from extension_schema_validator import ExtensionSchemaValidator


def build_variable(var_id, deps=None):
    return {
        "id": var_id,
        "type": "color",
        "scope": "theme",
        "xpath": "//a:clrScheme/a:accent1/a:srgbClr/@val",
        "ooxml": {
            "namespace": "http://schemas.openxmlformats.org/drawingml/2006/main",
            "element": "srgbClr",
            "attribute": "val",
            "valueType": "schemeClr",
        },
        "defaultValue": "0066CC",
        "dependencies": deps or [],
    }


def test_acyclic_dependencies():
    variables = [build_variable("var1", ["var2"]), build_variable("var2")]
    validator = ExtensionSchemaValidator()
    results = validator.validate_variable_collection(variables)
    assert all(r.is_valid for r in results)


def test_cyclic_dependencies():
    variables = [build_variable("var1", ["var2"]), build_variable("var2", ["var1"])]
    validator = ExtensionSchemaValidator()
    with pytest.raises(jsonschema.exceptions.ValidationError):
        validator.validate_variable_collection(variables)
