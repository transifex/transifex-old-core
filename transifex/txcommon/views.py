from django.db.models import Q
from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.template import RequestContext
from django.utils import simplejson
from projects.models import Project
from languages.models import Language
from txcommon.log import logger
from django.contrib.auth.forms import AuthenticationForm

def search(request):
    query_string = request.GET.get('q', "")
    search_terms = query_string.split()
    results = Project.objects.filter()

    if search_terms:
        query = Q()
        for term in search_terms:
            query &= Q(name__icontains=term) | Q(description__icontains=term) | Q(long_description__icontains=term)
        results = results.filter(query).distinct()
    else:
        results = []
    logger.debug("Searched for %s. Found %s results." % (query_string, len(results)))
    return render_to_response("search.html",
        {'query': query_string, 
         'terms': search_terms, 
         'results': results}, 
          context_instance = RequestContext(request))

def index(request):
    latest_projects = Project.objects.order_by('-created')[:5]
    num_projects = len(Project.objects.all())
    num_languages = len(Language.objects.all())
    return render_to_response("index.html",
        {'latest_projects': latest_projects,
         'form': AuthenticationForm(),
         'next': request.path,
         'num_projects': num_projects,
         'num_languages': num_languages,
         },
          context_instance = RequestContext(request))

# Ajax response

def json_result(result):
    return HttpResponse(simplejson.dumps(result))

def json_error(message, result=None):
    if result is None:
        result = {}
    result.update({
        'style': 'error',
        'error': message,
    })
    return json_result(result)
