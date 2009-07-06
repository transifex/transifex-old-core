from django.conf.urls.defaults import *

from reviews.views import review_modify

urlpatterns = patterns('',
    url(
        regex = ('^(?P<id>\d+)/delete/$'),
        view = review_modify,
        name = 'review_modify',)
    ,)
