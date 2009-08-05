import re
import polib
from django import forms
from django.utils.safestring import mark_safe

from projects.models import Project, Component

##################

def calculate_rows(entry):
    text = getattr(entry, 'msgid', entry)
    if isinstance(text, str):
        text = text.decode(getattr(entry, 'encoding', 'UTF-8'))
    replacement = polib.escape(text).replace(r'\n','<br />\n')
    lines = mark_safe(replacement).split(u'\n')
    return sum(len(line)/40 for k, line in enumerate(lines)) + 1

def guess_entry_status(entry):
    if entry.translated() and not entry.obsolete:
        return 'translated'
    elif 'fuzzy' in entry.flags:
        return 'fuzzy'
    elif not entry.translated() and not entry.obsolete:
        return 'untranslated'

##################

class PluralMessageWidget(forms.MultiWidget):

    def __init__(self, messages, attrs=None):
        widgets=[]
        for i, entry in enumerate(messages):
            widgets.append(forms.Textarea({'rows': calculate_rows(entry)}))
        super(PluralMessageWidget, self).__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            return value.split('#|#')
        return ['']

class PluralMessageField(forms.MultiValueField):
    def __init__(self, entry, initial, *args, **kwargs):
        fields = []
        for i in initial:
            fields.append(forms.CharField(label=entry.msgid_plural))
        super(PluralMessageField, self).__init__(fields, initial=initial, *args, **kwargs)

    def compress(self, data_list):
        if data_list:
            return "#|#".join(unicode(data) for data in data_list)
        return None

#####################

class MessageField(forms.CharField):
    """A field for translatable strings."""
    def __init__(self, entry, attrs=None, widget=None, *args, **kwargs):
        self.occurrences=entry.occurrences
        if not attrs:
            attrs = {}
        attrs.update({'rows': calculate_rows(entry), 'cols': 30,})
        if not widget:
            widget=MessageWidget(attrs=attrs)
        super(MessageField, self).__init__(attrs, widget=widget,
                                           *args, **kwargs)

class MessageWidget(forms.Textarea):
    """A widget to render translatable strings."""
    def __init__(self, attrs=None, *args, **kwargs):
        super(MessageWidget, self).__init__(attrs, *args, **kwargs)

######################

class ObjectPaginatorIterator(object):
    def __init__(self, paginator, page_num):
        self.paginator = paginator 
        self.page_num = page_num

    def __iter__(self):
        for obj in self.paginator.get_page (self.page_num):
            yield (obj._get_pk_val(), smart_unicode(obj))

#######################

class TranslationForm(forms.Form):

    def __init__(self, po_entries, *args, **kwargs):
        super(TranslationForm, self).__init__(*args, **kwargs)
        k=1;
        for entry in po_entries:
            if entry.obsolete == 0:
                entry_status = guess_entry_status(entry)
                fuzzy = False
                if entry_status == 'fuzzy':
                    fuzzy = True

                if entry.msgid_plural:
                    #TODO: It does not support pural entries yet
                    #message_keys = entry.msgstr_plural.keys()
                    #message_keys.sort()
                    #messages = [entry.msgstr_plural[key] for key in message_keys]
                    #field = PluralMessageField(
                        #entry=entry,
                        #initial=messages,
                        #label=mark_safe('<p>%s</p><p>%s</p>' % (entry.msgid, 
                                                                #entry.msgid_plural)),
                        #help_text=self.help_text(entry),
                        #widget=PluralMessageWidget(messages=messages),
                    #)
                    #msgid_field = PluralMessageField(
                        #entry=entry,
                        #initial=messages,
                        #widget=PluralSourceMessageWidget(messages=messages),
                    #)
                    pass
                else:
                    msgstr_field = MessageField(
                        entry=entry,
                        initial=polib.escape(entry.msgstr),
                        help_text=self.help_text(entry),
                        attrs={'class':'%s' % entry_status,
                               'title':'%s' % polib.escape(entry.comment),
                              },
                        label=polib.escape(entry.msgid)#.replace(r'\n','\\n<br />')
                        )
                    msgid_field = MessageField(widget=forms.HiddenInput,
                        entry=entry,
                        initial=polib.escape(entry.msgid),
                        )
                    fuzzy_field = forms.BooleanField(
                        required=False,
                        initial=fuzzy,
                        )
                    changed_field = forms.BooleanField(
                        widget=forms.HiddenInput,
                        required=False,
                        initial=False,
                        )

                    self.fields['msgid_field_%s' % k] = msgid_field
                    self.fields['fuzzy_field_%s' % k] = fuzzy_field
                    self.fields['msgstr_field_%s' % k] = msgstr_field
                    self.fields['changed_field_%s' % k] = changed_field
                k += 1;

    def help_text(self, entry):
        occurrences = ["%s (line %s)" % (file, line) for (file, line) in entry.occurrences]
        return '<small>%s</small>'% (', '.join(occurrences))
