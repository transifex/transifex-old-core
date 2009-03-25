from django.conf.urls.defaults import patterns, url

from repowatch.views import watch_add, watch_remove

urlpatterns = patterns('repowatch.views',
    url(
        regex = ('^add/(?P<id>[\d]+)$'),
        view = watch_add,
        name = 'watch_add',
    ),
    url(
        regex = ('^remove/(?P<id>[\d]+)$'),
        view = watch_remove,
        name = 'watch_remove',
    ),
)
