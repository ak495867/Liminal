from pathlib import Path

import pytest

from liminal.collectors.web import _validate_public_url


def test_collector_rejects_private_and_local_targets():
    for url in (
        "http://localhost",
        "http://127.0.0.1",
        "http://192.168.1.1",
        "file:///tmp/evidence",
    ):
        with pytest.raises(ValueError):
            _validate_public_url(url)


def test_project_has_no_central_joke_registry():
    root = Path(__file__).parents[1]
    source = "\n".join(
        path.read_text(encoding="utf-8") for path in (root / "src").rglob("*.py")
    )
    assert "JOKES" + " =" not in source
    assert "project" + "_joke" not in source


def test_python_source_has_no_comment_lines():
    root = Path(__file__).parents[1]
    paths = (
        list((root / "src").rglob("*.py"))
        + list((root / "tests").rglob("*.py"))
        + list((root / "examples").rglob("*.py"))
    )
    assert paths
    for path in paths:
        for line in path.read_text(encoding="utf-8").splitlines():
            assert not line.lstrip().startswith("#"), path
