import re

from django.conf import settings
from django.forms import CharField, ValidationError
from django.utils.translation import ugettext_lazy as _
from codebases.models import Unit

ALLOWED_REPOSITORY_PREFIXES = getattr(settings, 'ALLOWED_REPOSITORY_PREFIXES',
    None)

class ValidRegexField(CharField):
    def __init__(self, max_length=None, min_length=None, error_message=None,
        *args, **kwargs):
        super(ValidRegexField, self).__init__(max_length, min_length, *args,
            **kwargs)

    def clean(self, value):
        value = super(ValidRegexField, self).clean(value)
        try:
            return re.compile(value).pattern
        except re.error, e:
            raise ValidationError(_('Enter a valid regular expression.'))


class ValidTarBallUrl(CharField):
    def __init__(self, max_length=None, min_length=None, *args, **kwargs):
        super(ValidTarBallUrl, self).__init__(max_length, min_length, *args,
            **kwargs)

    def clean(self, value):
        value = super(ValidTarBallUrl, self).clean(value)
        if (value.startswith('http://') or value.startswith('ftp://')):
            if value.endswith('tar.gz') or value.endswith('.tgz'):
                return value
            else:
                raise ValidationError(_('The root url does not point to a '
                                        '.tar.gz or .tgz file'))
        else:
            raise ValidationError(_('The root url must start with http:// or '
                                    'ftp://'))
        return value

class ValidRootUri(CharField):
    """
    Create a charfield validator that forbids anything that doesn't start with
    something from settings.ALLOWED_REPOSITORY_PREFIXES
    """
    def __init__(self, max_length=None, min_length=None, *args, **kwargs):
        self.type = None
        super(ValidRootUri, self).__init__(max_length, min_length, *args,
            **kwargs)

    def clean(self, value):
        value = super(ValidRootUri, self).clean(value)
        self.starting = None
        if ALLOWED_REPOSITORY_PREFIXES:
            for key in ALLOWED_REPOSITORY_PREFIXES.keys():
                for option in ALLOWED_REPOSITORY_PREFIXES[key]:
                    if value.startswith(option):
                        self.starting = option
                        ret = value
            if self.starting == None:
                raise ValidationError(_("This is not a valid root URL for this "
                    "repository type. Valid choices are: %s" %
                    str(self.get_allowed_prefixes())))
            cleanedupstring = value[len(self.starting):]
            print cleanedupstring
            try:
                numofobj = Unit.objects.filter(root__icontains = cleanedupstring)
            except:
                pass

            if len(numofobj) > 0:
                raise ValidationError(_("This repo already exists on the "
                    "server"))
        return value

    def set_repo_type(self, type):
        """
        Set the repotype variable with the type of the repository.

        This is called by vcs/forms.py to setup the type of the repository (hg,
        git, etc), and its used in @get_allowed prefixes to print the abailable
        prefixes allowed in unit.root mask.
        """

        if type in ALLOWED_REPOSITORY_PREFIXES:
            self.repotype = type
        else:
            self.repotype = None

    def get_allowed_prefixes(self):
        """
        Concatenate the allowed prefixes from the settings var.
        
        This concanates the allowed prefixes into a list and return that list.
        If the self.repotype is set then we add to the list only the 
        ALLOWED_REPOSITORY_PREFIXES['all'] and the 
        ALLOWED_REPOSITORY_PREFIXES['self.reporype'] members. Otherwise we 
        return a list with all the members of the ALLOWED_REPOSITORY_PREFIXES.
        """

        if not hasattr(self, 'repotype'):
            return self.dry_get_all_options()
        if self.repotype:
            return (ALLOWED_REPOSITORY_PREFIXES['all'] + 
                ALLOWED_REPOSITORY_PREFIXES[self.repotype])
        else:
            return self.dry_get_all_options()

    def dry_get_all_options(self):
        """
        Create a list with all members of ALLOWED_REPOSITORY_PREFIXES.

        This just iterates in the ALLOWED_REPOSITORY_PREFIXES and append to the
        returnable list its members.
        """
        ret=[]
        try:
            for singlekey in ALLOWED_REPOSITORY_PREFIXES.keys():
                for option in ALLOWED_REPOSITORY_PREFIXES[singlekey]:
                    ret.append(option)
        except:
            #this can only happen when repotype is empty and
            #settings.ALLOWED_REPOSITORY_PREFIXES is empty
            pass
        return ret

