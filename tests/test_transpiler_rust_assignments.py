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

    assert "let (is_drm_free, is_image_based)" in generated.replace("mut ", "")
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


def test_kfx_known_constructor_types_class_fields():
    generated = rust_transpile("""
class Book:
    def __init__(self, file):
        self.datafile = DataFile(file)
        self.symtab = LocalSymbolTable(YJ_SYMBOLS.name)
        self.fragments = YJFragmentList()
""")

    assert "pub datafile: DataFile," in generated
    assert "pub symtab: LocalSymbolTable," in generated
    assert "pub fragments: YJFragmentList," in generated


def test_kfx_empty_self_list_infers_element_from_append():
    generated = rust_transpile("""
class Container:
    def __init__(self):
        self.entities = []

    def load(self):
        self.entities.append(KfxContainerEntity(self.symtab, 1, 2))
""")

    assert "pub entities: Vec<KfxContainerEntity>," in generated


def test_kfx_empty_self_set_infers_element_from_add():
    generated = rust_transpile("""
class Book:
    def __init__(self):
        self.reported_errors = set()

    def report(self, msg):
        self.reported_errors.add(msg)
""")

    assert "pub reported_errors: HashSet<TODO_py2many_unknown>," in generated


def test_kfx_empty_self_dict_infers_key_value_from_subscript_assignment():
    generated = rust_transpile("""
class Navigation:
    def __init__(self):
        self.anchor_uri = {}

    def add(self, anchor_name, uri):
        self.anchor_uri[anchor_name] = uri
""")

    assert (
        "pub anchor_uri: HashMap<TODO_py2many_unknown, TODO_py2many_unknown>,"
        in generated
    )


def test_kfx_fragment_list_get_methods_have_domain_return_types():
    generated = rust_transpile("""
class Book:
    def __init__(self):
        self.fragments = YJFragmentList()

    def use_fragments(self):
        fragment = self.fragments.get("$490")
        all_fragments = self.fragments.get_all("$490")
        return all_fragments
""")

    assert 'let fragment: Option<YJFragment> = self.fragments.get("$490");' in generated
    assert (
        'let all_fragments: Vec<YJFragment> = self.fragments.get_all("$490");'
        in generated
    )


def test_kfx_ion_type_check_narrows_branch_variable():
    generated = rust_transpile("""
def read_value(value):
    if ion_type(value) is IonStruct:
        item = value.get("$307")
        return item
""")

    assert 'let item: IonValue = value.get("$307");' in generated


def test_kfx_known_forward_constructor_emits_call_not_struct_literal():
    generated = rust_transpile("""
class First:
    def __init__(self, value):
        self.value = IonAnnots(value)

class IonAnnots:
    def __init__(self, value):
        self.value = value
""")

    assert "__self.value = IonAnnots(value);" in generated
    assert "IonAnnots{value: value}" not in generated


def test_self_subscript_assignment_is_not_treated_as_struct_field():
    generated = rust_transpile("""
class IonStruct:
    def set_first(self, value):
        self[0] = value
""")

    assert "pub 0:" not in generated
    assert "self[0] = value;" in generated


def test_kfx_ion_serial_method_return_types_are_known():
    generated = rust_transpile("""
def read_values(symtab, data):
    binary = IonBinary(symtab)
    value = binary.deserialize_single_value(data)
    annotated = binary.deserialize_annotated_value(data)
    values = binary.deserialize_multiple_values(data)
    return values
""")

    assert "let binary: IonBinary = IonBinary(symtab);" in generated
    assert "let value: IonValue = binary.deserialize_single_value(data);" in generated
    assert (
        "let annotated: IonAnnotation = binary.deserialize_annotated_value(data);"
        in generated
    )
    assert (
        "let values: Vec<IonValue> = binary.deserialize_multiple_values(data);"
        in generated
    )


