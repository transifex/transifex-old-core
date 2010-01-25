from django.conf.urls.defaults import *

from reviews.views import review_like

urlpatterns = patterns('',
    url(
        regex = ('^(?P<id>\d+)/like_dislike/$'),
        view = review_like,
        name = 'review_like',),
)
