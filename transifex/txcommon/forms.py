from django import forms
from contact_form.forms import ContactForm
from userena.forms import EditProfileForm as UserenaEditProfileForm
from userena.utils import get_profile_model


class EditProfileForm(UserenaEditProfileForm):

    def __init__(self, *args, **kw):
        super(forms.ModelForm, self).__init__(*args, **kw)

    class Meta:
        model = get_profile_model()
        exclude = ('user', 'privacy',)
        fields = ('first_name', 'last_name', 'location', 'languages', 'mugshot', 'blog',
            'linked_in', 'twitter', 'about', 'looking_for_work')
            



class CustomContactForm(ContactForm):

    subject = forms.CharField(max_length=150, widget=forms.TextInput())

    def __init__(self, data=None, files=None, request=None, *args, **kwargs):
        super(CustomContactForm, self).__init__(data=data, files=files, 
            request=request, *args, **kwargs)
        self.fields.keyOrder = ['name', 'email', 'subject', 'body']