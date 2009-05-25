import re
from django import forms
from django.utils.safestring import mark_safe
from django.utils.html import escape

from projects.models import Project, Component

rx = re.compile(r'(%(\([^\s\)]*\))?[sd])')

##################

def mark_code(text):
    replacement = escape(text).replace(r'\n','<br />\n')
    return mark_safe(rx.sub('<code class="ph">\\1</code>', replacement))

def calculate_rows(entry):
    text = getattr(entry, 'msgid', entry)
    replacement = escape(text).replace(r'\n','<br />\n')
    lines = mark_safe(replacement).split(u'\n')
    return sum(len(line)/40 for k, line in enumerate(lines)) + 1

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
        if not widget:
            widget=MessageWidget(attrs={'rows': calculate_rows(entry),
                                        'cols': 50,},)
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
        for k, entry in enumerate(po_entries[0:10]):
            if entry.msgid_plural:
                message_keys = entry.msgstr_plural.keys()
                message_keys.sort()
                messages = [entry.msgstr_plural[key] for key in message_keys]
                field = PluralMessageField(
                    entry=entry,
                    initial=messages,
                    label=entry.msgid,
                    help_text=self.help_text(entry),
                    widget=PluralMessageWidget(messages=messages),
                )
            else:
                field = MessageField(
                    entry=entry,
                    initial=entry.msgstr,
                    help_text=self.help_text(entry),
                    label=mark_code(entry.msgid),)
            self.fields['field_%s' % k] = field

    def help_text(self, entry):
        occurrences = ["%s (line %s)" % (file, line) for (file, line) in entry.occurrences]
        return '<small>%s</small>'% (', '.join(occurrences))
