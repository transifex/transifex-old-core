import os
from django.conf import settings

cvcs_submit_msg = """
%(date)s  %(userinfo)s

%(message)s

"""

dvcs_submit_msg = """
%(message)s
            
Transmitted-via: Transifex (%(domain)s)
"""

REPOSITORIES_PATH = os.path.join(settings.SCRATCH_DIR, 'sources')

def import_to_python(import_str):
    """
    Given a string 'a.b.c' returns object c from a.b module.
    """
    mod_name, obj_name = import_str.rsplit('.',1)
    obj = getattr(__import__(mod_name, {}, {}, ['']), obj_name)
    return obj
    
def get_browser_class(type):
    return import_to_python('txc.vcs.types.%s.%sBrowser' % (type, type))
