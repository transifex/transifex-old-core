# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils import simplejson
from django.utils.translation import ugettext as _
from projects.models import Project
from projects.permissions import *
from txcommon.decorators import one_perm_required_or_403
from models import URLInfo

@one_perm_required_or_403(pr_resource_add_change,
                          (Project, "slug__exact", "project_slug"))
def fetch_url(request, project_slug, resource_slug):
    """
    Trigger the fetching of the source file url and then update the resource.
    """

#    if not request.POST:
#        return HttpResponseBadRequest()

    response_dict = {}
    try:
        urlinfo = URLInfo.objects.get(resource__slug=resource_slug)
        urlinfo.update_source_file()
    except URLInfo.DoesNotExist:
        response_dict = { 'status':404,
                          'message':_("URL not set for this resource.")}
    except:
        response_dict = { 'status':500,
                          'message':_("Error updating source file.")}
    else:
        response_dict = { 'status':200,
                          'message':_("Source file updated successfully."),
                          'redirect_url':reverse('resource_detail',
                                                  args=[project_slug,
                                                        resource_slug])}

    json_dict = simplejson.dumps(response_dict)
    return HttpResponse(json_dict, mimetype='application/json')
