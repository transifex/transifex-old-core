from datetime import datetime
from django.contrib import admin
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

class Language(models.Model):
    """
    A Language is a code and name collection of languages.
    
    # Test Language creation
    >>> from translations.models import Language
    >>> l = Language.objects.create(code='pt_BR', name='Brazilian Portuguese')
    >>> l.save()
    >>> print l.code
    pt_BR
    >>> l.delete()
    
    """
    code = models.CharField(max_length=15)
    name = models.CharField(max_length=50)

#class LanguageAdmin(admin.ModelAdmin):
#    prepopulated_fields = {'slug': ('code',)}
#admin.site.register(Language, LanguageAdmin)

class POFile(models.Model):
    """
    A Statistic is a collection of information about translations stats
    of a component in a language.
    
    # Test Language creation
    >>> from translations.models import Language
    >>> l = Language.objects.create(code='pt_BR', name='Brazilian Portuguese')
    >>> l.save()
    >>> from translations.models import POFile
    >>> from projects.models import Project
    >>> p = Project.objects.create(slug="foobar", name="Foo Project")
    >>> s = POFile.objects.create(lang=l, object=p)
    >>> s.save()
    >>> print s.lang.code
    pt_BR

    # Take the a list of objects for a lang
    >>> ps = POFile.stats_for_lang(l)
    >>> print ps[0].lang.code
    pt_BR

    # Delete objects
    >>> p.delete()
    >>> l.delete()
    >>> s.delete()
    """    
    total = models.PositiveIntegerField(default=0)
    trans = models.PositiveIntegerField(default=0)
    fuzzy = models.PositiveIntegerField(default=0)
    untrans = models.PositiveIntegerField(default=0)

    trans_perc = models.PositiveIntegerField(default=0, editable=False)
    fuzzy_perc = models.PositiveIntegerField(default=0, editable=False)
    untrans_perc = models.PositiveIntegerField(default=100, editable=False)

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    object = generic.GenericForeignKey('content_type', 'object_id')
    
    lang = models.ForeignKey(Language, null=True)
    filename = models.TextField(null=False, max_length=1000)

    enabled = models.BooleanField(default=True)
    created = models.DateField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.modified = datetime.now()
        super(POFile, self).save(*args, **kwargs)

    def calulate_perc(self):
        if self.total != 0:
            self.trans_perc = self.trans*100/self.total
            self.fuzzy_perc = self.fuzzy*100/self.total
            self.untrans_perc = self.untrans*100/self.total
        else:
            self.trans_perc = 0
            self.fuzzy_perc = 0
            self.untrans_perc = 100
        
    def set_stats(self, trans=0, fuzzy=0, untrans=0):
        """ Initialize the object"""
        self.total = trans + fuzzy + untrans
        self.trans = trans
        self.fuzzy = fuzzy
        self.untrans = untrans
        self.calulate_perc()

    @classmethod
    def stats_for_lang(self, lang):
        """ Returns a list of objects statistics for a language."""
        return self.objects.filter(lang=lang).order_by('-trans_perc')
        