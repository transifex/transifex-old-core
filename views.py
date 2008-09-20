from django.db.models import Q
from django.shortcuts import render_to_response
from projects.models import Project
from django.template import RequestContext 

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
    return render_to_response("search.html",
        {'query': query_string, 
         'terms': search_terms, 
         'results': results}, 
          context_instance = RequestContext(request))

