"""The same level and seed give the same bytes."""

import hashlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

from mailgen.package import build_files
from mailgen.sampler import sample_instance

ROOT = Path(__file__).parent.parent


@pytest.mark.parametrize("level", [1, 2, 3])
def test_same_seed_gives_the_same_files(level):
    assert build_files(sample_instance(level, 5)) == build_files(sample_instance(level, 5))


@pytest.mark.parametrize("level", [1, 2, 3])
def test_another_seed_gives_another_mailbox(level):
    one = build_files(sample_instance(level, 5))
    other = build_files(sample_instance(level, 6))
    assert mailbox(one) != mailbox(other)


def mailbox(files) -> dict:
    return {path: text for path, text in files.items() if path.startswith("environment/mailbox/")}


def generate(out_dir, hash_seed):
    """Runs the generator in a fresh interpreter with its own hash seed, as on another machine."""
    environment = {**os.environ, "PYTHONHASHSEED": hash_seed}
    command = [sys.executable, "-m", "mailgen", "generate", "--level", "2", "--seed", "3", "--out", str(out_dir)]
    subprocess.run(command, check=True, cwd=ROOT, env=environment, capture_output=True)


def digest(directory) -> str:
    """One hash over the names and the bytes of all files below a directory."""
    total = hashlib.sha256()
    for path in sorted(directory.rglob("*")):
        if path.is_file():
            total.update(path.relative_to(directory).as_posix().encode("utf-8"))
            total.update(path.read_bytes())
    return total.hexdigest()


def test_output_does_not_depend_on_the_hash_seed(tmp_path):
    generate(tmp_path / "one", "1")
    generate(tmp_path / "other", "2")
    assert digest(tmp_path / "one") == digest(tmp_path / "other")


def test_written_files_have_unix_line_ends(tmp_path):
    generate(tmp_path, "0")
    files = [path for path in tmp_path.rglob("*") if path.is_file()]
    assert files
    assert not any(b"\r" in path.read_bytes() for path in files)
