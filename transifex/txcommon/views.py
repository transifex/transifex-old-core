import datetime
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django import forms
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils import simplejson
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_protect
from django.views.generic import list_detail

from notification import models as notification
from haystack.query import SearchQuerySet

from actionlog.models import LogEntry, action_logging
from transifex.languages.models import Language
from transifex.projects.models import Project
from transifex.simpleauth.forms import RememberMeAuthForm
from transifex.txcommon.filters import LogEntryFilter
from transifex.txcommon.log import logger
from transifex.txcommon.haystack_utils import prepare_solr_query_string, \
    fulltext_fuzzy_match_filter

def permission_denied(request, template_name=None, extra_context={}, *args,
    **kwargs):
    """Wrapper to allow undeclared key arguments."""
    from authority.views import permission_denied
    return permission_denied(request, template_name, extra_context)

def search(request):
    query_string = prepare_solr_query_string(request.GET.get('q', ""))
    search_terms = query_string.split()
    results = SearchQuerySet().models(Project).filter(
        fulltext_fuzzy_match_filter(query_string))
    spelling_suggestion = results.spelling_suggestion(query_string)

    logger.debug("Searched for %s. Found %s results." % (query_string, len(results)))
    return render_to_response("search.html",
        {'query': query_string,
         'terms': search_terms,
         'results': results,
         'spelling_suggestion': spelling_suggestion},
          context_instance = RequestContext(request))

@csrf_protect
def index(request):
    return render_to_response("index.html",
        {'form': RememberMeAuthForm(),
         'next': request.path,
         'num_projects': Project.objects.count(),
         'num_languages': Language.objects.count(),
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
    """View for nudging a user"""
    user = get_object_or_404(User, username=username)
    ctype = ContentType.objects.get_for_model(user)

    #It's just allowed to re-nudge the same person after 15 minutes
    last_minutes = datetime.datetime.today() - datetime.timedelta(minutes=15)

    log_entries = LogEntry.objects.filter(user=request.user,
        object_id=user.pk, content_type=ctype, action_time__gt=last_minutes)

    if log_entries:
        messages.warning(request,
                         _("You can't re-nudge the same user in a short amount of time."))
    elif user.pk == request.user.pk:
        messages.warning(request, _("You can't nudge yourself."))
    else:
        context={'performer': request.user}
        nt= 'user_nudge'
        action_logging(request.user, [user], nt, context=context)
        notification.send([user], nt, context)
        messages.success(request, _("You have nudged '%s'.") % user)

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
