import polib
from django import forms
from django.template.loader import render_to_string

from webtrans.fields import MessageField, PluralMessageField

def _guess_entry_status(entry):
    if entry.translated() and not entry.obsolete:
        return 'translated'
    elif 'fuzzy' in entry.flags:
        return 'fuzzy'
    elif not entry.translated() and not entry.obsolete:
        return 'untranslated'

def _get_label(msgid_list):
    """Return the label for a plural field."""
    return render_to_string('webtrans/msgid_label.html',
                            { 'msgid_list': msgid_list})


class TranslationForm(forms.Form):

    def __init__(self, po_entries, *args, **kwargs):
        super(TranslationForm, self).__init__(*args, **kwargs)
        k=1;
        for entry in po_entries:
            if entry.obsolete == 0:
                entry_status = _guess_entry_status(entry)
                fuzzy = False
                if entry_status == 'fuzzy':
                    fuzzy = True

                attrs = {'class':'%s msgstr_field_%s' % (entry_status, k),
                         'title':'%s' % polib.escape(entry.comment)}

                if entry.msgid_plural:
                    message_keys = entry.msgstr_plural.keys()
                    message_keys.sort()
                    messages = [entry.msgstr_plural[key] for key in message_keys]
                    msgstr_field = PluralMessageField(
                        entry=entry,
                        initial=messages,
                        help_text=self.help_text(entry),
                        label=_get_label([polib.escape(entry.msgid),
                            polib.escape(entry.msgid_plural)]),
                        attrs=attrs,
                        required=False,
                    )
                else:
                    msgstr_field = MessageField(
                        entry=entry,
                        initial=polib.escape(entry.msgstr),
                        help_text=self.help_text(entry),
                        attrs=attrs,
                        label=_get_label([polib.escape(entry.msgid)]),
                        required=False,
                        )

                msgid_field = MessageField(entry=entry, widget=forms.HiddenInput,
                    initial=polib.escape(entry.msgid))

                fuzzy_field = forms.BooleanField(required=False, initial=fuzzy)

                changed_field = forms.BooleanField(required=False, initial=False,
                    widget=forms.HiddenInput)

                self.fields['msgid_field_%s' % k] = msgid_field
                self.fields['fuzzy_field_%s' % k] = fuzzy_field
                self.fields['msgstr_field_%s' % k] = msgstr_field
                self.fields['changed_field_%s' % k] = changed_field

                k += 1;

    def help_text(self, entry):
        occurrences = ["%s (line %s)" % (file, line) for (file, line) in entry.occurrences]
        return '<small>%s</small>'% (', '.join(occurrences))
