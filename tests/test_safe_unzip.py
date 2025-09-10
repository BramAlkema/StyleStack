import zipfile
import pathlib
import pytest
import importlib.util


_BUILD_SPEC = importlib.util.spec_from_file_location(
    "build_module", pathlib.Path(__file__).resolve().parents[1] / "build.py"
)
build_module = importlib.util.module_from_spec(_BUILD_SPEC)
_BUILD_SPEC.loader.exec_module(build_module)

safe_unzip = build_module.safe_unzip
BuildContext = build_module.BuildContext
StyleStackError = build_module.StyleStackError


def _make_context(tmp_path):
    return BuildContext(source_path=tmp_path / "src", output_path=tmp_path / "out", temp_dir=tmp_path)


def test_rejects_path_traversal(tmp_path):
    zip_path = tmp_path / "traversal.zip"
    with zipfile.ZipFile(zip_path, "w") as z:
        z.writestr("../evil.txt", "malicious")
    ctx = _make_context(tmp_path)
    with pytest.raises(StyleStackError):
        safe_unzip(zip_path, tmp_path / "dest", ctx)


def test_rejects_absolute_path(tmp_path):
    zip_path = tmp_path / "absolute.zip"
    with zipfile.ZipFile(zip_path, "w") as z:
        z.writestr("/etc/passwd", "malicious")
    ctx = _make_context(tmp_path)
    with pytest.raises(StyleStackError):
        safe_unzip(zip_path, tmp_path / "dest", ctx)
