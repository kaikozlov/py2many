"""Rust emission helpers shared by the pyrs transpiler."""

from __future__ import annotations

import re
from typing import Iterable

# Identifiers that must use Rust raw identifier syntax (r#name).
RUST_RAW_IDENT_KEYWORDS = frozenset(
    {
        "abstract",
        "as",
        "async",
        "await",
        "become",
        "box",
        "break",
        "const",
        "continue",
        "crate",
        "do",
        "dyn",
        "else",
        "enum",
        "extern",
        "false",
        "final",
        "fn",
        "for",
        "if",
        "impl",
        "in",
        "let",
        "loop",
        "macro",
        "match",
        "mod",
        "move",
        "mut",
        "override",
        "priv",
        "pub",
        "ref",
        "return",
        "static",
        "struct",
        "super",
        "trait",
        "true",
        "try",
        "type",
        "typeof",
        "unsafe",
        "unsized",
        "use",
        "virtual",
        "where",
        "while",
        "yield",
    }
)

# Names that must never be escaped.
RUST_IDENT_EXCEPTIONS = frozenset({"self", "Self"})


def escape_rust_ident(name: str) -> str:
    if name in RUST_IDENT_EXCEPTIONS:
        return name
    if name in RUST_RAW_IDENT_KEYWORDS:
        return f"r#{name}"
    return name


def sanitize_rust_module_name(name: str) -> str:
    if not name or name in {".", "__init__"}:
        return ""
    return name.replace("-", "_")


def _needs_raw_rust_string(value: str) -> bool:
    if "\\" not in value:
        return False
    # Regex and path-like strings are safest as raw literals.
    if re.search(r"\\[sSdDwWbBnrt0-9.$^[\]()|+*?{}]", value):
        return True
    if re.search(r"\\u[0-9a-fA-F]{4}", value):
        return True
    if re.search(r"\\x[0-9a-fA-F]{2}", value):
        return True
    return True


def _raw_rust_string(value: str) -> str:
    hash_count = 0
    while True:
        delimiter = '"' + ("#" * hash_count)
        end = ("#" * hash_count) + '"'
        if delimiter not in value and end not in value:
            hashes = "#" * hash_count
            return f"r{hashes}\"{value}\"{hashes}"
        hash_count += 1


def _escape_normal_rust_string(value: str) -> str:
    parts: list[str] = []
    index = 0
    while index < len(value):
        char = value[index]
        if char == "\\" and index + 1 < len(value):
            next_char = value[index + 1]
            if next_char == "u" and index + 5 < len(value):
                hex_digits = value[index + 2 : index + 6]
                if len(hex_digits) == 4 and all(c in "0123456789abcdefABCDEF" for c in hex_digits):
                    parts.append(f"\\u{{{hex_digits}}}")
                    index += 6
                    continue
            if next_char == "x" and index + 3 < len(value):
                hex_digits = value[index + 2 : index + 4]
                if len(hex_digits) == 2 and all(c in "0123456789abcdefABCDEF" for c in hex_digits):
                    parts.append(f"\\x{hex_digits}")
                    index += 4
                    continue
        if char == "\\":
            parts.append("\\\\")
        elif char == '"':
            parts.append('\\"')
        elif char == "\n":
            parts.append("\\n")
        elif char == "\r":
            parts.append("\\r")
        elif char == "\t":
            parts.append("\\t")
        else:
            parts.append(char)
        index += 1
    return "".join(parts)


def rust_string_literal(value: str) -> str:
    if _needs_raw_rust_string(value):
        return _raw_rust_string(value)
    return f'"{_escape_normal_rust_string(value)}"'


def parenthesize_cast_expr(expr: str) -> str:
    stripped = expr.strip()
    if " as " not in stripped:
        return expr
    if stripped.startswith("(") and stripped.endswith(")"):
        inner = stripped[1:-1].strip()
        if inner.count("(") == inner.count(")"):
            return expr
    return f"({expr})"


def chained_compare_parts(
    left_expr: str,
    ops: Iterable[str],
    comparator_exprs: Iterable[str],
) -> str:
    parts = []
    left = left_expr
    for op, right in zip(ops, comparator_exprs):
        parts.append(f"{parenthesize_cast_expr(left)} {op} {parenthesize_cast_expr(right)}")
        left = right
    if len(parts) == 1:
        return parts[0]
    return " && ".join(f"({part})" for part in parts)
