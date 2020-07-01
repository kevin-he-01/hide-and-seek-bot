import ast
import astunparse

source="""
import typing
from typing import Dict, T, Callable
from typing import List

def foo(bar: Dict[T, List[T]],
        baz: Callable[[T], int] = lambda x: (x+3)/7,
        **kwargs) -> List[T]:
    pass
"""

class TypeHintRemover(ast.NodeTransformer):

    def visit_FunctionDef(self, node):
        # remove the return type defintion
        node.returns = None
        # remove all argument annotations
        if node.args.args:
            for arg in node.args.args:
                arg.annotation = None
        return node

    def visit_Import(self, node):
        node.names = [n for n in node.names if n.name != 'typing']
        return node if node.names else None

    def visit_ImportFrom(self, node):
        return node if node.module != 'typing' else None

# parse the source code into an AST
parsed_source = ast.parse(source)
# remove all type annotations, function return type definitions
# and import statements from 'typing'
transformed = TypeHintRemover().visit(parsed_source)
# convert the AST back to source code
print(astunparse.unparse(transformed))