# -*- coding: utf-8 -*-
import operator
from datetime import datetime
from django.db import models
from django.db.models import permalink
from django.template.defaultfilters import dictsort, dictsortreversed
from django.utils.translation import ugettext_lazy as _
from django.utils.itercompat import groupby
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from languages.models import Language
from simplelock.models import Lock
from txcommon.db.models import IntegerTupleField
from txcommon.notifications import is_watched_by_user_signal


def _group_pofiles(postats, grouping_key, pot_total):
    """
    Yield a virtual POFile grouped and summed by using a set of POFiles passed 
    by parameter that have the same grouping_key, passed also by parameter

    This function is responsible for the aggregation of POFiles, summing the 
    statistics of each POFile and yield the virtual POFile resulted from the
    operation. This virtual POfile has some extra attributes as 'is_aggregated'
    and 'counter'.

    This virtual object is not stored in the database.

    Parameters:
    postats: This is the set of POFiles to be aggregated
    grouping_key: A attribute from the POFile model to use it for grouping the 
                  postats
    pot_total: This is the total (sum) of strings from the source files relative
               to the set of POFiles.

    """
    from txcommon.log import logger
    grouped_postats = groupby(postats, key=operator.attrgetter(grouping_key))

    for key, pofiles in grouped_postats:
        count = po_trans = po_fuzzy = po_untrans = po_total = 0 
        for pofile in pofiles:
            po_trans += pofile.trans
            po_fuzzy += pofile.fuzzy
            po_untrans += pofile.untrans
            po_total += pofile.total
            count += 1
        if pot_total and pot_total > po_total:
            # Compare the total of entries between POT and PO
            # We need to sum entries as untranslated for languages 
            # that even are not present in a component
            no_po = pot_total - po_total
        else:
            no_po = 0

        # It uses the last pofile present at the 'pofiles' for aggregating the
        # stats sum. As it doesn't save the objects, it's safe to re-use then
        # in order to save memory.
        pofile.set_stats(po_trans, po_fuzzy, (po_untrans + no_po))

        if count > 1:
            pofile.is_aggregated=True
        else:
            pofile.is_aggregated=False

        pofile.counter = count
        yield pofile


class POFileManager(models.Manager):
    def by_object(self, obj):
        """
        Create a queryset matching all POFiles associated with the given
        object.
        """
        ctype = ContentType.objects.get_for_model(obj)
        return self.filter(content_type__pk=ctype.pk,
                           object_id=obj.pk).order_by('-trans_perc')

    def by_language(self, language):
        """Return a list of objects statistics for a language."""
        return self.filter(language=language)

    def by_release(self, release):
        """
        Return a QuerySet for a specific release.
        
        No ordering can take place here. Use key_dict instead.
        """
        ctype = ContentType.objects.get(app_label='projects', model='component')
        comp_query = release.components.values('pk').query
        return self.filter(content_type=ctype, object_id__in=comp_query)

    def by_release_and_language(self, release, language):
        """
        Return a list of stats object for a release and language.
        """
        return self.by_release(release).filter(language=language)

    def by_language_and_release(self, language, release):
        """
        Return a list of stats object for a language and release.
        """
        return self.by_release(release).filter(language=language)

    def by_lang_code_and_object(self, language_code, obj):
        """
        Return a list of stats for a language and object.
        """
        return self.by_object(obj).filter(language_code=language_code)

    def by_release_total(self, release):
        """
        Return a virtual POFile for every language in a release.
        
        This POFile object aggregates the language total statistics in a
        particular release. All POFile objects for each language-release tuple
        are added together, generating a total number for this release. This is
        mimicking something like: 'SELECT SUM(POFile.total) GROUP BY RELEASE'.
        
        This object is not stored in the database.
        """
        postats = self.by_release(release).filter(is_pot=True).values_list(
            'total', flat=True)
        pot_total = sum(postats)

        postats = self.by_release(release).filter(is_pot=False,
                                                  language__isnull=False)
        return _group_pofiles(postats, 'sort_id', pot_total)

    def by_object_total(self, obj):
        """
        Return a virtual POFile for every language in an object.
        
        This POFile object aggregates the language total statistics in a
        particular object. All POFile objects for each language-object tuple
        are added together, generating a total number for this object. This is
        mimicking something like: 'SELECT SUM(POFile.total) GROUP BY OBJECT'.
        
        This object is not stored in the database.
        """

        postats = self.by_object(obj).filter(is_pot=True).values_list(
            'total', flat=True)
        pot_total = sum(postats)

        postats = self.by_object(obj).filter(
            is_pot=False).order_by('language_code')

        return _group_pofiles(postats, 'sort_id', pot_total)


    def by_language_and_release_total(self, language, release):
        """
        Return a virtual POFile for every language in an Language x Release.
        
        This POFile object aggregates the language total statistics in a
        particular object. All POFile objects for each language-relation tuple
        are added together, generating a total number for this object.
        
        This object is not stored in the database.
        """
        postats = self.by_language_and_release(language, release).filter(
            is_pot=True).values_list('total', flat=True)
        pot_total = sum(postats)

        postats = self.by_language_and_release(language, release).filter(
            is_pot=False).order_by('object_id')

        return _group_pofiles(postats, 'object_id', pot_total)

    def by_release_and_language_total(self, release, language):
        return self.by_language_and_release_total(language, release)

