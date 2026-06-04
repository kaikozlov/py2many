import ast
from typing import Dict, Optional, Tuple

from py2many.analysis import get_id

TODO_TYPE = "TODO_py2many_unknown"


CONSTRUCTOR_TYPES = {
    "CONVERSION_PROGRESS": "CONVERSION_PROGRESS",
    "ContentChunk": "ContentChunk",
    "DataFile": "DataFile",
    "Deserializer": "Deserializer",
    "IonBinary": "IonBinary",
    "IonAnnots": "IonAnnots",
    "IonAnnotation": "IonAnnotation",
    "IonBLOB": "IonBLOB",
    "IonCLOB": "IonCLOB",
    "IonNop": "IonNop",
    "IonSExp": "IonSExp",
    "IonStruct": "IonStruct",
    "IonSymbol": "IonSymbol",
    "IonText": "IonText",
    "IonTextContainer": "IonTextContainer",
    "IonTextFile": "IonTextFile",
    "IonTimestamp": "IonTimestamp",
    "IonTimestampTZ": "IonTimestampTZ",
    "IonSharedSymbolTable": "IonSharedSymbolTable",
    "IS": "IonSymbol",
    "JsonContentContainer": "JsonContentContainer",
    "KfxContainer": "KfxContainer",
    "KfxContainerEntity": "KfxContainerEntity",
    "KpfContainer": "KpfContainer",
    "LocalSymbolTable": "LocalSymbolTable",
    "MatchReport": "MatchReport",
    "Serializer": "Serializer",
    "SourceEpub": "SourceEpub",
    "SQLiteFingerprintWrapper": "SQLiteFingerprintWrapper",
    "SymbolTableCatalog": "SymbolTableCatalog",
    "SymbolTableImport": "SymbolTableImport",
    "YJFragment": "YJFragment",
    "YJFragmentKey": "YJFragmentKey",
    "YJFragmentList": "YJFragmentList",
    "ZipUnpackContainer": "ZipUnpackContainer",
    "Style": "Style",
    "ImgPlane": "ImgPlane",
    "OutputFile": "OutputFile",
    "KfxEpubResource": "KfxEpubResource",
    "BookPart": "BookPart",
    "GuideEntry": "GuideEntry",
    "ManifestEntry": "ManifestEntry",
    "TocEntry": "TocEntry",
    "PageMapEntry": "PageMapEntry",
    "JxrImage": "JxrImage",
    "JxrMisc": "JxrMisc",
    "JxrContainer": "JxrContainer",
}


METHOD_RETURNS = {
    ("DataFile", "get_data"): "Vec<u8>",
    ("IonAnnotation", "verify_annotation"): "IonAnnotation",
    ("IonBinary", "deserialize_single_value"): "IonValue",
    ("IonBinary", "deserialize_annotated_value"): "IonAnnotation",
    ("IonBinary", "deserialize_multiple_values"): "Vec<IonValue>",
    ("IonText", "deserialize_single_value"): "IonValue",
    ("IonText", "deserialize_annotated_value"): "IonAnnotation",
    ("IonText", "deserialize_multiple_values"): "Vec<IonValue>",
    ("IonText", "serialize_multiple_values"): "Vec<u8>",
    ("IonText", "serialize_single_value"): "Vec<u8>",
    ("IonSerial", "serialize_single_value"): "Vec<u8>",
    ("IonSerial", "serialize_multiple_values"): "Vec<u8>",
    ("IonBinary", "serialize_single_value"): "Vec<u8>",
    ("IonBinary", "serialize_multiple_values"): "Vec<u8>",
    ("IonBinary", "deserialize_multiple_values"): "Vec<IonValue>",
    ("Token", "classify"): "String",
    ("Token", "__repr__"): "String",
    ("KfxContainerEntity", "deserialize"): "YJFragment",
    ("LocalSymbolTable", "create_import"): "Option<IonAnnotation>",
    ("LocalSymbolTable", "create_local_symbol"): "IonSymbol",
    ("LocalSymbolTable", "get_symbol"): "IonSymbol",
    ("Serializer", "serialize"): "Vec<u8>",
    ("Serializer", "sha1"): "Vec<u8>",
    ("SymbolTableCatalog", "get_shared_symbol_table"): "Option<IonSharedSymbolTable>",
    ("YJContainer", "get_fragments"): "YJFragmentList",
    ("KfxContainer", "get_fragments"): "YJFragmentList",
    ("KpfContainer", "get_fragments"): "YJFragmentList",
    ("YJFragmentList", "get"): "Option<YJFragment>",
    ("YJFragmentList", "get_all"): "Vec<YJFragment>",
    ("YJFragmentList", "filtered"): "YJFragmentList",
    ("IonStruct", "__getitem__"): "IonValue",
    ("IonStruct", "get"): "IonValue",
    ("IonStruct", "pop"): "IonValue",
    ("IonList", "pop"): "IonValue",
    ("IonSExp", "pop"): "IonValue",
    ("HashMap<IonSymbol, IonValue>", "get"): "IonValue",
    ("HashMap<IonSymbol, IonValue>", "pop"): "IonValue",
    ("HashMap<IonSymbol, HashMap<IonSymbol, IonValue>>", "get"): "IonValue",
    ("HashMap<String, KfxEpubResource>", "get"): "Option<KfxEpubResource>",
    ("HashMap<String, OutputFile>", "get"): "Option<OutputFile>",
    ("YJ_Book", "get_container"): "YJContainer",
    ("YJ_Book", "get_fragment"): "IonValue",
    ("YJ_Book", "get_named_fragment"): "IonValue",
    ("KFX_EPUB", "get_fragment"): "IonValue",
    ("KFX_EPUB", "get_named_fragment"): "IonValue",
    ("KFX_EPUB", "get_structure_name"): "IonValue",
}

