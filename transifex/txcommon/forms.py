import re

from codebases.forms import UnitForm
from tarball.forms import TarballSubForm
from vcs.forms import VcsUnitSubForm

def unit_sub_forms(unit, post_request=None, blacklist_qs=None,):
    """
    Return a list of Unit SubForms with different fields based on the unit types

    ``unit``: It's an instance of the Unit model
    ``post_request``: The POST request sent to populate the Forms
    ``blacklist_qs`` : a blacklisted queryset for vcsunit objects that shouldn't
        have anything common
    """
    if post_request:
        unit_form = UnitForm(post_request, instance=unit, prefix='unit')
        try: 
            unit_instance = unit_form.save(commit=False)
        except ValueError:
            unit_instance = unit
    else: 
        unit_instance = unit

    _subforms = [VcsUnitSubForm, TarballSubForm]
    _formd = {False: None, True: unit_instance}

    ret = [
        {
            'form': unitform(post_request,
                instance=_formd[unitform._meta.model == type(unit)],
                prefix=unicode(unitform.Meta.model._meta.object_name)),
            'id': unitform.Meta.model._meta.object_name,
            'triggers': unitform.Meta.model.unit_types,
        } for unitform in _subforms]

    for something in ret:
        if something['id'] == 'VcsUnit':
            something['form'].set_blacklist_root_field(blacklist_qs)
    return ret
    