class POFile(models.Model):
    """
    A POFile is a representation of a PO file structure.
    
    It can either be a real PO file on a repository, a
    dynamically-generated one, etc. It represents the translation
    of a component to a language. The model's basic use is the
    calculation of translation statistics.    
    """

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    object = generic.GenericForeignKey('content_type', 'object_id')
    
    total = models.PositiveIntegerField(default=0)
    trans = models.PositiveIntegerField(default=0)
    fuzzy = models.PositiveIntegerField(default=0)
    untrans = models.PositiveIntegerField(default=0)
    
    language = models.ForeignKey(Language, null=True)
    language_code = models.CharField(null=True, max_length=20)
    filename = models.CharField(null=False, max_length=255, db_index=True)

    # This field is used to indicate whenever a file was created 
    # by the system, even a POT file through intltool-update
    # We might rename it later
    is_msgmerged = models.BooleanField(default=True, editable=False)
    is_pot = models.BooleanField(default=False, editable=False, db_index=True)

    enabled = models.BooleanField(default=True, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)
    error = models.BooleanField(default=False, editable=False)
    
    # Normalized fields
    trans_perc = models.PositiveIntegerField(default=0, editable=False)
    fuzzy_perc = models.PositiveIntegerField(default=0, editable=False)
    untrans_perc = models.PositiveIntegerField(default=100, editable=False)

    rev = IntegerTupleField(max_length=64, null=True,
        help_text='Latest revision seen')

    # Managers
    objects = POFileManager()

    def __unicode__(self):
        return u"%(file)s (%(type)s %(obj)s)" % {
            'file': self.filename,
            'type': self.content_type,
            'obj': self.object,}

    @property
    def sort_id(self):
        if self.language:
            return self.language.name.lower()
        elif self.language_code:
            return self.language_code.lower()
        else:
            # In case no language was found to the POFile
            return self.filename.lower()

    @property
    def lang_or_code(self):
        return self.language or self.language_code

    class Meta:
        unique_together = ("content_type", "object_id", "filename")
        verbose_name = _('PO file')
        verbose_name_plural = _('PO files')
        db_table  = 'translations_pofile'
        ordering  = ('language__name',)
        get_latest_by = 'created'
        
    def save(self, *args, **kwargs):
        self.calculate_perc()
        super(POFile, self).save(*args, **kwargs)

    def calculate_perc(self):
        """Update normalized percentage statistics fields."""
        if (hasattr(self.object, 'should_calculate') and
            self.object.should_calculate):
            try:
                self.trans_perc = self.trans * 100 / self.total
                self.fuzzy_perc = self.fuzzy * 100 / self.total
                self.untrans_perc = self.untrans * 100 / self.total
            except ZeroDivisionError:
                self.trans_perc = 0
                self.fuzzy_perc = 0
                self.untrans_perc = 0

    def set_stats(self, trans=0, fuzzy=0, untrans=0, error=False):
        if (hasattr(self.object, 'should_calculate') and
            self.object.should_calculate):
            self.total = trans + fuzzy + untrans
            self.trans = trans
            self.fuzzy = fuzzy
            self.untrans = untrans
            self.error = error
            self.calculate_perc()

    @property
    def locked(self):
        if self.locks.all():
            return True
        else:
            return False
    @property
    def symbolic_path(self):
        """Return a path in the form project/component/pofile_path."""
        path = self.object.trans.tm.get_file_path(self.filename)
        return '%s/%s/%s' % (self.object.project.slug,
                                 self.object.slug,
                                 self.filename)

    def is_watched_by(self, user, signal=None):
        return is_watched_by_user_signal(self, user, signal)

class POFileLock(Lock):
    """A lock/hold on a POFile object."""
    
    pofile = models.ForeignKey(POFile, related_name='locks', null=True)

    class Meta(Lock.Meta):
        db_table = 'translations_pofile_lock'
        unique_together = ('pofile', 'owner')

    def __unicode__(self):
        return u"%(pofile)s (%(owner)s)" % {
            'owner': self.owner,
            'pofile': self.pofile.filename,}

def suite():
    """
    Define the testing suite for Django's test runner.
    
    Enables test execution with ``./manage.py test <appname>``.
    """
     
    import unittest
    import doctest
    s = unittest.TestSuite()

    #FIXME: Load tests automatically:
    #    for vcs_type in settings.VCS_CHOICES:
    #        vcs_browser = import_to_python('vcs.lib.types' % vcs_type)
    #        s.addTest(doctest.DocTestSuite(vcs_browser))
    from translations.tests import test_models 
    s.addTest(doctest.DocTestSuite(test_models))
        
    return s