METHOD_NAME_RETURNS = {
    "classify": "String",
    "serialize": "Vec<u8>",
    "serialize_multiple_values": "Vec<u8>",
    "serialize_single_value": "Vec<u8>",
    "create_import": "Option<IonAnnotation>",
    "create_local_symbol": "IonSymbol",
    "deserialize_annotated_value": "IonAnnotation",
    "deserialize_multiple_values": "Vec<IonValue>",
    "deserialize_single_value": "IonValue",
    "get_container": "YJContainer",
    "get_shared_symbol_table": "Option<IonSharedSymbolTable>",
    "get_symbol": "IonSymbol",
    "items": "Vec<(IonSymbol, IonValue)>",
    "values": "Vec<IonValue>",
}

FREE_FUNCTION_RETURNS = {
    "filtered_IonList": "Vec<IonValue>",
    "ion_type": "IonDataType",
    "unannotated": "IonValue",
}

ION_TYPE_ALIASES = {
    "IonBool": "bool",
    "IonDecimal": "Decimal",
    "IonFloat": "f64",
    "IonInt": "i32",
    "IonList": "Vec<IonValue>",
    "IonNull": "()",
    "IonString": "String",
    "IonStruct": "IndexMap<IonSymbol, IonValue>",
    "IonSymbol": "IonSymbol",
    "IonValue": "IonValue",
    "IonDataType": "IonDataType",
    "IonAnnotation": "IonAnnotation",
    "IonAnnots": "IonAnnots",
    "IonBLOB": "IonBLOB",
    "IonCLOB": "IonCLOB",
    "IonSExp": "Vec<IonValue>",
    "IonTimestamp": "IonTimestamp",
    "IonNop": "IonNop",
}

ION_TYPE_NAMES = {
    "IonAnnotation",
    "IonBLOB",
    "IonBool",
    "IonCLOB",
    "IonDecimal",
    "IonFloat",
    "IonInt",
    "IonList",
    "IonNop",
    "IonNull",
    "IonSExp",
    "IonString",
    "IonStruct",
    "IonSymbol",
    "IonTimestamp",
}

