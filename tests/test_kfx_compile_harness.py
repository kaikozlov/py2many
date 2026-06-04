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


def test_compile_harness_writes_generated_bodies_as_real_modules(tmp_path):
    src_dir = tmp_path / "generated"
    src_dir.mkdir()
    (src_dir / "simple.rs").write_text(
        "pub fn generated_value() -> i32 {\n    7\n}\n",
        encoding="utf-8",
    )
    crate_dir = tmp_path / "crate"

    result = subprocess.run(
        [
            sys.executable,
            str(HARNESS),
            "--src",
            str(src_dir),
            "--keep",
            str(crate_dir),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    module_text = (crate_dir / "src" / "simple.rs").read_text(encoding="utf-8")
    assert "__PY2MANY_SOURCE" not in module_text
    assert "pub fn generated_value() -> i32" in module_text


def test_compile_harness_rewrites_local_imports_without_rewriting_external_crates(tmp_path):
    src_dir = tmp_path / "generated"
    src_dir.mkdir()
    (src_dir / "helper.rs").write_text(
        "pub fn generated_value() -> i32 {\n    7\n}\n",
        encoding="utf-8",
    )
    (src_dir / "uses_helper.rs").write_text(
        "\n".join(
            [
                "use helper::generated_value;",
                "use once_cell::sync::Lazy;",
                "",
                "pub static GENERATED_VALUE: Lazy<i32> = Lazy::new(|| generated_value());",
                "",
                "pub fn read_generated_value() -> i32 {",
                "    *GENERATED_VALUE",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    crate_dir = tmp_path / "crate"

    result = subprocess.run(
        [
            sys.executable,
            str(HARNESS),
            "--src",
            str(src_dir),
            "--keep",
            str(crate_dir),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    module_text = (crate_dir / "src" / "uses_helper.rs").read_text(encoding="utf-8")
    assert "use crate::helper::generated_value;" in module_text
    assert "use once_cell::sync::Lazy;" in module_text


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
