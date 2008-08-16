from django.forms import ModelForm
from models import Hold

class HoldForm(ModelForm):
    class Meta:
        model = Hold