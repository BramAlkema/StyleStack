import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build import BuildContext, process_extension_variables


class DummyResult:
    def __init__(self, success=True, error_message="", validation_errors=None):
        self.success = success
        self.error_message = error_message
        self.validation_errors = validation_errors or []


class DummyPipeline:
    def __init__(self):
        self.processed = []

    def substitute_variables_in_document(
        self, file_path, backup_original=True, validate_result=True
    ):
        self.processed.append(Path(file_path))
        return DummyResult(success=True)


def test_process_extension_variables_uses_extension_manager(tmp_path, caplog):
    pkg_dir = tmp_path

    # XML file containing a StyleStack extension
    ext_xml = pkg_dir / "with_ext.xml"
    ext_xml.write_text(
        """
<root xmlns:stylestack='https://stylestack.org/extensions/variables/v1'>
  <extLst>
    <ext uri='https://stylestack.org/extensions/variables/v1'>
      <stylestack:variables>
        <stylestack:variable id='a' type='string' scope='user'/>
      </stylestack:variables>
    </ext>
  </extLst>
</root>
""",
        encoding="utf-8",
    )

    # XML file without any StyleStack extensions
    no_ext_xml = pkg_dir / "without_ext.xml"
    no_ext_xml.write_text("<root />", encoding="utf-8")

    context = BuildContext(
        source_path=pkg_dir,
        output_path=pkg_dir,
        temp_dir=pkg_dir,
        substitution_pipeline=DummyPipeline(),
    )

    with caplog.at_level(logging.INFO):
        process_extension_variables(context, pkg_dir)

    processed_files = [p.name for p in context.substitution_pipeline.processed]
    assert processed_files == ["with_ext.xml"]
    assert any("with_ext.xml" in record.message for record in caplog.records)

