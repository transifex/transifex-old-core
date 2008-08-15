from django.newforms import ModelForm
from django.shortcuts import render_to_response
from models import Project

class ProjectForm(ModelForm):
    class Meta:
        model = Project

def project_add(request):
    from txc.projects.project_form import ProjectForm
    form_message = ''
    if request.POST:
        form = ProjectForm(request.POST)
        if form.is_valid():
            form.save()
            #redirect it somewhere
        else:
            form_message = 'Oops. Please correct the errors below.'
    else:
        form = ProjectForm()
    return render_to_response("projects/project_add.html", {
        'form' : form,
        'form_message': form_message                                                       
    })

def project_detail(request):
    from txc.projects.forms import HoldForm
    thisForm = HoldForm
    form_message = ''
    if request.POST:
        form = thisForm(request.POST)
        if form.is_valid():
            form.save()
            #redirect it somewhere
        else:
            form_message = 'Oops. Please correct the errors below.'
    else:
        form = thisForm()
    
    return render_to_response("projects/project_detail.html", {
        'form' : form,
        'form_message': form_message
    })
