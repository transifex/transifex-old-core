# -*- coding: utf-8 -*-
import polib
from django import forms
from django.template.loader import render_to_string

from webtrans.fields import MessageField, PluralMessageField

def _guess_entry_status(entry, key, data):
    """
    Return a string referring to the status of a POFile entry in a form.

    ``entry`` is a polib.POEntry.
    ``key`` is the key related to the form field position.
    ``data`` is used for populating a form from the session. 

    Usually ``data`` is the request.POST passed to the form. This parameter can 
    receive the saved wizard session related to the specific form, which might 
    have changed fields with different status than the original polib.POEntry.

    """
    if data:
        if not entry.msgid_plural:
            msgstr_field = data.get('msgstr_field_%s' % key, None)
        else:
            msgstr_field = data.get('msgstr_field_%s_0' % key, None)

        fuzzy_field = data.get('fuzzy_field_%s' % key, None)
        if fuzzy_field:
            return 'fuzzy'
        elif msgstr_field:
            return 'translated'
        else:
            return 'untranslated'
    else:
        if entry.translated() and not entry.obsolete:
            return 'translated'
        elif 'fuzzy' in entry.flags:
            return 'fuzzy'
        elif not entry.translated() and not entry.obsolete:
            return 'untranslated'

def _get_label(msgid_list):
    """Return the label for a field."""
    return render_to_string('webtrans/msgid_label.html',
                            { 'msgid_list': msgid_list })

class TranslationForm(forms.Form):
    """
    Return a form created dynamicaly using a list of PO files entries.

    ``po_entries`` is a list of polib.POEntry objects.

    """
    def __init__(self, po_entries, *args, **kwargs):
        super(TranslationForm, self).__init__(*args, **kwargs)
        if po_entries:
            for k, entry in enumerate(po_entries):
                status = _guess_entry_status(entry, k, kwargs.get('data', None))
                attrs = {'class': '%s msgstr_field_%s' % (status, k)}

                if 'fuzzy' in entry.flags:
                    fuzzy=True
                else:
                    fuzzy=False

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

                self.fields['msgid_field_%s' % k] = msgid_field
                self.fields['fuzzy_field_%s' % k] = fuzzy_field
                self.fields['msgstr_field_%s' % k] = msgstr_field

    def help_text(self, entry):
        """Return the comments of a field."""
        occurrences = ["%s (line %s)" % (file, line) for (file, line) in entry.occurrences]
        return render_to_string('webtrans/comments.html', {
            'comment': polib.escape(entry.comment),
            'msgctxt': entry.msgctxt,
            'occurrences': '%s' % ('\n'.join(occurrences)),})