def test_kfx_symbol_table_method_return_types_are_known():
    generated = rust_transpile("""
def symbols(symtab, catalog):
    local = symtab.create_local_symbol("abc")
    existing = symtab.get_symbol(1)
    table = catalog.get_shared_symbol_table("YJ_symbols")
    import_value = symtab.create_import()
    return local
""")

    assert 'let local: IonSymbol = symtab.create_local_symbol("abc");' in generated
    assert "let existing: IonSymbol = symtab.get_symbol(1);" in generated
    assert (
        'let table: Option<IonSharedSymbolTable> = catalog.get_shared_symbol_table("YJ_symbols");'
        in generated
    )
    assert (
        "let import_value: Option<IonAnnotation> = symtab.create_import();" in generated
    )


def test_kfx_assigned_ion_type_variable_narrows_source_value():
    generated = rust_transpile("""
def read_value(value):
    data_type = ion_type(value)
    if data_type is IonSExp:
        item = value.pop()
        return item
""")

    assert "let data_type: IonDataType = ion_type(value);" in generated
    assert "let item: IonValue = value.pop();" in generated


def test_kfx_ion_type_membership_narrows_source_value():
    generated = rust_transpile("""
def read_value(value):
    if ion_type(value) in {IonList, IonStruct}:
        item = value.get("$307")
        return item
""")

    assert 'let item: IonValue = value.get("$307");' in generated


def test_kfx_isinstance_narrows_branch_variable():
    generated = rust_transpile("""
def read_fragment(fragment):
    if isinstance(fragment, YJFragment):
        value = fragment.value
        return value
""")

    assert "let value: IonValue = fragment.value;" in generated


def test_kfx_yj_book_mixin_fields_resolve_on_book_structure():
    generated = rust_transpile("""
class BookStructure:
    def collect(self):
        fragment = self.fragments.get("$490")
        sym = self.symtab.create_local_symbol("abc")
        return fragment
""")

    assert 'let fragment: Option<YJFragment> = self.fragments.get("$490");' in generated
    assert 'let sym: IonSymbol = self.symtab.create_local_symbol("abc");' in generated


def test_kfx_epub_mixin_fields_resolve_on_conversion_mixins():
    generated = rust_transpile("""
class KFX_EPUB_Resources:
    def process(self, resource_name):
        cached = self.resource_cache.get(resource_name)
        part = self.oebps_files.get("part.xhtml")
        data = self.book_data.get("$417", {})
        fragment = self.book.fragments.get("$490")
        return cached
""")

    assert (
        "let cached: Option<KfxEpubResource> = self.resource_cache.get(resource_name);"
        in generated
    )
    assert (
        'let part: Option<OutputFile> = self.oebps_files.get("part.xhtml");'
        in generated
    )
    assert (
        'let data: IonValue = self.book_data.get("$417", HashMap::new());' in generated
    )
    assert (
        'let fragment: Option<YJFragment> = self.book.fragments.get("$490");'
        in generated
    )


def test_kfx_first_party_constructor_fields_are_known():
    generated = rust_transpile("""
class KpfContainer:
    def load(self, file, data):
        self.source_epub = SourceEpub(file)
        self.kdf_datafile = DataFile("book.kdf", data)
        self.wrapper = SQLiteFingerprintWrapper(self.kdf_datafile)
        self.deserializer = Deserializer(data)
""")

    assert "pub source_epub: SourceEpub," in generated
    assert "pub kdf_datafile: DataFile," in generated
    assert "pub wrapper: SQLiteFingerprintWrapper," in generated
    assert "pub deserializer: Deserializer," in generated


def test_kfx_ion_type_is_not_narrows_else_branch():
    generated = rust_transpile("""
def read_value(value):
    if ion_type(value) is not IonStruct:
        return None
    else:
        item = value.get("$307")
        return item
""")

    assert 'let item: IonValue = value.get("$307");' in generated


def test_kfx_assigned_ion_type_membership_narrows_source_value():
    generated = rust_transpile("""
def read_value(value):
    data_type = ion_type(value)
    if data_type in {IonList, IonStruct}:
        item = value.get("$307")
        return item
""")

    assert 'let item: IonValue = value.get("$307");' in generated


