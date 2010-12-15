from itertools import chain
from django import forms
from django.utils.html import escape, conditional_escape
from django.utils.encoding import force_unicode

class ReadOnlyWidget(forms.Widget):
    """Display a form field value as plain-text just for reading purposes."""
    def __init__(self, value):
        self.value = value

        super(ReadOnlyWidget, self).__init__()

    def render(self, name, value, attrs=None):
        return unicode(self.value)


class SelectWithDisabledOptions(forms.Select):
    """
    Custom Select widget to allow to display disabled options in a Select box.

    Just pass to ``disabled_choices`` the list of ``choices`` integer ids that
    should be disabled in the rendering.

    NOTE: This is only for redering purposes. Validation in a field or form
    level is still required.
    """
    def __init__(self, attrs=None, choices=(), disabled_choices=()):
        super(SelectWithDisabledOptions, self).__init__(attrs)
        self.choices = list(choices)
        self.disabled_choices = list(disabled_choices)

    def render_option(self, selected_choices, option_value, option_label):
        option_value = force_unicode(option_value)
        selected_html = (option_value in selected_choices) and u' selected="selected"' or ''
        disabled_html = (int(option_value) in self.disabled_choices) and u' disabled="disabled"' or ''
        return u'<option value="%s"%s>%s</option>' % (
            escape(option_value), selected_html + disabled_html,
            conditional_escape(force_unicode(option_label)))