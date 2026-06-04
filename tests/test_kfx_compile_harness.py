"""Regression tests for the kfxlib compile harness and scan gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HARNESS = ROOT / "scripts" / "check_transpiled_kfxlib.py"
TRANSPILER_TESTS = ROOT / "py2many" / "tests" / "test_transpiler_rust_assignments.py"


def test_compile_harness_scan_reports_no_python_api_leaks():
    result = subprocess.run(
        [sys.executable, str(HARNESS), "--scan-only"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    summary = result.stdout
    assert "append_leak: 0" in summary
    assert "re_sub_leak: 0" in summary
    assert "getvalue_leak: 0" in summary


def test_compile_harness_batches_and_full_crate_pass():
    for batch in ("1", "2", "3", "4"):
        result = subprocess.run(
            [sys.executable, str(HARNESS), "--batch", batch],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr

    result = subprocess.run(
        [sys.executable, str(HARNESS)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_transpiler_regression_suite_still_passes():
    result = subprocess.run(
        [
            "uv",
            "run",
            "--extra",
            "test",
            "pytest",
            str(TRANSPILER_TESTS),
            "-q",
        ],
        cwd=ROOT / "py2many",
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
