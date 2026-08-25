import inspect
import kerykeion
print('version', getattr(kerykeion, '__version__', 'unknown'))
print('exports', [name for name in dir(kerykeion) if 'Chart' in name or 'Subject' in name or 'Drawer' in name][:30])
for name in ('AstrologicalSubject', 'KerykeionChartSVG', 'ChartDataFactory', 'ChartDrawer'):
    obj = getattr(kerykeion, name, None)
    if obj is not None:
        print(name, inspect.signature(obj) if callable(obj) else type(obj))
        if hasattr(obj, 'make_svg'):
            print('make_svg', inspect.signature(obj.make_svg))
        if hasattr(obj, 'makeTemplate'):
            print('makeTemplate', inspect.signature(obj.makeTemplate))
