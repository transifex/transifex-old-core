# -*- coding: utf-8 -*-
from polib import unescape

from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.conf import settings
from django.utils.translation import ugettext as _

from translations.models import POFile
from reviews.models import POReviewRequest


def transfile_review_list(request, pofile_id):
    pofile = get_object_or_404(POFile, pk=pofile_id)
    reviews = pofile.reviews.open_reviews()
    return render_to_response('reviews/review_list.html', {
        'pofile': pofile,
        'reviews': reviews,
    }, context_instance=RequestContext(request))


