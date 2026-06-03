import ast
from typing import Dict, Optional, Tuple

from py2many.analysis import get_id

TODO_TYPE = "TODO_py2many_unknown"


CONSTRUCTOR_TYPES = {
    "DataFile": "DataFile",
    "IonAnnots": "IonAnnots",
    "IonAnnotation": "IonAnnotation",
    "IonBLOB": "IonBLOB",
    "IonCLOB": "IonCLOB",
    "IonNop": "IonNop",
    "IonSExp": "IonSExp",
    "IonStruct": "IonStruct",
    "IonSymbol": "IonSymbol",
    "IonTimestamp": "IonTimestamp",
    "IonTimestampTZ": "IonTimestampTZ",
    "IS": "IonSymbol",
    "KfxContainer": "KfxContainer",
    "KfxContainerEntity": "KfxContainerEntity",
    "KpfContainer": "KpfContainer",
    "LocalSymbolTable": "LocalSymbolTable",
    "SymbolTableCatalog": "SymbolTableCatalog",
    "YJFragment": "YJFragment",
    "YJFragmentKey": "YJFragmentKey",
    "YJFragmentList": "YJFragmentList",
}


METHOD_RETURNS = {
    ("YJFragmentList", "get"): "Option<YJFragment>",
    ("YJFragmentList", "get_all"): "Vec<YJFragment>",
    ("IonStruct", "get"): "IonValue",
    ("IonStruct", "pop"): "IonValue",
}


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
            return None
        if isinstance(node, ast.Call):
            fname = get_id(node.func)
            if fname in CONSTRUCTOR_TYPES:
                return CONSTRUCTOR_TYPES[fname]
            if fname == "set":
                return "HashSet"
            if isinstance(node.func, ast.Attribute):
                receiver_type = self._type_of_expr(node.func.value)
                return METHOD_RETURNS.get((receiver_type, node.func.attr))
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

    def _self_field_name(self, node) -> Optional[str]:
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            if node.value.id == "self":
                return node.attr
        return None

    def _collect_self_field_constraints(self, node: ast.ClassDef) -> Dict[str, str]:
        fields = {}
        empty_containers = {}

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
                inferred = self._type_of_expr(child.value)
                if inferred in {"Vec", "HashSet", "HashMap"}:
                    empty_containers[field] = inferred
                elif inferred:
                    fields.setdefault(field, inferred)

            elif isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                field = self._self_field_name(child.func.value)
                if field is None:
                    continue
                if field not in empty_containers:
                    continue

                if child.func.attr in {"append", "add"} and child.args:
                    element_type = self._type_of_expr(child.args[0]) or TODO_TYPE
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
        fields = self._collect_self_field_constraints(node)
        self._class_field_stack.append(fields)
        self.generic_visit(node)
        self._class_field_stack.pop()
        node.kfx_field_types = fields
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

        return node

    def visit_Call(self, node):
        self.generic_visit(node)
        _set_rust_type(node, self._type_of_expr(node))
        return node

    def _ion_type_narrowing(self, node) -> Dict[str, str]:
        if (
            not isinstance(node, ast.Compare)
            or len(node.ops) != 1
            or len(node.comparators) != 1
        ):
            return {}
        if not isinstance(node.ops[0], (ast.Is, ast.Eq)):
            return {}
        left = node.left
        right = node.comparators[0]
        if not (
            isinstance(left, ast.Call)
            and get_id(left.func) == "ion_type"
            and len(left.args) == 1
            and isinstance(left.args[0], ast.Name)
        ):
            return {}
        right_id = get_id(right)
        if right_id in {"IonStruct", "IonList", "IonSymbol", "IonAnnotation"}:
            return {left.args[0].id: right_id}
        return {}

    def visit_If(self, node):
        self.visit(node.test)
        narrowing = self._ion_type_narrowing(node.test)
        self._narrowing_stack.append(narrowing)
        node.body = [self.visit(child) for child in node.body]
        self._narrowing_stack.pop()
        node.orelse = [self.visit(child) for child in node.orelse]
        return node


def resolve_kfx_rust_types(node):
    return KfxRustTypeResolver().visit(node)
