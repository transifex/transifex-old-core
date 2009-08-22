version_info = (0, 7, 0, 'final', 0)

_verpart = ''
if version_info[3] != 'final':
    _verpart = version_info[3]

version = '.'.join(str(v) for v in version_info[:3]) + _verpart

del _verpart

def import_to_python(import_str):
    """Given a string 'a.b.c' return object c from a.b module."""
    mod_name, obj_name = import_str.rsplit('.', 1)
    obj = getattr(__import__(mod_name, {}, {}, ['']), obj_name)
    return obj
