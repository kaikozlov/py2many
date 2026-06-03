import ast
from typing import Union

from py2many.analysis import get_id
from py2many.clike import CLikeTranspiler as CommonCLikeTranspiler
from py2many.clike import LifeTime

from .inference import (
    RUST_CONTAINER_TYPE_MAP,
    RUST_RANK_TO_TYPE,
    RUST_TYPE_MAP,
    RUST_WIDTH_RANK,
    is_rust_reference,
)
from .rust_emit import (
    chained_compare_parts,
    escape_rust_ident,
    parenthesize_cast_expr,
)

# allowed as names in Python but treated as keywords in Rust
RUST_KEYWORDS = frozenset(
    [
        "struct",
        "type",
        "match",
        "impl",
        "const",
        "enum",
        "extern",
        "fn",
        "loop",
        "move",
        "mut",
        "pub",
        "ref",
        "trait",
        "where",
        "use",
        "unsafe",
    ]
)


class CLikeTranspiler(CommonCLikeTranspiler):
    def __init__(self):
        super().__init__()
        CommonCLikeTranspiler._type_map = RUST_TYPE_MAP
        CommonCLikeTranspiler._container_type_map = RUST_CONTAINER_TYPE_MAP
        self._keywords = RUST_KEYWORDS

    @classmethod
    def _map_type(cls, typename, lifetime=LifeTime.UNKNOWN) -> str:
        if isinstance(typename, str):
            typename = typename.replace("Union [", "Union[")
            if typename.startswith("Union[") and typename.endswith("]"):
                return cls._map_union_type(typename)
            if typename.startswith("typing."):
                typename = typename.split(".", 1)[1]
            if typename in {"Optional", "Any"}:
                return cls._default_type
        ret = CommonCLikeTranspiler._map_type(typename, lifetime)
        if lifetime == LifeTime.STATIC and ret[0] == "&":
            return f"&'static {ret[1:]}"
        return ret

    @classmethod
    def _map_union_type(cls, typename: str) -> str:
        union_body = typename.removeprefix("Union[").removesuffix("]")
        parts = []
        depth = 0
        start = 0
        for index, char in enumerate(union_body):
            if char == "[":
                depth += 1
            elif char == "]":
                depth -= 1
            elif char == "," and depth == 0:
                parts.append(union_body[start:index].strip())
                start = index + 1
        parts.append(union_body[start:].strip())
        mapped = [cls._map_type(part) for part in parts if part]
        mapped = [part for part in mapped if part and part != cls._default_type]
        if not mapped:
            return cls._default_type
        if len(mapped) == 1:
            return mapped[0]
        if "None" in parts or "NoneType" in parts:
            non_none = [part for part in mapped if part != "()"]
            if len(non_none) == 1:
                return f"Option<{non_none[0]}>"
        if "IonValue" in mapped:
            return "IonValue"
        return mapped[0]

    def visit_Name(self, node) -> str:
        escaped = escape_rust_ident(node.id)
        if escaped != node.id:
            return escaped
        if node.id in self._keywords:
            return node.id + "_"
        return super().visit_Name(node)

    @classmethod
    def _union_type_from_subscript(cls, node) -> str:
        slice_value = cls._slice_value(node)
        if isinstance(slice_value, ast.Tuple):
            parts = [cls._typename_from_type_node(elt) for elt in slice_value.elts]
            parts = [part for part in parts if isinstance(part, str)]
            if parts:
                return cls._map_union_type(f"Union[{', '.join(parts)}]")
        part = cls._typename_from_type_node(slice_value)
        if isinstance(part, str):
            return cls._map_union_type(f"Union[{part}]")
        return cls._default_type

    @classmethod
    def _typename_from_annotation(cls, node, attr="annotation") -> str:
        if hasattr(node, attr):
            type_node = getattr(node, attr)
            if isinstance(type_node, ast.Subscript):
                value_type = None
                if isinstance(type_node.value, ast.Name):
                    value_type = type_node.value.id
                elif isinstance(type_node.value, ast.Attribute):
                    value_type = get_id(type_node.value).split(".")[-1]
                if value_type == "Union":
                    return cls._union_type_from_subscript(type_node)
        return super()._typename_from_annotation(node, attr)

    @classmethod
    def _typename_from_type_node(cls, node) -> Union[list, str, None]:
        if isinstance(node, ast.Subscript):
            value_type = None
            if isinstance(node.value, ast.Name):
                value_type = node.value.id
            elif isinstance(node.value, ast.Attribute):
                value_type = get_id(node.value).split(".")[-1]
            if value_type == "Union":
                return cls._union_type_from_subscript(node)
        typename = super()._typename_from_type_node(node)
        if isinstance(typename, str):
            if typename.startswith("Union[") and typename.endswith("]"):
                return cls._map_union_type(typename)
            if typename.startswith("typing."):
                return cls._map_type(typename.split(".", 1)[1])
        return typename

    def visit_BinOp(self, node) -> str:
        if isinstance(node.op, ast.Pow):
            return f"pow({self.visit(node.left)}, {self.visit(node.right)})"

        left = self.visit(node.left)
        op = self.visit(node.op)
        right = self.visit(node.right)

        left_type = self._typename_from_annotation(node.left)
        right_type = self._typename_from_annotation(node.right)
        op_type = self._typename_from_annotation(node)

        left_rank = RUST_WIDTH_RANK.get(left_type, -1)
        right_rank = RUST_WIDTH_RANK.get(right_type, -1)
        left_target_rank = left_rank
        right_target_rank = right_rank

        op_rank = -1
        if op_type != self._default_type:
            op_rank = RUST_WIDTH_RANK.get(op_type, -1)
            left_target_rank = right_target_rank = op_rank

        if right_target_rank > right_rank:
            right_target_type = RUST_RANK_TO_TYPE[right_target_rank]
            right = f"({right} as {right_target_type})"
        if left_target_rank > left_rank:
            left_target_type = RUST_RANK_TO_TYPE[left_target_rank]
            left = f"({left} as {left_target_type})"

        # Multiplication and division binds tighter (has higher precedence) than addition and subtraction.
        # To visually communicate this we omit spaces when multiplying and dividing.
        if isinstance(node.op, (ast.Mult, ast.Div)):
            return f"({left}{op}{right})"
        else:
            return f"({left} {op} {right})"

    def _visit_single_compare(self, left_node, op_node, right_node) -> str:
        left_type = self._typename_from_annotation(left_node)
        right_type = self._typename_from_annotation(right_node)

        left = self.visit(left_node)
        op = self.visit(op_node)
        right = self.visit(right_node)

        if not is_rust_reference(left_node) and is_rust_reference(right_node):
            right = f"*{right}"

        if is_rust_reference(left_node) and not is_rust_reference(right_node):
            left = f"*{left}"

        left_rank = RUST_WIDTH_RANK.get(left_type, -1)
        right_rank = RUST_WIDTH_RANK.get(right_type, -1)

        if left_rank > right_rank:
            right = f"({right} as {left_type})"
        elif right_rank > left_rank:
            left = f"({left} as {right_type})"

        left = parenthesize_cast_expr(left)
        right = parenthesize_cast_expr(right)
        if isinstance(left_node, ast.Compare):
            left = f"({left})"
        return f"{left} {op} {right}"

    def visit_Compare(self, node) -> str:
        if isinstance(node.ops[0], ast.In):
            return self.visit_In(node)

        if len(node.ops) > 1:
            left = self.visit(node.left)
            ops = [self.visit(op) for op in node.ops]
            comparators = [self.visit(comp) for comp in node.comparators]
            return chained_compare_parts(left, ops, comparators)

        return self._visit_single_compare(node.left, node.ops[0], node.comparators[0])

    def visit_In(self, node) -> str:
        left = self.visit(node.left)
        right = self.visit(node.comparators[0])
        return f"{right}.any({left})"