CLASS_FIELD_TYPES = {
    "Book": {
        "symtab": "LocalSymbolTable",
        "chapters": "HashMap<String, Vec<String>>",
    },
    "BookMetadata": {
        "fragments": "YJFragmentList",
        "symtab": "LocalSymbolTable",
        "kpf_container": "Option<KpfContainer>",
        "is_kpf_prepub": "bool",
        "is_dictionary": "bool",
        "is_scribe_notebook": "bool",
    },
    "BookPosLoc": {
        "fragments": "YJFragmentList",
        "symtab": "LocalSymbolTable",
        "kpf_container": "Option<KpfContainer>",
    },
    "BookStructure": {
        "fragments": "YJFragmentList",
        "symtab": "LocalSymbolTable",
        "kpf_container": "Option<KpfContainer>",
        "is_kpf_prepub": "bool",
        "is_dictionary": "bool",
        "is_scribe_notebook": "bool",
    },
    "KpfBook": {
        "fragments": "YJFragmentList",
        "symtab": "LocalSymbolTable",
        "kpf_container": "Option<KpfContainer>",
        "yj_containers": "Vec<YJContainer>",
        "is_kpf_prepub": "bool",
    },
    "YJ_Book": {
        "container_datafiles": "Vec<DataFile>",
        "datafile": "DataFile",
        "fragments": "YJFragmentList",
        "kpf_container": "Option<KpfContainer>",
        "reported_errors": "HashSet<String>",
        "reported_missing_fids": "HashSet<IonSymbol>",
        "symtab": "LocalSymbolTable",
        "yj_containers": "Vec<YJContainer>",
    },
    "YJContainer": {
        "datafile": "Option<DataFile>",
        "fragments": "YJFragmentList",
        "symtab": "LocalSymbolTable",
    },
    "KfxContainer": {
        "container_info": "IonStruct",
        "datafile": "Option<DataFile>",
        "doc_symbols": "Option<IonAnnotation>",
        "entities": "Vec<KfxContainerEntity>",
        "format_capabilities": "Option<IonAnnotation>",
        "fragments": "YJFragmentList",
        "symtab": "LocalSymbolTable",
    },
    "KfxContainerEntity": {
        "value": "IonValue",
    },
    "KpfContainer": {
        "book": "YJ_Book",
        "eid_symbol": "HashMap<i32, IonSymbol>",
        "element_type": "HashMap<String, String>",
        "fragments": "YJFragmentList",
        "kcb_data": "HashMap<String, IonValue>",
        "kcb_datafile": "DataFile",
        "kdf_datafile": "DataFile",
        "max_eid_in_sections": "IonValue",
        "source_epub": "Option<SourceEpub>",
        "symtab": "LocalSymbolTable",
    },
    "YJFragment": {
        "annotations": "YJFragmentKey",
        "value": "IonValue",
    },
    "IonAnnotation": {
        "annotations": "IonAnnots",
        "value": "IonValue",
    },
    "IonSerial": {
        "symtab": "Option<LocalSymbolTable>",
    },
    "IonText": {
        "symtab": "Option<LocalSymbolTable>",
        "indent": "i32",
        "file": "Option<TODO_py2many_unknown>",
        "allow_operators": "i32",
        "allow_unicode_strings": "bool",
    },
    "IonTimestampTZ": {
        "__offset": "Option<i32>",
        "__format": "String",
        "__fraction_len": "i32",
        "__present": "bool",
    },
    "Token": {
        "text": "String",
        "line_number": "i32",
        "start_col": "i32",
        "ttype": "String",
    },
    "Deserializer": {
        "symtab": "Option<LocalSymbolTable>",
    },
    "Serializer": {
        "symtab": "Option<LocalSymbolTable>",
    },
    "IonStruct": {},
    "IonSExp": {},
    "KFX_EPUB": {
        "book": "YJ_Book",
        "book_data": "HashMap<IonSymbol, HashMap<IonSymbol, IonValue>>",
        "book_symbols": "HashSet<IonSymbol>",
        "oebps_files": "HashMap<String, OutputFile>",
        "resource_cache": "HashMap<String, KfxEpubResource>",
        "used_fragments": "HashMap<(IonSymbol, IonSymbol), IonValue>",
    },
    "KFX_EPUB_Content": {},
    "KFX_EPUB_Illustrated_Layout": {},
    "KFX_EPUB_Metadata": {},
    "KFX_EPUB_Misc": {},
    "KFX_EPUB_Navigation": {},
    "KFX_EPUB_Notebook": {},
    "KFX_EPUB_Properties": {},
    "KFX_EPUB_Resources": {},
    "EPUB_Output": {
        "book_parts": "Vec<BookPart>",
        "guide": "Vec<GuideEntry>",
        "manifest": "Vec<ManifestEntry>",
        "manifest_files": "HashMap<String, ManifestEntry>",
        "ncx_toc": "Vec<TocEntry>",
        "oebps_files": "HashMap<String, OutputFile>",
        "pagemap": "Vec<PageMapEntry>",
    },
    "Style": {
        "properties": "HashMap<String, String>",
    },
    "ImgPlane": {
        "w": "i32",
        "h": "i32",
        "data": "Vec<u8>",
    },
    "OutputFile": {
        "data": "Vec<u8>",
        "media_type": "String",
    },
    "KfxEpubResource": {
        "data": "Vec<u8>",
        "media_type": "String",
    },
    "IonSharedSymbolTable": {
        "name": "String",
        "version": "i32",
        "symbols": "Vec<String>",
    },
    "SymbolTableCatalog": {
        "shared_symbol_tables": "HashMap<(String, i32), IonSharedSymbolTable>",
    },
    "LocalSymbolTable": {
        "symbols": "Vec<Option<IonSymbol>>",
        "id_of_symbol": "HashMap<IonSymbol, i32>",
        "symbol_of_id": "HashMap<i32, IonSymbol>",
        "local_min_id": "i32",
        "imports": "Vec<SymbolTableImport>",
        "max_id": "i32",
    },
    "Serializer": {
        "output": "Vec<u8>",
    },
    "Deserializer": {
        "data": "Vec<u8>",
    },
    "JxrImage": {
        "planes": "Vec<ImgPlane>",
        "width": "i32",
        "height": "i32",
    },
}

