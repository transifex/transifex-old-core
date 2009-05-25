from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

from projects.models import Component
from translations.models import POFile

from forms import TranslationForm


def transfile_edit(request, pofile_id):
    pofile = get_object_or_404(POFile, pk=pofile_id)
    po_entries = pofile.object.trans.get_po_entries(pofile.filename)
    if request.method == "POST":
        # if request.POST["action"] == "update":
        #     form = form_class(request.POST)
        #     project = form.save(commit=False)
        #     project.creator = request.user
        #     project.save()
        #     return HttpResponseRedirect(project.get_absolute_url())
        pass
    else:
        form = TranslationForm(po_entries)
    
    return render_to_response('webtrans/transfile_edit.html', {
        'pofile': pofile,
        'pofile_form': form,
    }, context_instance=RequestContext(request))
