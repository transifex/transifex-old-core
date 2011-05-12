# -*- coding: utf-8 -*-
import os
from datetime import datetime
import tagging
from tagging.fields import TagField
import markdown

from django.conf import settings
from django.core.cache import cache
from django.utils.translation import ugettext_lazy as _
from django.db import models, IntegrityError
from django.db.models import permalink, get_model, Q
from django.dispatch import Signal
from django.forms import ModelForm
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.utils.html import escape

from authority.models import Permission
from notification.models import ObservedItem

from transifex.actionlog.models import LogEntry
from transifex.txcommon.db.models import ChainerManager
from transifex.txcommon.log import log_model, logger
from transifex.projects.signals import project_created

class DefaultProjectQuerySet(models.query.QuerySet):
    """
    This is the default manager of the project model (assigned to objects field).
    """

    def watched_by(self, user):
        """
        Retrieve projects being watched by the specific user.
        """
        try:
            ct = ContentType.objects.get(name="project")
        except ContentType.DoesNotExist:
            pass
        observed_projects = [i[0] for i in list(set(ObservedItem.objects.filter(user=user, content_type=ct).values_list("object_id")))]
        watched_projects = []
        for object_id in observed_projects:
            try:
                watched_projects.append(Project.objects.get(id=object_id))
            except Project.DoesNotExist:
                pass
        return watched_projects

    def maintained_by(self,user):
        """
        Retrieve projects being maintained by the specific user.
        """
        return Project.objects.filter(maintainers__id=user.id)

    def translated_by(self, user):
        """
        Retrieve projects being translated by the specific user.

        The method returns all the projects in which user has been granted
        permission to submit translations.
        """
        try:
            ct = ContentType.objects.get(name="project")
        except ContentType.DoesNotExist:
            pass
        return Permission.objects.filter(user=user, content_type=ct, approved=True)

    def for_user(self, user):
        """
        Filter available projects based on the user doing the query. This
        checks permissions and filters out private projects that the user
        doesn't have access to.
        """
        projects = self
        if user in [None, AnonymousUser()]:
            projects = projects.filter(private=False)
        else:
            if not user.is_superuser:
                projects = projects.exclude(
                    Q(private=True) & ~(Q(maintainers__in=[user]) |
                    Q(team__coordinators__in=[user]) |
                    Q(team__members__in=[user]))).distinct()
        return projects

    def public(self):
        return self.filter(private=False)

    def private(self):
        return self.filter(private=True)


class PublicProjectManager(models.Manager):
    """
    Return a QuerySet of public projects.

    Usage: Projects.public.all()
    """

    def get_query_set(self):
        return super(PublicProjectManager, self).get_query_set().filter(private=False)

    def recent(self):
        return self.order_by('-created')

    def open_translations(self):
        #FIXME: This should look like this, more or less:
        #open_resources = Resource.objects.filter(accept_translations=True)
        #return self.filter(resource__in=open_resources).distinct()
        return self.all()


class Project(models.Model):
    """
    A project is a group of translatable resources.
    """

    private = models.BooleanField(default=False, verbose_name=_('Private'),
        help_text=_('A private project is visible only by you and your team.'
                    'Moreover, private projects are limited according to billing'
                    'plans for the user account.'))
    slug = models.SlugField(_('Slug'), max_length=30, unique=True,
        help_text=_('A short label to be used in the URL, containing only '
                    'letters, numbers, underscores or hyphens.'))
    name = models.CharField(_('Name'), max_length=50,
        help_text=_('A short name or very short description.'))
    description = models.CharField(_('Description'), blank=True, max_length=255,
        help_text=_('A sentence or two describing the object (optional).'))
    long_description = models.TextField(_('Long description'), blank=True,
        max_length=1000,
        help_text=_('A longer description (optional). Use Markdown syntax.'))
    homepage = models.URLField(_('Homepage'), blank=True, verify_exists=False)
    feed = models.CharField(_('Feed'), blank=True, max_length=255,
        help_text=_('An RSS feed with updates to the project.'))
    bug_tracker = models.URLField(_('Bug tracker'), blank=True,
        help_text=_('The URL for the bug and tickets tracking system '
                    '(Bugzilla, Trac, etc.)'))
    trans_instructions = models.URLField(_('Translator Instructions'), blank=True,
        help_text=_("A web page containing documentation or instructions for "
                    "translators, or localization tips for your community."))
    anyone_submit = models.BooleanField(_('Anyone can submit'),
        default=False, blank=False,
        help_text=_('Can anyone submit files to this project?'))

    hidden = models.BooleanField(_('Hidden'), default=False, editable=False,
        help_text=_('Hide this object from the list view?'))
    enabled = models.BooleanField(_('Enabled'),default=True, editable=False,
        help_text=_('Enable this object or disable its use?'))
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    tags = TagField(verbose_name=_('Tags'))

    # Relations
    maintainers = models.ManyToManyField(User, verbose_name=_('Maintainers'),
        related_name='projects_maintaining', blank=False, null=True)

    outsource = models.ForeignKey('Project', blank=True, null=True,
        verbose_name=_('Outsource project'),
        help_text=_('Project that owns the access control of this project.'))

    owner = models.ForeignKey(User, blank=True, null=True,
        editable=False, verbose_name=_('Owner'),
        help_text=_('The user who owns this project.'))

    # Normalized fields
    long_description_html = models.TextField(_('HTML Description'), blank=True,
        max_length=1000,
        help_text=_('Description in HTML.'), editable=False)

    # Reverse Relation for LogEntry GenericForeignkey
    # Allows to access LogEntry objects for a given project
    actionlogs = generic.GenericRelation(LogEntry,
        object_id_field="object_id", content_type_field="content_type")

    # Managers
    objects = ChainerManager(DefaultProjectQuerySet)
    public = PublicProjectManager()

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return repr(u'<Project: %s>' % self.name)

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
        if self.id is None:
            is_new = True
        else:
            is_new = False
        super(Project, self).save(*args, **kwargs)
        project_created.send(sender=self)

    def delete(self, *args, **kwargs):
        self.resources.all().delete()
        super(Project, self).delete(*args, **kwargs)

    @permalink
    def get_absolute_url(self):
        return ('project_detail', None, { 'project_slug': self.slug })

try:
    tagging.register(Project, tag_descriptor_attr='tagsobj')
except tagging.AlreadyRegistered, e:
    logger.debug('Tagging: %s' % str(e))

log_model(Project)
