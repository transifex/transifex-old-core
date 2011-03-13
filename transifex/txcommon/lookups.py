from django.contrib.auth.models import User
from django.db.models import Q

class UsersLookup(object):
    """A lookup class, used by django-ajax-select app to search model data."""

    def get_query(self,q,request):
        """
        Return a query set.

        You also have access to request.user if needed.
        """
        return User.objects.filter(Q(username__istartswith=q))

    def format_item(self,user):
        """Simple display of an object when displayed in the list of objects """
        return unicode(user)

    def format_result(self,user):
        """
        A more verbose display, used in the search results display.

        It may contain html and multi-lines.
        """
        return u"%s" % (user.username)

    def get_objects(self,ids):
        """Given a list of ids, return the objects ordered."""
        return User.objects.filter(pk__in=ids).order_by('username','last_name')
