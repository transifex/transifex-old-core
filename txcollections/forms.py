from django import forms
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.db.models import permalink
from django.contrib.admin import widgets    

from txcollections.models import (CollectionRelease as Release, Collection)

#TODO: Abstract this to re-use across applications
class ReleaseForm(forms.ModelForm):
    class Meta:
        model = Release

    def __init__(self, collection, *args, **kwargs):
        super(ReleaseForm, self).__init__(*args, **kwargs)
        collections = self.fields["collection"].queryset.filter(slug=collection.slug)
        self.fields["collection"].queryset = collections
        self.fields["collection"].empty_label = None
