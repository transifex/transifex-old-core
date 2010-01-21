from django.conf.urls.defaults import *

from reviews.views import (review_modify, review_like)

urlpatterns = patterns('',
    url(
        regex = ('^(?P<id>\d+)/delete/$'),
        view = review_modify,
        name = 'review_modify',),
    url(
        regex = ('^(?P<id>\d+)/like_dislike/$'),
        view = review_like,
        name = 'review_like',),
)
