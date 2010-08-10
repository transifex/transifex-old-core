# -*- coding: utf-8 -*-

from hashlib import md5
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _

from happix.models import Resource, SourceEntity
from languages.models import Language

class Suggestion(models.Model):
    """
    The representation of a suggestion for a translation on a source string.
    
    More or less it is a duplication of the Translation model with a differrent
    way to determine the unique instances.
    """

    string = models.TextField(_('String'), blank=False, null=False,
        help_text=_("The actual string content of suggestion."))
    string_hash = models.CharField(_('String Hash'), blank=False, null=False,
        max_length=32, editable=False,
        help_text=_("The hash of the suggestion string used for indexing"))
    score = models.FloatField(_('Score Value'), default=0, blank=True,
        help_text=_("A value which indicates the relevance of this suggestion"
                    "to the translation of the source string."))

    # Timestamps
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_update = models.DateTimeField(auto_now=True, editable=False)

    # Foreign Keys
    source_entity = models.ForeignKey(SourceEntity,
        verbose_name=_('Source Entity'),
        blank=False, null=False,
        help_text=_("The source entity which is being translated by this"
                    "suggestion instance."))

    language = models.ForeignKey(Language,
        verbose_name=_('Target Language'),blank=False, null=True,
        help_text=_("The language in which this suggestion string belongs to."))

    resource = models.ForeignKey(Resource, verbose_name=_('Resource'),
        blank=False, null=False,
        help_text=_("The translation resource which owns the source string."))

    user = models.ForeignKey(User,
        verbose_name=_('User'), blank=False, null=True,
        help_text=_("The user who committed the specific suggestion."))

    voters = models.ManyToManyField(User, through='Vote',
        verbose_name=_('Voters'), blank=True, null=True, related_name='voters',
        help_text=_("Users who has voted for this suggestion"))

    #TODO: Managers

    def __unicode__(self):
        return self.string

    class Meta:
        unique_together = (('source_entity', 'string_hash', 'language',
            'resource'),)
        verbose_name = _('suggestion')
        verbose_name_plural = _('suggestion')
        ordering  = ('-score',)
        order_with_respect_to = 'source_entity'

    def vote_up(self, user):
        vote, created = Vote.objects.get_or_create(user=user, suggestion=self,
            defaults={ 'vote_type': True })
        if created:
            self.score += 1
            self.save()
        else:
            # Undo the previous choice
            if vote.vote_type==True:
                vote.delete()
                self.score -= 1
                self.save()
            # Changed opinion and votes up instead of down.
            else:
                vote.vote_type = True
                vote.save()
                self.score += 2
                self.save()

    def vote_down(self, user):
        vote, created = Vote.objects.get_or_create(user=user, suggestion=self,
            defaults={ 'vote_type': False })
        if created:
            self.score -= 1
            self.save()
        else:
            # Undo the previous choice
            if vote.vote_type==False:
                vote.delete()
                self.score += 1
                self.save()
            # Changed opinion and votes up instead of down.
            else:
                vote.vote_type = False
                vote.save()
                self.score -= 2
                self.save()

    @property
    def integer_score(self):
        return int(self.score)

    def save(self, *args, **kwargs):
        """
        Do some exra processing before the actual save to db.
        """
        # encoding happens to support unicode characters
        self.string_hash = md5(self.string.encode('utf-8')).hexdigest()
        super(Suggestion, self).save(*args, **kwargs)


class Vote(models.Model):
    """
    A user vote for a suggestion.
    """
    suggestion = models.ForeignKey(Suggestion,
        verbose_name=_('Suggestion'), blank=False, null=False,
        help_text=_("The suggestion which is being voted."))
    user = models.ForeignKey(User,
        verbose_name=_('User'), blank=False, null=False,
        help_text=_("The user who voted the specific suggestion."))

     # False = -1, True = +1
    vote_type = models.BooleanField()

    # Timestamps
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_update = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        unique_together = (('suggestion', 'user'))
        verbose_name = _('vote')
        verbose_name_plural = _('votes')

