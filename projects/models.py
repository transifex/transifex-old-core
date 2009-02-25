import os
from datetime import datetime
import markdown

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.db.models import permalink
from django.forms import ModelForm
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.utils.html import escape

import tagging
from tagging.fields import TagField

from txcollections.models import Collection, CollectionRelease
from translations.models import POFile
from vcs.models import Unit
from transifex.log import (logger, log_model)
from projects.handlers import get_trans_handler


# The following is a tricky module, so we're including it only if needed
if settings.ENABLE_NOTICES:
    from notification import models as notification

def cached_property(func):
    """
    Cached property.

    This function is able to verify if an instance of a property fieald
    was already created before and, if not, it creates the new one.
    When needed it also is able to delete the cached property field from
    the memory.

    Usage:
    @cached_property
    def trans(self):
        ...

    del(self.trans)
 
    """
    def _set_cache(self):
        cache_attr = "__%s" % func.__name__
        try:
            return getattr(self, cache_attr)
        except AttributeError:
            value = func(self)
            setattr(self, cache_attr, value)
            return value

    def _del_cache(self):
        cache_attr = "__%s" % func.__name__
        try:
            delattr(self, cache_attr)
        except AttributeError:
            pass
        
    return property(_set_cache, fdel=_del_cache)


class Project(models.Model):
    
    """
    A project is a collection of translatable resources.

    >>> p = Project.objects.create(slug="foo", name="Foo Project")
    >>> p = Project.objects.get(slug='foo')
    >>> p
    <Project: Foo Project>
    >>> Project.objects.create(slug="foo", name="Foo Project")
    Traceback (most recent call last):
        ...
    IntegrityError: column slug is not unique
    >>> p.delete()
    
    """

    slug = models.SlugField(max_length=30, unique=True, 
        help_text=_('A short label to be used in the URL, containing only '
                    'letters, numbers, underscores or hyphens.'))
    name = models.CharField(max_length=50,
        help_text=_('A string like a name or very short description.'))
    description = models.CharField(blank=True, max_length=255,
        help_text=_('A sentence or two describing the object (optional).'))
    long_description = models.TextField(blank=True, max_length=1000,
        help_text=_('A longer description (optional). Use Markdown syntax.'))
    homepage = models.URLField(blank=True, verify_exists=False)
    feed = models.CharField(blank=True, max_length=255,
        help_text=_('An RSS feed with updates on the project.'))

    hidden = models.BooleanField(default=False,
        help_text=_('Hide this object from the list view?'))
    enabled = models.BooleanField(default=True,
        help_text=_('Enable this object or disable its use?'))
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)
    
    tags = TagField()

    # Relations
    # The collections this project belongs to.
    collections = models.ManyToManyField(Collection, related_name='projects',
                                         blank=True, null=True,)

    # Normalized fields
    long_description_html = models.TextField(blank=True, max_length=1000, 
        help_text=_('Description in HTML.'), editable=False)

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return _('<Project: %s>') % self.name

    class Meta:
        verbose_name = _('project')
        verbose_name_plural = _('projects')
        db_table  = 'projects_project'
        ordering  = ('name',)
        get_latest_by = 'created'

    def save(self, *args, **kwargs):
        """Save the object in the database."""
        long_desc = escape(self.long_description)
        self.long_description_html = markdown.markdown(long_desc)
        # Get a grip on the empty 'created' to detect a new addition. 
        created = self.created
        super(Project, self).save(*args, **kwargs)

        for c in Component.objects.filter(project=self):
            c.save()
        
        if not created and settings.ENABLE_NOTICES:
            notification.send(User.objects.all(), "projects_added_new",
                              {'project': self})

    def delete(self, *args, **kwargs):
        for c in Component.objects.filter(project=self):
            c.delete()
        super(Project, self).delete(*args, **kwargs)

    @permalink
    def get_absolute_url(self):
        return ('project_detail', None, { 'slug': self.slug })

tagging.register(Project, tag_descriptor_attr='tagsobj')
log_model(Project)


class ComponentManager(models.Manager):
    
    def with_language(self, language):
        """
        Return distinct components which ship a language's files.

        Poll Components for ones that have files of a particular
        language. Can be used by a language page, to list all
        components which ship this language.
        """

        pofiles = POFile.objects.filter(language=language)
        qs = self.filter(id__in=[c.object_id for c in pofiles])
        return qs.distinct()


