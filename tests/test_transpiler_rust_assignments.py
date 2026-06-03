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