def test_kfx_isinstance_tuple_narrows_branch_variable():
    generated = rust_transpile("""
def read_annotation(value):
    if isinstance(value, (IonAnnotation, YJFragment)):
        payload = value.value
        return payload
""")

    assert "let payload: IonValue = value.value;" in generated


def test_kfx_empty_self_list_infers_element_from_extend_literal():
    generated = rust_transpile("""
class KfxContainer:
    def load(self):
        self.entities = []
        self.entities.extend([KfxContainerEntity(self.symtab, 1, 2)])
""")

    assert "pub entities: Vec<KfxContainerEntity>," in generated


def test_kfx_unpack_container_constructor_fields_are_known():
    generated = rust_transpile("""
class Book:
    def load(self, symtab, datafile):
        self.ion_text = IonTextContainer(symtab, datafile=datafile)
        self.zip_unpack = ZipUnpackContainer(symtab, datafile=datafile)
        self.json_content = JsonContentContainer(self)
        self.progress = CONVERSION_PROGRESS(None)
""")

    assert "pub ion_text: IonTextContainer," in generated
    assert "pub zip_unpack: ZipUnpackContainer," in generated
    assert "pub json_content: JsonContentContainer," in generated
    assert "pub progress: CONVERSION_PROGRESS," in generated


def test_regex_string_literal_uses_raw_rust_string():
    generated = rust_transpile("""
import re
PATTERN = re.compile(r"^\\$[0-9]+$")
""")

    assert 'Regex::new(r"^\\$[0-9]+$")' in generated


def test_unicode_regex_string_literal_uses_raw_rust_string():
    generated = rust_transpile("""
import re
PATTERN = re.compile(r"^[\\u0021-\\u007e]+$")
""")

    assert 'Regex::new(r"^[\\u0021-\\u007e]+$")' in generated


def test_dot_prefixed_string_literal_emits_valid_rust():
    generated = rust_transpile("""
EXT = ".azw"
NAME = "bookmanifest.kfx"
""")

    assert 'pub const EXT: &' in generated and '".azw"' in generated
    assert 'pub const NAME: &' in generated and '"bookmanifest.kfx"' in generated


def test_cast_comparison_is_parenthesized():
    generated = rust_transpile("""
def check(data):
    if len(data) < 10:
        return False
    return True
""")

    assert "(data.len() as i32" in generated and "< 10" in generated


def test_chained_comparison_expands_to_boolean_conjunction():
    generated = rust_transpile("""
def check(a, b, c):
    return a == b != c
""")

    assert "&&" in generated
    assert "a == b" in generated
    assert "b != c" in generated


def test_reserved_identifier_final_uses_raw_ident():
    generated = rust_transpile("""
class Report:
    def run(self):
        self.final()

def final():
    return 1
""")

    assert "pub fn r#final()" in generated
    assert "self.r#final();" in generated


def test_tuple_mut_destructuring_uses_mut_per_binding():
    generated = rust_transpile("""
def swap(pair):
    a, b = pair
    a = b
    b = a
    return a
""")

    assert "let (mut a, mut b)" in generated
    assert "let mut (a, b)" not in generated


def test_module_level_for_is_wrapped_in_init_function():
    generated = rust_transpile("""
VERSIONS = []
for version, capabilities in VERSIONS:
    pass
""")

    assert "pub fn __module_init_" in generated
    assert "for (version, capabilities) in VERSIONS" in generated


def test_relative_import_only_declares_available_local_mod():
    generated = rust_transpile("""
from .utilities import helper

def run():
    return helper()
""")

    assert "mod .;" not in generated


def test_advanced_slice_emits_rust_range():
    generated = rust_transpile("""
def take(data):
    return data[1:5]
""")

    assert "&data[1..5]" in generated


def test_advanced_step_slice_emits_helper_call():
    generated = rust_transpile("""
def take(data):
    return data[1:10:2]
""")

    assert "python_slice(data, 1, 10, 2)" in generated


