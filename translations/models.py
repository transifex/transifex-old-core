# -*- coding: utf-8 -*-
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


class POFileManager(models.Manager):
    def get_for_object(self, obj):
        """
        Create a queryset matching all POFiles associated with the given
        object.
        """
        ctype = ContentType.objects.get_for_model(obj)
        return self.filter(content_type__pk=ctype.pk,
                           object_id=obj.pk)

    def by_language(self, language):
        """ Return a list of objects statistics for a language."""
        return self.filter(language=language)

    def by_release(self, release):
        """ Return a QuerySet for a specific release """
        ctype = ContentType.objects.get(app_label='projects', model='component')
        comp_query = release.components.values('pk').query
        return self.filter(content_type=ctype, object_id__in=comp_query)

    def by_language_and_release(self, language, release):
        """ 
        Return a list of stats object for a language and release.
        """
        return self.by_release(release).filter(language=language)


    def by_release_total(self, release):
        """
        Yield a POFile for every language in a release containing the language
        total statistics
        """
        postats = self.by_release(release).filter(is_pot=True).values('total')
        pot_total = sum(postat['total'] for postat in postats)

        postats = self.by_release(release).filter(is_pot=False,
                                                  language__isnull=False)

        grouped_postats = groupby(postats, key=lambda po:po.language)

        for lang, pofiles in grouped_postats:
            po_trans = po_fuzzy = po_untrans = po_total = 0 
            for pofile in pofiles:
                po_trans += pofile.trans
                po_fuzzy += pofile.fuzzy
                po_untrans += pofile.untrans
                po_total += pofile.total

            if pot_total and pot_total > po_total:
                # Compare the total of entries between POT and PO
                # We need to sum entries as untranslated for languages 
                # that even are not present in a component
                no_po = pot_total - po_total
            else:
                no_po = 0

            po = self.model(trans=po_trans,
                            fuzzy=po_fuzzy, 
                            untrans=po_untrans + no_po, 
                            total=po_total + no_po, 
                            filename=lang.code, # Not used but needed
                            object=lang, # Not used but needed
                            language=lang)
            po.calculate_perc()
            yield po


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
    filename = models.CharField(null=False, max_length=255)

    # This field is used to indicate whenever a file was created 
    # by the system, even a POT file through intltool-update
    # We might rename it later
    is_msgmerged = models.BooleanField(default=True, editable=False)
    is_pot = models.BooleanField(default=False, editable=False)

    enabled = models.BooleanField(default=True, editable=False)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)
    error = models.BooleanField(default=False, editable=False)
    
    # Normalized fields
    trans_perc = models.PositiveIntegerField(default=0, editable=False)
    fuzzy_perc = models.PositiveIntegerField(default=0, editable=False)
    untrans_perc = models.PositiveIntegerField(default=100, editable=False)

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
        else:
            return self.filename.lower()

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
        try:
            self.trans_perc = self.trans * 100 / self.total
            self.fuzzy_perc = self.fuzzy * 100 / self.total
            self.untrans_perc = self.untrans * 100 / self.total
        except ZeroDivisionError:
            self.trans_perc = 0
            self.fuzzy_perc = 0
            self.untrans_perc = 0

    def set_stats(self, trans=0, fuzzy=0, untrans=0, error=False):
        self.total = trans + fuzzy + untrans
        self.trans = trans
        self.fuzzy = fuzzy
        self.untrans = untrans
        self.error = error
        self.calculate_perc()
    
    def guess_lang(self):
        """
        Try to find the language of the POFile.

        Return None if guesswork fails.
        This method is currently specific to <lang>.po files.        
        """
        # FIXME: Per-i18n-type functionality is stroed in the transmanager,
        # and this method should be there. Or, we should have this model
        # tied to a particular manager. Design decision needed.

        from os.path import basename
        try:
            lang_code = basename(self.filename[:-3:])
            return Language.objects.get(code=lang_code)
        except:
            return

    @property
    def locked(self):
        if self.locks.all():
            return True
        else:
            return False

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
