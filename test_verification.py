import ast
import sys

# Read and parse the verification cog
path = "D:\\project\\chatly\\cogs\\verification.py"
with open(path, encoding="utf-8") as f:
    source = f.read()

# Parse AST
tree = ast.parse(source)

# Count functions and classes
funcs = [node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]

print(f"✅ {len(funcs)} functions defined")
print(f"✅ {len(classes)} classes defined")
print("✅ No syntax errors - file is valid Python")
