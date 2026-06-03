from argparse import Namespace
from pathlib import Path

from py2many.cli import _transpile
from py2many.pyrs import settings as rust_settings


def rust_transpile(source: str) -> str:
    args = Namespace(
        typpete=False,
        extension=False,
        no_prologue=False,
        llm=False,
    )
    settings = rust_settings(args)
    return _transpile([Path("case.py")], [source], settings, args)[0][0]


def test_class_method_locals_are_not_class_constants():
    generated = rust_transpile(
        """
class Action:
    name = "Action"

    def genesis(self):
        m = self.menu
        return m
"""
    )

    assert "let m = self.menu;" in generated
    assert "pub const m" not in generated


def test_class_method_tuple_destructuring_uses_let_pattern():
    generated = rust_transpile(
        """
class Action:
    def genesis(self):
        is_drm_free, is_image_based = self.status_cache[file_name][1]
"""
    )

    assert "let (is_drm_free, is_image_based)" in generated
    assert "pub const (is_drm_free, is_image_based)" not in generated


def test_global_tuple_constant_has_explicit_tuple_type():
    generated = rust_transpile("version = (2, 33, 0)\n")

    assert "pub const version: (i32, i32, i32) = (2, 33, 0);" in generated


def test_class_tuple_constant_has_explicit_tuple_type():
    generated = rust_transpile(
        """
class Action:
    minimum_calibre_version = (5, 0, 0)
"""
    )

    assert "pub const minimum_calibre_version: (i32, i32, i32) = (5, 0, 0);" in generated


def test_module_level_subscript_assignment_is_wrapped_in_init_function():
    generated = rust_transpile(
        """
plugin_config = JSONConfig("plugins/KFX Input")
plugin_config.defaults[DesaturateNotebooks] = False
"""
    )

    assert "pub const plugin_config: _ = JSONConfig(\"plugins/KFX Input\");" in generated
    assert "pub fn __module_init_3()" in generated
    assert "plugin_config.defaults[DesaturateNotebooks] = false;" in generated
