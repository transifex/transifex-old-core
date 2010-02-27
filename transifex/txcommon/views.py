import datetime
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils import simplejson
from django.utils.translation import ugettext as _
from django.views.generic import list_detail

from notification import models as notification

from actionlog.models import LogEntry, action_logging
from languages.models import Language
from projects.models import Project
from txcommon.filters import LogEntryFilter
from txcommon.log import logger

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
    num_projects = Project.objects.count()
    num_languages = Language.objects.count()
    return render_to_response("index.html",
        {'form': AuthenticationForm(),
         'next': request.path,
         'num_projects': num_projects,
         'num_languages': num_languages,
         },
          context_instance = RequestContext(request))


@login_required
def user_timeline(request, *args, **kwargs):
    """
    Present a log of the latest actions of a user.
    
    The view limits the results and uses filters to allow the user to even
    further refine the set.
    """
    log_entries = LogEntry.objects.by_user(request.user)
    f = LogEntryFilter(request.GET, queryset=log_entries)

    return render_to_response("txcommon/user_timeline.html",
        {'f': f,
         'actionlog': f.qs},
        context_instance = RequestContext(request))


@login_required
def user_nudge(request, username):
    """View for nudging an user"""
    user = get_object_or_404(User, username=username)
    ctype = ContentType.objects.get_for_model(user)

    #It's just allowed to re-nudge the same person after 15 minutes
    last_minutes = datetime.datetime.today() - datetime.timedelta(minutes=15)
    
    log_entries = LogEntry.objects.filter(user=request.user, 
        object_id=user.pk, content_type=ctype, action_time__gt=last_minutes)

    if log_entries:
        request.user.message_set.create(message = _(
                "You can't re-nudge the same user in a short amount of time."))
    elif user.pk == request.user.pk:
        request.user.message_set.create(message = _(
                "You can't nudge yourself."))
    else:
        context={'performer': request.user}
        nt= 'user_nudge'
        action_logging(request.user, [user], nt, context=context)
        notification.send([user], nt, context)
        request.user.message_set.create(message = _(
                "You have nudged '%s'.") % user)

    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

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
