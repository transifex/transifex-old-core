from django import forms

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe

from ajax_select.fields import AutoCompleteField

from authority import permissions
from authority.models import Permission


class UserAjaxPermissionForm(forms.ModelForm):
    """
    A class for building a permission form using an ajax autocomplete field.
    
    This class mimics the functionality of UserPermissionForm in django 
    authority application, but instead of a Charfield for user field, uses
    an AutoCompleteField as specified by ajax_select application. Usernames
    are retrieved asynchronously with ajax calls and filling of the input field
    occurs with an automatic way.
    """
    codename = forms.CharField(label=_('Permission'))
    # declare a field and specify the named channel that it uses
    user = AutoCompleteField('users', required=True)

    class Meta:
        model = Permission
        fields = ('user',)

    def __init__(self, perm=None, obj=None, approved=False, *args, **kwargs):
        self.perm = perm
        self.obj = obj
        self.approved = approved
        if not self.approved:
            self.base_fields['user'].widget = forms.HiddenInput()

        if obj and perm:
            self.base_fields['codename'].widget = forms.HiddenInput()
        elif obj and (not perm or not approved):
            perm_choices = get_choices_for(self.obj)
            self.base_fields['codename'].widget = forms.Select(
                choices=perm_choices)
        super(UserAjaxPermissionForm, self).__init__(*args, **kwargs)

    def save(self, request, commit=True, *args, **kwargs):
        self.instance.creator = request.user
        self.instance.content_type = ContentType.objects.get_for_model(self.obj)
        self.instance.object_id = self.obj.id
        self.instance.codename = self.perm
        self.instance.approved = self.approved
        return super(UserAjaxPermissionForm, self).save(commit)

    def clean_user(self):
        username = self.cleaned_data["user"]
        try:
            user = User.objects.get(username__iexact=username)
        except User.DoesNotExist:
            raise forms.ValidationError(
                mark_safe(_("A user with that username does not exist.")))
        check = permissions.BasePermission(user=user)
        error_msg = None
        if user.is_superuser:
            error_msg = _("The user %(user)s do not need to request "
                          "access to any permission as it is a super user.")
        elif check.has_perm(self.perm, self.obj):
            error_msg = _("The user %(user)s already has the permission "
                          "'%(perm)s' for %(object_name)s '%(obj)s'")
        elif check.requested_perm(self.perm, self.obj):
            error_msg = _("The user %(user)s already requested the permission"
                          " '%(perm)s' for %(object_name)s '%(obj)s'")
        if error_msg:
            error_msg = error_msg % {
                'object_name': self.obj._meta.object_name.lower(),
                'perm': self.perm,
                'obj': self.obj,
                'user': user,
            }
            raise forms.ValidationError(mark_safe(error_msg))
        return user