KFX_EPUB_MIXINS = {
    "KFX_EPUB_Content",
    "KFX_EPUB_Illustrated_Layout",
    "KFX_EPUB_Metadata",
    "KFX_EPUB_Misc",
    "KFX_EPUB_Navigation",
    "KFX_EPUB_Notebook",
    "KFX_EPUB_Properties",
    "KFX_EPUB_Resources",
    "EPUB_Output",
}

YJ_BOOK_MIXINS = {"BookMetadata", "BookPosLoc", "BookStructure", "KpfBook"}


def _fields_for_class(name: str) -> Dict[str, str]:
    fields = {}
    if name in YJ_BOOK_MIXINS:
        fields.update(CLASS_FIELD_TYPES["YJ_Book"])
    if name in KFX_EPUB_MIXINS:
        fields.update(CLASS_FIELD_TYPES["KFX_EPUB"])
        fields.update(CLASS_FIELD_TYPES["EPUB_Output"])
    fields.update(CLASS_FIELD_TYPES.get(name, {}))
    return fields


def _set_rust_type(node, rust_type: Optional[str]):
    if rust_type:
        node.kfx_rust_type = rust_type


class KfxRustTypeResolver(ast.NodeTransformer):
    """Project-aware type facts for the kfxlib Rust port.

    This pass intentionally stays conservative: it only asserts concrete domain
    types for known kfxlib constructors/methods and otherwise uses an explicit
    TODO placeholder inside containers instead of inventing misleading types.
    """

    def __init__(self):
        self._class_field_stack = []
        self._narrowing_stack = []
        self._ion_type_sources_stack = []

    @property
    def _class_fields(self) -> Dict[str, str]:
        if not self._class_field_stack:
            return {}
        return self._class_field_stack[-1]

    @property
    def _narrowings(self) -> Dict[str, str]:
        merged = {}
        for scope in self._narrowing_stack:
            merged.update(scope)
        return merged

    @property
    def _ion_type_sources(self) -> Dict[str, str]:
        merged = {}
        for scope in self._ion_type_sources_stack:
            merged.update(scope)
        return merged

    def _record_ion_type_source(self, type_var: str, source_var: str):
        if not self._ion_type_sources_stack:
            self._ion_type_sources_stack.append({})
        self._ion_type_sources_stack[-1][type_var] = source_var

    def _type_of_name(self, node: ast.Name) -> Optional[str]:
        if node.id == "self":
            return "Self"
        if node.id in self._narrowings:
            return self._narrowings[node.id]

        definition = node.scopes.find(node.id) if hasattr(node, "scopes") else None
        if definition is None:
            return None
        return getattr(definition, "kfx_rust_type", None)

    def _type_of_expr(self, node) -> Optional[str]:
        if node is None:
            return None
        if hasattr(node, "kfx_rust_type"):
            return node.kfx_rust_type
        if isinstance(node, ast.Name):
            return self._type_of_name(node)
        if isinstance(node, ast.Attribute):
            value_type = self._type_of_expr(node.value)
            if value_type == "Self":
                return self._class_fields.get(node.attr)
            if value_type in CLASS_FIELD_TYPES:
                return _fields_for_class(value_type).get(node.attr)
            if (
                value_type
                and value_type.startswith("Option<")
                and value_type.endswith(">")
            ):
                inner_type = value_type[len("Option<") : -1]
                return _fields_for_class(inner_type).get(node.attr)
            return None
        if isinstance(node, ast.Call):
            fname = get_id(node.func)
            if fname in CONSTRUCTOR_TYPES:
                return CONSTRUCTOR_TYPES[fname]
            if fname in FREE_FUNCTION_RETURNS:
                return FREE_FUNCTION_RETURNS[fname]
            if fname == "defaultdict" and node.args:
                factory = get_id(node.args[0])
                if factory == "list":
                    return "Vec"
                if factory == "set":
                    return "HashSet"
                if factory == "dict":
                    return "HashMap"
            if fname == "set":
                return "HashSet"
            if isinstance(node.func, ast.Attribute):
                receiver_type = self._type_of_expr(node.func.value)
                method_name = node.func.attr
                if method_name == "setdefault" and node.args:
                    value_type = self._type_of_expr(node.args[-1]) or TODO_TYPE
                    if receiver_type and receiver_type.startswith("HashMap<"):
                        return value_type
                mapped = METHOD_RETURNS.get((receiver_type, method_name))
                if mapped:
                    return mapped
                return METHOD_NAME_RETURNS.get(method_name)
        if isinstance(node, ast.List):
            if node.elts:
                element_type = self._type_of_expr(node.elts[0]) or TODO_TYPE
                return f"Vec<{element_type}>"
            return "Vec"
        if isinstance(node, ast.Set):
            if node.elts:
                element_type = self._type_of_expr(node.elts[0]) or TODO_TYPE
                return f"HashSet<{element_type}>"
            return "HashSet"
        if isinstance(node, ast.Dict):
            if node.keys:
                key_type = self._type_of_expr(node.keys[0]) or TODO_TYPE
                value_type = self._type_of_expr(node.values[0]) or TODO_TYPE
                return f"HashMap<{key_type}, {value_type}>"
            return "HashMap"
        return None

    def _ion_source_from_call(self, node) -> Optional[str]:
        if not (
            isinstance(node, ast.Call)
            and get_id(node.func) == "ion_type"
            and len(node.args) == 1
            and isinstance(node.args[0], ast.Name)
        ):
            return None
        return node.args[0].id

    @staticmethod
    def _container_with_element(
        container_type: str, element_type: Optional[str]
    ) -> str:
        element_type = element_type or TODO_TYPE
        if container_type == "Vec":
            return f"Vec<{element_type}>"
        if container_type == "HashSet":
            return f"HashSet<{element_type}>"
        return container_type

    @staticmethod
    def _vec_element_type(rust_type: Optional[str]) -> Optional[str]:
        if rust_type and rust_type.startswith("Vec<") and rust_type.endswith(">"):
            return rust_type[len("Vec<") : -1]
        return rust_type

    def _self_field_name(self, node) -> Optional[str]:
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            if node.value.id == "self":
                return node.attr
        return None

    def _collect_self_field_constraints(self, node: ast.ClassDef) -> Dict[str, str]:
        fields = {}
        empty_containers = {}
        none_initialized = set()

        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                target = child.targets[0]
                if isinstance(target, ast.Subscript):
                    field = self._self_field_name(target.value)
                    if field is None or empty_containers.get(field) != "HashMap":
                        continue
                    key_type = self._type_of_expr(target.slice) or TODO_TYPE
                    value_type = self._type_of_expr(child.value) or TODO_TYPE
                    fields.setdefault(field, f"HashMap<{key_type}, {value_type}>")
                    continue

                field = self._self_field_name(target)
                if field is None:
                    continue
                if (
                    isinstance(child.value, ast.Call)
                    and get_id(child.value.func) == "defaultdict"
                    and child.value.args
                ):
                    factory = get_id(child.value.args[0])
                    if factory == "list":
                        fields[field] = f"HashMap<{TODO_TYPE}, Vec<{TODO_TYPE}>>"
                    elif factory == "set":
                        fields[field] = f"HashMap<{TODO_TYPE}, HashSet<{TODO_TYPE}>>"
                    elif factory == "dict":
                        fields[field] = f"HashMap<{TODO_TYPE}, HashMap<{TODO_TYPE}, {TODO_TYPE}>>"
                    continue
                if (
                    isinstance(child.value, ast.Constant)
                    and child.value.value is None
                ):
                    none_initialized.add(field)
                    continue
                inferred = self._type_of_expr(child.value)
                if field in none_initialized and inferred:
                    fields[field] = inferred
                    none_initialized.discard(field)
                    continue
                if inferred in {"Vec", "HashSet", "HashMap"}:
                    empty_containers[field] = inferred
                elif inferred:
                    fields.setdefault(field, inferred)

            elif isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                field = self._self_field_name(child.func.value)
                if field is None:
                    continue
                if child.func.attr == "setdefault" and child.args:
                    value_type = self._type_of_expr(child.args[-1]) or TODO_TYPE
                    if field in empty_containers and empty_containers[field] == "HashMap":
                        key_type = (
                            self._type_of_expr(child.args[0]) if child.args else TODO_TYPE
                        )
                        fields.setdefault(
                            field, f"HashMap<{key_type or TODO_TYPE}, {value_type}>"
                        )
                    continue
                if field not in empty_containers:
                    continue

                if child.func.attr in {"append", "add", "extend", "update"} and child.args:
                    element_type = self._type_of_expr(child.args[0]) or TODO_TYPE
                    if child.func.attr == "extend":
                        element_type = self._vec_element_type(element_type)
                    if child.func.attr == "update" and empty_containers[field] == "HashMap":
                        if isinstance(child.args[0], ast.Dict) and child.args[0].keys:
                            key_type = self._type_of_expr(child.args[0].keys[0]) or TODO_TYPE
                            value_type = (
                                self._type_of_expr(child.args[0].values[0]) or TODO_TYPE
                            )
                            fields.setdefault(
                                field, f"HashMap<{key_type}, {value_type}>"
                            )
                        continue
                    fields.setdefault(
                        field,
                        self._container_with_element(
                            empty_containers[field], element_type
                        ),
                    )

        for field, container_type in empty_containers.items():
            if field not in fields:
                if container_type == "HashMap":
                    fields[field] = f"HashMap<{TODO_TYPE}, {TODO_TYPE}>"
                else:
                    fields[field] = self._container_with_element(container_type, None)

        return fields

    def visit_ClassDef(self, node):
        fields = _fields_for_class(node.name)
        for field, rust_type in self._collect_self_field_constraints(node).items():
            if field in fields and TODO_TYPE in rust_type:
                continue
            fields[field] = rust_type
        self._class_field_stack.append(fields)
        self.generic_visit(node)
        self._class_field_stack.pop()
        node.kfx_field_types = fields
        return node

    def _infer_function_return_type(self, node: ast.FunctionDef) -> Optional[str]:
        return_types = []
        for child in ast.walk(node):
            if isinstance(child, ast.Return) and child.value is not None:
                rust_type = getattr(child.value, "kfx_rust_type", None) or self._type_of_expr(
                    child.value
                )
                if rust_type:
                    return_types.append(rust_type)
        if not return_types:
            return None
        if all(t == return_types[0] for t in return_types):
            return return_types[0]
        if all(t in {"String", "&str"} for t in return_types):
            return "String"
        return return_types[0]

    def visit_FunctionDef(self, node):
        self._ion_type_sources_stack.append({})
        self.generic_visit(node)
        self._ion_type_sources_stack.pop()
        inferred = self._infer_function_return_type(node)
        if inferred:
            node.kfx_return_type = inferred
        return node

    def visit_Assign(self, node):
        self.generic_visit(node)

        if len(node.targets) != 1:
            return node

        target = node.targets[0]
        rust_type = None

        field = self._self_field_name(target)
        if field is not None:
            rust_type = self._class_fields.get(field) or self._type_of_expr(node.value)
            _set_rust_type(node.value, rust_type)
            _set_rust_type(target, rust_type)
            return node

        if isinstance(target, ast.Name):
            rust_type = self._type_of_expr(node.value)
            _set_rust_type(target, rust_type)
            _set_rust_type(node.value, rust_type)
            ion_source = self._ion_source_from_call(node.value)
            if ion_source:
                self._record_ion_type_source(target.id, ion_source)

        return node

    def visit_Return(self, node):
        self.generic_visit(node)
        if node.value is not None:
            _set_rust_type(node.value, self._type_of_expr(node.value))
        return node

    def visit_Call(self, node):
        self.generic_visit(node)
        _set_rust_type(node, self._type_of_expr(node))
        return node

    def _isinstance_narrowing(self, node) -> Dict[str, str]:
        if not (
            isinstance(node, ast.Call)
            and get_id(node.func) == "isinstance"
            and len(node.args) >= 2
            and isinstance(node.args[0], ast.Name)
        ):
            return {}
        type_names = []
        type_arg = node.args[1]
        if isinstance(type_arg, ast.Tuple):
            type_names = [get_id(elt) for elt in type_arg.elts]
        else:
            type_names = [get_id(type_arg)]
        for type_name in type_names:
            if type_name in CONSTRUCTOR_TYPES or type_name in ION_TYPE_NAMES:
                return {node.args[0].id: CONSTRUCTOR_TYPES.get(type_name, type_name)}
        return {}

    def _isinstance_else_narrowing(self, node) -> Dict[str, str]:
        # A negative isinstance against a tuple narrows the else branch to one of
        # the listed domain types. Prefer annotation-like wrappers because their
        # fields are useful for downstream value access.
        return self._isinstance_narrowing(node)

    def _ion_compare_narrowing(self, node) -> Dict[str, str]:
        return self._ion_compare_narrowing_for_ops(node, (ast.Is, ast.Eq))

    def _ion_compare_else_narrowing(self, node) -> Dict[str, str]:
        return self._ion_compare_narrowing_for_ops(node, (ast.IsNot, ast.NotEq))

    def _ion_compare_narrowing_for_ops(self, node, op_types) -> Dict[str, str]:
        if (
            not isinstance(node, ast.Compare)
            or len(node.ops) != 1
            or len(node.comparators) != 1
        ):
            return {}
        if not isinstance(node.ops[0], op_types):
            return {}
        left = node.left
        right = node.comparators[0]
        source_name = self._ion_source_from_call(left)
        if source_name is None and isinstance(left, ast.Name):
            source_name = self._ion_type_sources.get(left.id)
        if source_name is None:
            return {}
        right_id = get_id(right)
        if right_id in ION_TYPE_NAMES:
            return {source_name: right_id}
        return {}

    def _ion_membership_narrowing(self, node) -> Dict[str, str]:
        if (
            not isinstance(node, ast.Compare)
            or len(node.ops) != 1
            or len(node.comparators) != 1
            or not isinstance(node.ops[0], ast.In)
        ):
            return {}
        source_name = self._ion_source_from_call(node.left)
        if source_name is None and isinstance(node.left, ast.Name):
            source_name = self._ion_type_sources.get(node.left.id)
        if source_name is None:
            return {}
        comparator = node.comparators[0]
        if not isinstance(comparator, (ast.Set, ast.List, ast.Tuple)):
            return {}
        type_names = [get_id(elt) for elt in comparator.elts]
        if "IonStruct" in type_names:
            return {source_name: "IonStruct"}
        if "IonList" in type_names:
            return {source_name: "IonList"}
        for type_name in type_names:
            if type_name in ION_TYPE_NAMES:
                return {source_name: type_name}
        return {}

    def _condition_narrowing(self, node) -> Dict[str, str]:
        narrowing = {}
        if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.And):
            for value in node.values:
                narrowing.update(self._condition_narrowing(value))
            return narrowing
        narrowing.update(self._isinstance_narrowing(node))
        narrowing.update(self._ion_compare_narrowing(node))
        narrowing.update(self._ion_membership_narrowing(node))
        return narrowing

    def _condition_else_narrowing(self, node) -> Dict[str, str]:
        narrowing = {}
        if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.And):
            return narrowing
        narrowing.update(self._ion_compare_else_narrowing(node))
        return narrowing

    def visit_If(self, node):
        self.visit(node.test)
        narrowing = self._condition_narrowing(node.test)
        else_narrowing = self._condition_else_narrowing(node.test)
        self._narrowing_stack.append(narrowing)
        node.body = [self.visit(child) for child in node.body]
        self._narrowing_stack.pop()
        self._narrowing_stack.append(else_narrowing)
        node.orelse = [self.visit(child) for child in node.orelse]
        self._narrowing_stack.pop()
        return node


def resolve_kfx_rust_types(node):
    return KfxRustTypeResolver().visit(node)
