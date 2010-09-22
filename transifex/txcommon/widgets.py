from django import forms

class ReadOnlyWidget(forms.Widget):
    """Display a form field value as plain-text just for reading purposes."""
    def __init__(self, value):
        self.value = value

        super(ReadOnlyWidget, self).__init__()

    def render(self, name, value, attrs=None):
        return unicode(self.value)
