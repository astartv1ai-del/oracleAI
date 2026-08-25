import inspect
import resvg_py

print(inspect.signature(resvg_py.svg_to_bytes))
print(inspect.getdoc(resvg_py.svg_to_bytes) or "no docstring")