class Component(models.Model):

    """A component is a translatable resource."""

    slug = models.SlugField(max_length=30,
        help_text=_('A short label to be used in the URL, containing only '
                    'letters, numbers, underscores or hyphens.'))
    name = models.CharField(max_length=50,
        help_text=_('A string like a name or very short description.'))
    description = models.CharField(blank=True, max_length=255,
        help_text=_('A sentence or two describing the object (optional).'))
    long_description = models.TextField(blank=True, max_length=1000,
        help_text=_('A longer description (optional). Use Markdown syntax.'))
    source_lang = models.CharField(max_length=50,
        help_text=_("The source language for this component, "
                    "eg. 'en', 'pt_BR', 'el'."))
    i18n_type = models.CharField(max_length=20,
        choices=settings.TRANS_CHOICES.items(),
        help_text=_("The code's type of i18n support (%s)" %
                    ', '.join(settings.TRANS_CHOICES.keys())))
    file_filter = models.CharField(max_length=50, blank=True, null=True,
        help_text=_("A regex to filter the exposed files. Eg: 'po/.*'"))
    hidden = models.BooleanField(default=False,
        help_text=_('Hide this object from the list view?'))
    enabled = models.BooleanField(default=True,
        help_text=_('Enable this object or disable its use?'))
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)
    
    # Normalized fields
    full_name = models.CharField(max_length=100, editable=False)
    long_description_html = models.TextField(blank=True,
        max_length=1000, help_text=_('Description in HTML.'), editable=False)

    # Relations
    project = models.ForeignKey(Project)
    unit = models.OneToOneField(Unit, blank=True, null=True, editable=False)
    pofiles = generic.GenericRelation(POFile)
    releases = models.ManyToManyField(CollectionRelease, related_name='components',
                                      blank=True, null=True)

    # Managers
    objects = ComponentManager()
        
    def __unicode__(self):
        return self.name

    def __repr__(self):
        return _('<Component: %s>') % self.full_name
    
    class Meta:
        unique_together = ("project", "slug")
        verbose_name = _('component')
        verbose_name_plural = _('components')
        db_table  = 'projects_component'
        ordering  = ('name',)
        get_latest_by = 'created'

    @cached_property
    def trans(self):
        """ 
        Cache TransHandler property field. 

        Allow the TransHandler initialization only when it is needed.
        """
        if self.id and self.i18n_type:
            handler_class = get_trans_handler(self.i18n_type)
            return handler_class(self)

    @permalink
    def get_absolute_url(self):
        return ('component_detail', None,
                { 'project_slug': self.project.slug,
                 'component_slug': self.slug })

    def get_pofiles(self):
        return POFile.objects.get_for_object(self)

    def get_full_name(self):
        return "%s.%s" % (self.project.slug, self.slug)

    def save(self, *args, **kwargs):
        desc_escaped = escape(self.long_description)
        self.long_description_html = markdown.markdown(desc_escaped)
        self.full_name = self.get_full_name()
        # Get a grip on the empty 'created' to detect a new addition. 
        created = self.created

        if self.id:
            component_old = Component.objects.get(id=self.id)
        else:
            component_old = None

        super(Component, self).save(*args, **kwargs)

        if self.unit:
            self.unit.name = self.full_name
            self.unit.save()

        if component_old and component_old.full_name != self.full_name:
            component_old.rename_static_dir(self.full_name)

        if not created and settings.ENABLE_NOTICES:
            notification.send(User.objects.all(), 
                              "projects_added_new_component",  
                              {'project': self.project, 
                              'component': self,})

    def delete(self, *args, **kwargs):
        self.clear_cache()
        if self.unit:
            self.unit.delete()
        super(Component, self).delete(*args, **kwargs)

    def set_unit(self, root, branch, type, web_frontend=None):
        """
        Associate a unit with this component.
        
        Another place the same functionality happens is when the Component
        form is saved.
        """
        if self.unit:
            self.unit.name = self.full_name
            self.unit.root = root
            self.unit.branch = branch
            self.unit.type = type
            self.unit.web_frontend = web_frontend
        else:
            logger.debug("Unit for %s not found. Creating." % self.full_name)
            try:
                u = Unit.objects.create(name=self.full_name, root=root, 
                                        branch=branch, type=type, 
                                        web_frontend=web_frontend)
                u.save()
                self.unit = u
            except IntegrityError:
                logger.error("Yow! Unit exists but is not associated with %s! "
                          % self.full_name)
                # TODO: Here we should probably send an e-mail to the 
                # admin, because something very strange would be happening
                pass

    def get_files(self):
        """Return a list of filtered files for the component."""
        return [f for f in self.unit.get_files(self.file_filter)]

    def prepare_repo(self):
        """
        Abstract unit.prepare_repo().

        This function creates/updates the Component local repository
        and then unset the TransHandler property cache for it be created
        again, with a new set of files, next time that it will be used.
        """
        logger.debug("Updating local repo for %s" % self.full_name)
        self.unit.prepare_repo()
        del(self.trans)

    def clear_cache(self):
        """
        Clear the local cache of the component.

        Delete statistics, teardown repo, remove static dir, rest unit.
        """ 
        logger.debug("Clearing local cache for %s" % self.full_name)
        try:
            self.trans.clear_stats()
            self.delete_static_dir()
            self.unit.teardown_repo()
            del(self.trans)
            if self.unit:
                self.delete_static_dir()
                self.unit.last_checkout = None
                self.unit.save()
        except:
             logger.error("Clearing cache failed for %s." % (self.full_name))
         
    def get_rev(self, path=None):
        """Get revision of a path from the underlying Unit"""
        return self.unit.get_rev(path)

    def submit(self, files, msg, user):
        return self.unit.submit(files, msg, user)

    # TODO: We might want to move the next two functions to another 
    # app later, like Utils or something
    def rename_static_dir(self, new_name):
        """Rename the directory of static content for a component"""
        import shutil
        try:
            original = os.path.join(settings.MSGMERGE_DIR, self.full_name)
            destination = os.path.join(settings.MSGMERGE_DIR, new_name)
            shutil.move(original, destination)
        except IOError:
            pass

    def delete_static_dir(self):
        """Delete the directory of static content for a component"""
        import shutil
        try:
            shutil.rmtree(os.path.join(settings.MSGMERGE_DIR, 
                                       self.full_name))
        except OSError:
            pass

log_model(Component)
log_model(Unit)
