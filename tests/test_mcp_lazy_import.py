from __future__ import annotations

import subprocess
import sys

import pytest

pytestmark = pytest.mark.offline


def test_paperqa_and_mcp_module_import_without_mcp_extra() -> None:
    code = """
import builtins

original_import = builtins.__import__

def guarded_import(name, *args, **kwargs):
    if name == "mcp" or name.startswith("mcp."):
        raise AssertionError("MCP was imported eagerly")
    return original_import(name, *args, **kwargs)

builtins.__import__ = guarded_import

import paperqa
import paperqa.mcp_server
"""
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", code],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
