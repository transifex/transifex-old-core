from django import forms
from userena.forms import EditProfileForm as UserenaEditProfileForm
from userena.utils import get_profile_model

class EditProfileForm(UserenaEditProfileForm):

    def __init__(self, *args, **kw):
        super(forms.ModelForm, self).__init__(*args, **kw)

    class Meta:
        model = get_profile_model()
        exclude = ('user', 'privacy',)
        fields = ('first_name', 'last_name', 'location', 'language', 'mugshot', 'blog',
            'linked_in', 'twitter', 'about', 'looking_for_work')