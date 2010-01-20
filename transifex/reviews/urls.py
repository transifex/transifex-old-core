from django.conf.urls.defaults import *

from reviews.views import (review_modify, review_add, review_like)

urlpatterns = patterns('',
    url(
        regex = ('^(?P<id>\d+)/delete/$'),
        view = review_modify,
        name = 'review_modify',),
    url(
        regex = ('^(?P<id>\d+)/like_dislike/$'),
        view = review_like,
        name = 'review_like',),
    url(
        regex = ('^add_in_component/(?P<component_id>\d+)/$'),
        view = review_add,
        name = 'review_add',),
)