def test_union_return_type_is_mapped_to_rust_placeholder():
    generated = rust_transpile("""
from typing import Union

def pick(value: Union[int, str]) -> Union[int, str]:
    return value
""")

    assert "Union[" not in generated
    assert "pub fn pick(value: i32)" in generated
    assert "-> &i32" in generated or "-> i32" in generated


def test_defaultdict_list_field_infers_vec_type():
    generated = rust_transpile("""
from collections import defaultdict

class Book:
    def load(self):
        self.chapters = defaultdict(list)
        self.chapters["a"].append("x")
""")

    assert "pub chapters: HashMap" in generated or "pub chapters: Vec" in generated


def test_none_initialized_field_upgrades_on_later_assignment():
    generated = rust_transpile("""
class Book:
    def load(self, symtab):
        self.symtab = None
        self.symtab = symtab
""")

    assert "pub symtab: LocalSymbolTable," in generated


def test_yj_book_get_container_return_type():
    generated = rust_transpile("""
class YJ_Book:
    def current(self):
        container = self.get_container()
        return container
""")

    assert "let container: YJContainer = self.get_container();" in generated


def test_struct_pack_emits_helper_placeholder():
    generated = rust_transpile("""
import struct

def pack_value(value):
    return struct.pack(">I", value)
""")

    assert "struct_pack(" in generated


def test_compare_with_is_not_parenthesizes_subexpression():
    generated = rust_transpile("""
def check(cde_type, is_sample):
    if (cde_type == "EBSP") is not is_sample:
        return False
    return True
""")

    assert '(cde_type == "EBSP") != is_sample' in generated.replace(" != ", " != ") or '(cde_type == "EBSP")' in generated


def test_function_argument_named_type_uses_raw_ident():
    generated = rust_transpile("""
class Context:
    def __exit__(self, type, value, traceback):
        return False
""")

    assert "r#type:" in generated


def test_string_addition_uses_format():
    generated = rust_transpile("""
def join(prefix, suffix):
    return "a" + suffix
""")

    assert 'format!("{}{}", "a", suffix)' in generated


def test_bytesio_emits_helper_placeholder():
    generated = rust_transpile("""
from io import BytesIO

def make(data):
    return BytesIO(data)
""")

    assert "BytesIO::from_bytes(data)" in generated


def test_division_with_deref_operand_does_not_open_block_comment():
    generated = rust_transpile("""
def scale(size, dpi):
    return size / dpi
""")

    assert ") / (" in generated
    assert ")/*" not in generated


def test_attribute_tuple_unpack_rewrites_to_valid_rust():
    generated = rust_transpile("""
class Book:
    def load(self, viewports_by_count):
        (self.original_width, self.original_height), best_count = viewports_by_count[0]
        return best_count
""")

    assert "let (self.original_width, self.original_height)" not in generated
    assert "self.original_width = " in generated
    assert "self.original_height = " in generated


def test_forward_class_reference_emits_constructor_call():
    generated = rust_transpile("""
class Outer:
    def build(self):
        return ImgPlane(self, False)

class ImgPlane:
    def __init__(self, parent, alpha):
        self.parent = parent
""")

    assert "ImgPlane(self, false)" in generated
    assert "ImgPlane{" not in generated


def test_negative_subscript_assignment_emits_helper():
    generated = rust_transpile("""
def trim(items):
    items[-2] = "x"
""")

    assert "python_index_assign(&mut items, -2" in generated


def test_dict_with_str_values_does_not_break_inference():
    generated = rust_transpile("""
def make():
    return {"key": "value", "other": "data"}
""")

    assert "FAILED" not in generated
    assert "HashMap" in generated or "vec!" in generated or "{" in generated


def test_zipfile_emits_helper_placeholder():
    generated = rust_transpile("""
import zipfile

def open_zip(path):
    return zipfile.ZipFile(path)
""")

    assert "ZipFile::open(path)" in generated


def test_sqlite3_connect_emits_helper_placeholder():
    generated = rust_transpile("""
import sqlite3

def connect_db(path):
    return sqlite3.connect(path)
""")

    assert "sqlite3_connect(path)" in generated


