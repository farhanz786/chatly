import ast
with open("cogs/verification.py", encoding="utf-8") as f:
    source = f.read()
tree = ast.parse(source)
funcs = [node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
print(f"OK: {len(funcs)} functions, {len(classes)} classes")
print("Syntax is valid")
