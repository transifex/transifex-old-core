from django.shortcuts import render_to_response
from models import Hold
from forms import HoldForm

def hold_create(request):
    form_message = ''
    if request.POST:
        form = HoldForm(request.POST)
        if form.is_valid():
            form.save()
            #redirect it somewhere
        else:
            form_message = 'Oops. Please correct the errors below.'
    else:
        form = HoldForm()
    return render_to_response("projects/hold_form.html", {
        'form' : form,
        'form_message': form_message                                                       
    })