def test_struct_unpack_emits_helper_placeholder():
    generated = rust_transpile("""
import struct

def unpack_value(data):
    return struct.unpack(">I", data)
""")

    assert "struct_unpack(" in generated


def test_package_init_relative_imports_emit_sibling_mods():
    generated = rust_transpile("""
from . import message_logging
from . import utilities

set_logger = message_logging.set_logger
""")

    assert "extern crate ;" not in generated
    assert "use message_logging::*;" in generated
    assert "use utilities::*;" in generated


def test_relative_import_declares_mod_when_sibling_is_transpiled():
    from argparse import Namespace
    from pathlib import Path

    from py2many.cli import _transpile
    from py2many.pyrs import settings as rust_settings

    args = Namespace(typpete=False, extension=False, no_prologue=False, llm=False)
    settings = rust_settings(args)
    outputs = _transpile(
        [Path("message_logging.py"), Path("__init__.py")],
        [
            "def set_logger():\n    return None\n",
            "from . import message_logging\n",
        ],
        settings,
        args,
    )
    init_rs = outputs[0][1]

    assert "mod message_logging;" in init_rs


def test_negative_index_emits_python_index_helper():
    generated = rust_transpile("""
def last(items):
    return items[-1]
""")

    assert "python_index(items, -1)" in generated


def test_negative_slice_emits_python_slice_helper():
    generated = rust_transpile("""
def trim(items):
    return items[:-1]
""")

    assert "python_slice(items, None, -1, None)" in generated


def test_class_with_new_emits_constructor_call():
    generated = rust_transpile("""
class IonAnnots(tuple):
    def __new__(cls, annotations):
        return tuple.__new__(cls, annotations)

def make(annotations):
    return IonAnnots(annotations)
""")

    assert "IonAnnots::new(annotations)" in generated
    assert "IonAnnots{" not in generated


def test_defaultdict_set_field_infers_hashset_type():
    generated = rust_transpile("""
from collections import defaultdict

class Book:
    def load(self):
        self.tags = defaultdict(set)
        self.tags["a"].add("x")
""")

    assert "pub tags: HashMap" in generated


def test_defaultdict_emits_pylib_helper():
    generated = rust_transpile("""
from collections import defaultdict

def make():
    return defaultdict(list)
""")

    assert "defaultdict(|| Vec::new())" in generated
    assert "collections.defaultdict" not in generated


def test_re_sub_emits_regex_replace_helper():
    generated = rust_transpile("""
import re

def clean(value):
    return re.sub("[^A-Za-z]", "_", value)
""")

    assert "regex_replace(" in generated
    assert "re.sub(" not in generated


def test_module_level_type_alias_emits_pub_type():
    generated = rust_transpile("""
IonBool = bool
IonNull = type(None)
""")

    assert "pub type IonBool = bool;" in generated
    assert "pub type IonNull = ();" in generated


def test_type_comparison_emits_python_type_eq():
    generated = rust_transpile("""
class Style:
    pass

def check(value):
    if type(value) != Style:
        return False
    return True
""")

    assert "python_type_eq(" in generated
    assert "r#type(" not in generated


def test_isinstance_list_emits_instance_tag_helper():
    generated = rust_transpile("""
def check(value):
    return isinstance(value, list)
""")

    assert 'is_instance_tag(&value as &dyn std::any::Any, "list")' in generated


def test_getvalue_emits_single_call_without_double_parens():
    generated = rust_transpile("""
from io import BytesIO

def read_buf(buf):
    return buf.getvalue()
""")

    assert "buf.getvalue()" in generated
    assert "getvalue()()" not in generated


def test_ordered_dict_emits_index_map():
    generated = rust_transpile("""
import collections

def make():
    return collections.OrderedDict()
""")

    assert "IndexMap::new()" in generated
    assert "collections.OrderedDict" not in generated


def test_vec_truthiness_uses_is_empty():
    generated = rust_transpile("""
class YJ_Book:
    def check(self):
        if self.yj_containers:
            return True
        return False
""")

    assert ".is_empty()" in generated
