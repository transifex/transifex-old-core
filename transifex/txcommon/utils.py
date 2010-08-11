from django.core.urlresolvers import get_resolver

def get_url_pattern(urlname, args=[]):
    """
    Return URL pattern for a URL based on its name.

    args - list of argument names for the URL. Useful to distinguish URL 
    patterns identified with the same name.

    >>> get_url_pattern('project_detail')
    u'/projects/p/%(project_slug)s/'

    >>> get_url_pattern('project_detail', args=['project_slug'])
    u'/projects/p/%(project_slug)s/'

    """
    patterns = get_resolver(None).reverse_dict.getlist(urlname)
    if not args:
        return '/%s' % patterns[0][0][0][0]

    for pattern in patterns:
        if pattern[0][0][1] == args:
            return '/%s' % pattern[0][0][0]


def cached_property(func):
    """
    Cached property.

    This function is able to verify if an instance of a property field
    was already created before and, if not, it creates the new one.
    When needed it also is able to delete the cached property field from
    the memory.

    Usage:
    @cached_property
    def trans(self):
        ...

    del(self.trans)

    """
    def _set_cache(self):
        cache_attr = "__%s" % func.__name__
        try:
            return getattr(self, cache_attr)
        except AttributeError:
            value = func(self)
            setattr(self, cache_attr, value)
            return value

    def _del_cache(self):
        cache_attr = "__%s" % func.__name__
        try:
            delattr(self, cache_attr)
        except AttributeError:
            pass

    return property(_set_cache, fdel=_del_cache)

def key_sort(l, *keys):
    """
    Sort an iterable given an arbitary number of keys relative to it
    and return the result as a list. When a key starts with '-' the
    sorting is reversed.

    Example: key_sort(people, 'lastname', '-age')
    """
    l = list(l)
    for key in keys:
        #Find out if we want a reversed ordering
        if key.startswith('-'):
            reverse = True
            key = key[1:]
        else:
            reverse = False

        attrs = key.split('.')
        def fun(x):
            # Calculate x.attr1.attr2...
            for attr in attrs:
                x = getattr(x, attr)
            # If the key attribute is a string we lowercase it
            if isinstance(x, basestring):
                x = x.lower()
            return x
        l.sort(key=fun, reverse=reverse)
    return l

def size_human(size):
    """
    Make the size in bytes to a more human readable format.
    
    This function compares the size value with some thresholds and returns
    a new value with the appropriate suffix (K, M, T, P). The correct input
    is an integer value not a string!!!
    
    >>> size_human(755745434)
    '721.0M'
    """

    if size:
        _abbrevs = [
        (1<<50L, 'P'),
        (1<<40L, 'T'), 
        (1<<30L, 'G'), 
        (1<<20L, 'M'), 
        (1<<10L, 'k'),
        (1, 'bytes')]

        for factor, suffix in _abbrevs:
            if size > factor:
                break
        if factor == 1:
            return "%d %s" % (size, suffix)
        else:
            return "%.3f%s" % (float(size)/float(factor), suffix)


def restructured_table(column_names, column_ids, object_list, truncate_len=13):
    """Restructured table creation method
    
    This method takes some objects in a list and present them in a table format.
    The format is similar with the one used in restructured text, so it can easily
    be used in formatted text.
    The arguments are the following:
    column_names : a list or tupple with the title of each column
    column_id : a list or tupple of all the keys which will be presented from 
    each object
    object_list : the list of the objects which contain the data to be presented
    truncate_len : the length of the strings in each cell
    
    Example output :
    +---------------+---------------+---------------+
    |Alfa           |Beta           |Gama           |
    +---------------+---------------+---------------+
    |2314           |34545          |5666           |
    |12165          |34512345       |53254          |
    +---------------+---------------+---------------+

    """
    single_cell_border = "+" + (truncate_len+2) * "-"
    border = len(column_names) * single_cell_border + "+"
    table = "\n" + border + "\n"
    # Column Headers first
    for column in column_names:
        table += "| %-13s " % column[:truncate_len]
    table += "|\n" + border + "\n"
    # Data next
    for obj in object_list:
        for i in column_ids:
            levels = i.split(".")
            attr = obj
            for l in levels:
                attr = getattr(attr, l)
            table += "| %-13s " % str(attr)[:truncate_len]
        table += "|\n"
    table += border + "\n"
    return table
