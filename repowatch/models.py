from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from projects.models import Component
from repowatch import WatchException
from translations.models import POFile

class WatchManager(models.Manager):
    def add_watch(self, user, component, path=None):
        """
        Adds a file or repo to the watched list

        user: django.contrib.auth.models.User requesting the watch
        component: projects.models.Component to watch
        path: Path for file to watch, or None for a repo change
        """
        try:
            watch = self.get(path=path, component=component,
                user=user)
        except Watch.DoesNotExist:
            watch = Watch(path=path, component=component, user=user)
        try:
            rev = component.get_rev(path)
        except ValueError:
            raise WatchException(_('Unable to add watch for path %r') % 
                path)
        watch.rev = rev
        watch.save()
        return watch

    def remove_watch(self, user, component, path=None):
        """
        Removes a file or repo from the watched list
        Returns Watch.DoesNotExist if the watch doesn't exist

        user: django.contrib.auth.models.User requesting the watch
        component: projects.models.Component to watch
        path: Path for file to watch, or None for a repo change
        """
        watch = self.get(user=user, component=component, path=path)
        watch.delete()

    def get_watches(self, user, component):
        """
        Gets the current watches on a component by a user

        user: django.contrib.auth.models.User owning the watches
        component: projects.models.Component being watched
        """
        return self.filter(user=user, component=component)

    def update_watch(self, user, component, path=None):
        """
        Updates a watch without notifying the user

        user: django.contrib.auth.models.User owning the watch
        component: projects.models.Component to watch
        path: Path for file to watch, or None for a repo change
        """
        try:
            watch = self.get(user=user, component=component, path=path)
            try:
                rev = component.get_rev(path)
            except ValueError:
                pass
            watch.rev = rev
            watch.save()
        except Watch.DoesNotExist:
            pass

class IntegerTupleField(models.CharField):
    """
    A field type for holding a tuple of integers. Stores as a string
    with the integers delimited by colons.
    """
    __metaclass__ = models.SubfieldBase

    def formfield(self, **kwargs):
        defaults = {
            'form_class': forms.RegexField,
            # We include the final comma so as to not penalize Python
            # programmers for their inside knowledge
            'regex': r'^\((\s*[+-]?\d+\s*(,\s*[+-]?\d+)*)\s*,?\s*\)$',
            'max_length': self.max_length,
            'error_messages': {
                'invalid': _('Enter 0 or more comma-separated integers '
                    'in parentheses.'),
                'required': _('You must enter at least a pair of '
                    'parentheses containing nothing.'),
            },
        }
        defaults.update(kwargs)
        return super(IntegerTupleField, self).formfield(**defaults)
    
    def to_python(self, value):
        if type(value) == tuple:
            return value
        if value == '':
            return ()
        if value is None:
            return None
        return tuple(int(x) for x in value.split(u':'))
        
    def get_db_prep_value(self, value):
        if value is None:
            return None
        return u':'.join(unicode(x) for x in value)
        
    def get_db_prep_lookup(self, lookup_type, value):
        if lookup_type == 'exact':
            return [self.get_db_prep_value(value)]
        else:
            raise TypeError('Lookup type %r not supported' %
                lookup_type)
    
    def value_to_string(self, obj):
        return self.get_db_prep_value(obj)

class Watch(models.Model):
    path = models.CharField(max_length=128, null=True, default=None,
        help_text='Path to the file within the repo, or NULL for the '
        'whole repo')
    rev = IntegerTupleField(max_length=64, null=True,
        help_text='Latest revision seen')
    component = models.ForeignKey(Component,
        help_text='Component containing the repo to watch')
    user = models.ForeignKey(User,
        help_text='User to notify upon detecting a change')
    
    objects = WatchManager()

    def __unicode__(self):
        if self.path is None:
            return u'repo of %s for %s' % (self.component, self.user)
        return u'%s in %s for %s' % (self.path, self.component,
            self.user)

    class Meta:
        verbose_name = _('watch')
        verbose_name_plural = _('watches')

# Function to monkeypatch into translations models
def __watched(self):
    return len(self.object.watch_set.filter(path=self.filename)) > 0

for m in (POFile,):
    m.watched = __watched
