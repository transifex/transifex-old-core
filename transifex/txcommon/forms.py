from userena.forms import EditProfileForm as UserenaEditProfileForm
from userena.utils import get_profile_model

class EditProfileForm(UserenaEditProfileForm):

    class Meta:
        model = get_profile_model()
        exclude = ('user', 'privacy',)


