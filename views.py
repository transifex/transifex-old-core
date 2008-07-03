from django.db.models import Q
from django.shortcuts import render_to_response
from txc.projects.models import Project

def search(request):
    query = request.GET.get('q', '')
    if query:
        qset = (
            Q(name__icontains=query)
            | Q(description__icontains=query)
#            | Q(tags__last_name__icontains=query)
        )
        results = Project.objects.filter(qset).distinct()
    else:
        results = []
    return render_to_response("search.html", {
        "results": results,
        "query": query
    })
