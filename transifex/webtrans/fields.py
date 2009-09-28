import polib
from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

def _calculate_rows(entry):
    """Return the estimated number of rows for a textarea based on string size."""
    text = getattr(entry, 'msgid', entry)
    if isinstance(text, str):
        text = text.decode(getattr(entry, 'encoding', 'UTF-8'))
    replacement = polib.escape(text).replace(r'\n','<br />\n')
    lines = mark_safe(replacement).split(u'\n')
    return sum(len(line)/40 for k, line in enumerate(lines)) + 1


class PluralMessageWidget(forms.MultiWidget):
    """A widget to render plural translatable strings."""
    def __init__(self, messages, attrs=None):
        widgets=[]
        for i, entry in enumerate(messages):
            widgets.append(forms.Textarea(attrs=attrs))
        super(PluralMessageWidget, self).__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            return value.split('#|#')
        return ['']


class PluralMessageField(forms.MultiValueField):
    """A field for plural translatable strings."""
    def __init__(self, entry, initial, attrs={}, widget=None, *args, **kwargs):
        attrs.update({'rows': _calculate_rows(entry)})
        fields = []
        for i in initial:
            fields.append(forms.CharField(label=entry.msgid_plural))

        if not widget:
            widget=PluralMessageWidget(initial, attrs=attrs)
        super(PluralMessageField, self).__init__(fields, initial=initial, 
            widget=widget, *args, **kwargs)

    def compress(self, data_list):
        if data_list:
            return "#|#".join(unicode(data) for data in data_list)
        return None

    def clean(self, value):
        """Plural fields should either be all filled or all leaved as blank."""
        number=0
        for v in value:
            if v=='':
                number = number+1
        if number != 0 and number != len(value):
            raise forms.ValidationError(_('The %s fields should be filled.') % 
                                          len(value))
        return value


class MessageField(forms.CharField):
    """A field for translatable strings."""
    def __init__(self, entry, attrs={}, widget=None, *args, **kwargs):
        attrs.update({'rows': _calculate_rows(entry)})
        if not widget:
            widget=MessageWidget(attrs=attrs)
        super(MessageField, self).__init__(attrs, widget=widget, *args, **kwargs)


class MessageWidget(forms.Textarea):
    """A widget to render translatable strings."""
    def __init__(self, attrs=None, *args, **kwargs):
        super(MessageWidget, self).__init__(attrs, *args, **kwargs)
