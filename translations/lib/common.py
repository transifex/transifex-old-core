"""
Common methods to be used around the modules. 
"""

def import_to_python(import_str):
    """Given a string 'a.b.c' return object c from a.b module."""
    mod_name, obj_name = import_str.rsplit('.',1)
    obj = getattr(__import__(mod_name, {}, {}, ['']), obj_name)
    return obj