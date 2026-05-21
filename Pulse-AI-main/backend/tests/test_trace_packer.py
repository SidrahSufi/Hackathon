"""Tests for the trace zip packer."""
from __future__ import annotations

import sys
import zipfile
from io import BytesIO
from pathlib import Path

import pytest

_repo_root = Path(__file__).resolve().parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))
_backend_root = Path(__file__).resolve().parent.parent
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

from api.trace_packer import pack_trace  # noqa: E402


def test_pack_trace_for_existing_run():
    # r-final-1 was produced by the smoke run in the previous step.
    blob = pack_trace("r-final-1")
    zf = zipfile.ZipFile(BytesIO(blob))
    names = zf.namelist()
    assert any(n.endswith("outcome.json") for n in names)
    assert any(n.endswith("metadata.json") for n in names)


def test_pack_trace_for_unknown_run_raises():
    with pytest.raises(FileNotFoundError):
        pack_trace("r-does-not-exist-99")
