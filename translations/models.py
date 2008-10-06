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

class POStatistic(models.Model):
    """
    A Statistic is a collection of information about translations stats
    of a component in a language.
    
    # Test Language creation
    >>> from translations.models import Language
    >>> l = Language.objects.create(code='pt_BR', name='Brazilian Portuguese')
    >>> l.save()
    >>> from translations.models import POStatistic
    >>> from projects.models import Project
    >>> p = Project.objects.create(slug="foobar", name="Foo Project")
    >>> s = POStatistic.objects.create(lang=l, object=p)
    >>> s.save()
    >>> print s.lang.code
    pt_BR

    # Take the a list of objects for a object
    >>> ps = POStatistic.get_stats_for_object(p)
    >>> print ps[0].lang.code
    pt_BR

    # Take the a list of objects for a lang
    >>> ps = POStatistic.get_stats_for_lang(l)
    >>> print ps[0].lang.code
    pt_BR

    # Take the a list available languages for a project
    >>> langs = POStatistic.get_langs_for_object(p)
    >>> print langs[0].code
    pt_BR

    # Take the a list available languages for a project
    >>> POStatistic.delete_stats_for_object(p)
    >>> langs = POStatistic.get_langs_for_object(p)
    >>> print langs
    []

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
        super(POStatistic, self).save(*args, **kwargs)

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
    def get_stats_for_object(self, object):
        """ Returns a list of languages statistics for an object."""
        return self.objects.filter(object_id=object.id).order_by('-trans_perc')
    
    @classmethod
    def get_stats_for_lang(self, lang):
        """ Returns a list of objects statistics for a language."""
        return self.objects.filter(lang=lang).order_by('-trans_perc')

    @classmethod
    def get_stats_for_lang_object(self, lang, object):
        """ Returns statistics for an object in a specific language."""
        try: 
            return self.objects.filter(lang=lang, object_id=object.id)[0]
        except:
            return POStatistic(lang=lang, object=object)

    @classmethod
    def get_langs_for_object(self, object):
        """ Returns a list of languages availables for an object."""
        langs = []
        for obj in self.objects.filter(object_id=object.id):
            langs.append(obj.lang)
        return langs

    @classmethod
    def delete_stats_for_object(self, object):
        """ Delete all lang statistics of an object."""
        self.objects.filter(object_id=object.id).delete()

        