import time
import unittest
from lxml import etree

from tools.patch_execution_engine import (
    PatchExecutionEngine,
    ExecutionMode,
    ExecutionContext,
    StyleStackError,
    PatchErrorCode,
)
from tools.json_patch_parser import ValidationLevel


class TestPatchExecutionEngineErrorHandling(unittest.TestCase):
    def setUp(self):
        self.xml_doc = etree.fromstring("<root/>")

    def test_invalid_patch_strict_validation(self):
        engine = PatchExecutionEngine(validation_level=ValidationLevel.STRICT)
        invalid_patch = '{"metadata": {"version": "1.0"}}'
        with self.assertRaises(StyleStackError) as ctx:
            engine.execute_patch_content(invalid_patch, self.xml_doc, ExecutionMode.NORMAL)
        self.assertEqual(ctx.exception.error_code, PatchErrorCode.INVALID_PATCH.value)

    def test_unsupported_operation_normal_mode(self):
        engine = PatchExecutionEngine()
        patches = [{"operation": "remove", "target": "//a:srgbClr/@val", "value": "00FF00"}]
        with self.assertRaises(StyleStackError) as ctx:
            engine._execute_patches(
                patches,
                self.xml_doc,
                ExecutionMode.NORMAL,
                ExecutionContext(),
                [],
                [],
                time.time(),
            )
        self.assertEqual(ctx.exception.error_code, PatchErrorCode.UNSUPPORTED_OPERATION.value)

    def test_unsupported_operation_validate_only(self):
        engine = PatchExecutionEngine()
        patches = [{"operation": "remove", "target": "//a:srgbClr/@val", "value": "00FF00"}]
        with self.assertRaises(StyleStackError) as ctx:
            engine._execute_patches(
                patches,
                self.xml_doc,
                ExecutionMode.VALIDATE_ONLY,
                ExecutionContext(),
                [],
                [],
                time.time(),
            )
        self.assertEqual(ctx.exception.error_code, PatchErrorCode.UNSUPPORTED_OPERATION.value)


if __name__ == "__main__":
    unittest.main()

