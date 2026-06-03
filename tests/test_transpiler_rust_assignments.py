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
    generated = rust_transpile("""
class Action:
    name = "Action"

    def genesis(self):
        m = self.menu
        return m
""")

    assert "let m = self.menu;" in generated
    assert "pub const m" not in generated


def test_class_method_tuple_destructuring_uses_let_pattern():
    generated = rust_transpile("""
class Action:
    def genesis(self):
        is_drm_free, is_image_based = self.status_cache[file_name][1]
""")

    assert "let (is_drm_free, is_image_based)" in generated
    assert "pub const (is_drm_free, is_image_based)" not in generated


def test_global_tuple_constant_has_explicit_tuple_type():
    generated = rust_transpile("version = (2, 33, 0)\n")

    assert "pub const version: (i32, i32, i32) = (2, 33, 0);" in generated


def test_class_tuple_constant_has_explicit_tuple_type():
    generated = rust_transpile("""
class Action:
    minimum_calibre_version = (5, 0, 0)
""")

    assert (
        "pub const minimum_calibre_version: (i32, i32, i32) = (5, 0, 0);" in generated
    )


def test_module_level_subscript_assignment_is_wrapped_in_init_function():
    generated = rust_transpile("""
plugin_config = JSONConfig("plugins/KFX Input")
plugin_config.defaults[DesaturateNotebooks] = False
""")

    assert (
        'pub const plugin_config: TODO_py2many_unknown = JSONConfig("plugins/KFX Input");'
        in generated
    )
    assert "pub fn __module_init_3()" in generated
    assert "plugin_config.defaults[DesaturateNotebooks] = false;" in generated


def test_percent_string_formatting_with_single_value_uses_format_macro():
    generated = rust_transpile("""
def describe(name):
    return "hello %s" % name
""")

    assert 'return format!("hello {}", name);' in generated


def test_percent_string_formatting_with_tuple_values_uses_format_macro():
    generated = rust_transpile("""
def describe(name, count):
    return "%s has %d books" % (name, count)
""")

    assert 'return format!("{} has {} books", name, count);' in generated


def test_f_string_uses_format_macro():
    generated = rust_transpile("""
def describe(name, count):
    return f"{name} has {count} books"
""")

    assert 'return format!("{} has {} books", name, count);' in generated


def test_try_except_preserves_handler_body_without_unsupported_marker():
    generated = rust_transpile("""
def load(log):
    try:
        work()
    except Exception as err:
        log.error(err)
""")

    assert "unsupported exception handler" not in generated
    assert "Err(err)" in generated
    assert "log.error(err);" in generated


def test_raise_emits_err_without_unsupported_marker():
    generated = rust_transpile("""
def load():
    raise Exception("bad")
""")

    assert "raise!(" not in generated
    assert "//unsupported" not in generated
    assert 'return Err(Exception("bad").into());' in generated


def test_isinstance_uses_rust_helper_not_python_builtin():
    generated = rust_transpile("""
def check(value):
    return isinstance(value, str)
""")

    assert "isinstance(" not in generated
    assert "is_instance::<str>(&value)" in generated


def test_hasattr_uses_rust_helper_not_python_builtin():
    generated = rust_transpile("""
def check(value):
    return hasattr(value, "name")
""")

    assert "hasattr(" not in generated
    assert 'has_attr(&value, "name")' in generated


def test_init_method_generates_new_constructor_name():
    generated = rust_transpile("""
class Item:
    def __init__(self, name):
        self.name = name
""")

    assert "pub fn __init__" not in generated
    assert "pub fn new" in generated


def test_unknown_public_field_type_uses_todo_placeholder_not_underscore():
    generated = rust_transpile("""
class Item:
    def __init__(self, name):
        self.name = name
""")

    assert "pub name: _" not in generated
    assert "TODO_py2many_unknown" in generated


def test_regex_module_import_maps_to_regex_crate():
    generated = rust_transpile("""
import re

def check(value):
    return re.match("abc", value)
""")

    assert "extern crate re;" not in generated
    assert "use regex::Regex;" in generated
    assert 'Regex::new("abc").unwrap().is_match(&value)' in generated


def test_python_format_method_uses_format_macro():
    generated = rust_transpile("""
def describe(value):
    return "{:,}".format(value)
""")

    assert '"{:,}".format(value)' not in generated
    assert 'format!("{}", value)' in generated


def test_starred_args_do_not_emit_unsupported_marker():
    generated = rust_transpile("""
def call(args):
    target(*args)
""")

    assert "unsupported" not in generated
    assert "starred!(args)" in generated
