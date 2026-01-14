import ast
from argparse import ArgumentParser
from typing import Any

_types: set[type] = set([str, int, tuple, dict, float, set, list, bool])
types = {t.__name__: t for t in _types}


def cleaned_body(body: list[ast.stmt]):
    nbody = []
    for obj in body:
        if not isinstance(obj, ast.Pass):
            nbody.append(obj)

    return nbody


class Layer(ast.NodeTransformer):
    def view(self, node: ast.AST) -> Any:
        return super().visit(node)


class TypeHookDetect(ast.NodeVisitor):
    def __init__(self) -> None:
        self.renames = set()

    def visit_ClassDef(self, node: ast.ClassDef):
        if node.name in types and cleaned_body(node.body) != []:
            self.renames.add(node.name)

        return self.generic_visit(node)


class TypeCleaner(Layer):
    def view(self, node: ast.AST) -> Any:
        hook_detector = TypeHookDetect()
        hook_detector.visit(node)

        self.renames = hook_detector.renames

        return super().view(node)

    def visit_Call(self, node: ast.Call):
        if (
            isinstance(node.func, ast.Name)
            and node.func.id in types
            and node.func.id not in self.renames
            and len(node.args) == 1
            and isinstance(node.args[0], ast.Constant)
            and not node.keywords
        ):
            try:
                return ast.Constant(types[node.func.id](node.args[0].value))
            except Exception:
                pass

        return self.generic_visit(node)


class NoJunkConsts(Layer):
    def visit_Expr(self, node: ast.Expr):
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            return

        return self.generic_visit(node)


class InlineOps(Layer):
    def view(self, node: ast.AST) -> Any:
        hook_detector = TypeHookDetect()
        hook_detector.visit(node)

        self.renames = hook_detector.renames

        return super().view(node)

    def visit_BinOp(self, node: ast.BinOp) -> Any:
        if (
            isinstance(node.left, ast.Constant)
            and isinstance(node.right, ast.Constant)
            and type(node.left.value).__name__ not in self.renames
            and type(node.right.value).__name__ not in self.renames
        ):
            return ast.Constant(
                eval(
                    compile(
                        ast.fix_missing_locations(ast.Expression(node)),
                        "<inline>",
                        "eval",
                    )
                )
            )

        return self.generic_visit(node)


class NoStupidLambda(Layer):
    def visit_Call(self, node: ast.Call) -> Any:
        if isinstance(node.func, ast.Lambda) and isinstance(
            node.func.body, ast.Constant
        ):
            return node.func.body

        return self.generic_visit(node)


class GetUnsedVars(ast.NodeVisitor):
    def __init__(self) -> None:
        self.unused = {}

    def visit_Assign(self, node: ast.Assign) -> Any:
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            self.unused[node.targets[0].id] = 2

        return self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> Any:
        if node.id in self.unused:
            self.unused[node.id] -= 1
            if self.unused[node.id] == 0:
                del self.unused[node.id]

        return self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        if not node.decorator_list:
            self.unused[node.name] = 2
        return self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> Any:
        if not node.decorator_list:
            self.unused[node.name] = 2
        return self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> Any:
        if not node.decorator_list:
            self.unused[node.name] = 2
        return self.generic_visit(node)


class NoJunkVars(Layer):
    def view(self, node: ast.AST) -> Any:
        unused_detector = GetUnsedVars()
        unused_detector.visit(node)

        self.unused = unused_detector.unused
        return super().view(node)

    def visit_Assign(self, node: ast.Assign) -> Any:
        if (
            len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id in self.unused
        ):
            return

        return self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        if node.name in self.unused:
            return

        return self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> Any:
        if node.name in self.unused:
            return

        return self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> Any:
        if node.name in self.unused:
            return

        return self.generic_visit(node)


def main():
    parser = ArgumentParser(description="PyInline by @PaketPKSoftware")
    parser.add_argument("file", type=str, help="Original .py file path")
    parser.add_argument("passes", type=int, help="Pass count")

    args = parser.parse_args()

    layers = [TypeCleaner, NoJunkConsts, InlineOps, NoStupidLambda, NoJunkVars]

    with open(args.file, "rb") as f:
        raw_code = f.read()

    code = ast.parse(raw_code)

    print("# pyinline by @paketpksoftware")
    print(f"# original file: {args.file}")
    if code is None:
        print("# [pyinline] no ast ?? :(")
        return

    output = "# hi"
    passes = args.passes

    for _pass in range(passes):
        for layer in layers:
            code = layer().view(code)
            code = ast.fix_missing_locations(code)
            if not code:
                print(f"# [pyinline] code has no payload (pass: {_pass}) :///")
                return

            output = ast.unparse(code)

    print("# passes:", passes, end="\n\n")
    print(output)


if __name__ == "__main__":
    main()
