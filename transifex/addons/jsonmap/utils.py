def remove_attrs_startwith(dictionay, chars):
    """
    Remove attributes starting with ``chars`` from ``dictionary`` in place.
    """
    def for_list(val):
        for v in val:
            if isinstance(v, (list, tuple)):
                for_list(v)
            elif type(v) == dict:
                remove_attrs_startwith(v, chars)

    for key, val in dictionay.items():
        if key.startswith(chars):
            dictionay.pop(key)
        elif type(val) != dict:
            if isinstance(val, (list, tuple)):
                for_list(val)
        else:
            remove_attrs_startwith(val, chars)
