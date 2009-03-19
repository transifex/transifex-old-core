version_info = (0, 5, 0, 'final', 0)

_verpart = ''
if version_info[3] != 'final':
    _verpart = version_info[3]

version = '.'.join(str(v) for v in version_info[:3]) + _verpart

del _verpart
