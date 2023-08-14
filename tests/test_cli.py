"""Test that the CLI will work alright."""
import sys

from pathlib import Path

from conntracker.cli import main
from conntracker.testing import warnings_catcher


def test_cli_features(tmp_path: Path) -> None:
    """Test that the CLI will work."""
    cdir = Path(__file__).absolute().parent
    example_file = str(cdir / "example.py")

    output = tmp_path / "output.txt"

    exit_code = None
    try:
        with warnings_catcher():
            main(["-o", str(output), sys.executable, example_file])
    except SystemExit as exc:
        exit_code = exc.code

    assert exit_code == 0
    assert output.exists()
    text = output.read_text()
    assert len(text.split("\n")) > 1, f"Output:\n{text}\n--"
