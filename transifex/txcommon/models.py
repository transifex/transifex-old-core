from django.db.models.fields.related import OneToOneField

def exclusive_fields(inmodel, except_fields=[]):
    '''
    Returns a generator that yields the fields that belong only to the
    given model descendant
    
    ``except_fields`` is a list that allows to skip some fields based on theirs 
    names
    '''
    for field, model in inmodel._meta.get_fields_with_model():
        if field.name in except_fields:
            yield field
        # Field belongs to an ancestor
        if model is not None:
            continue
        # Field relates to an ancestor
        if isinstance(field, OneToOneField) and (field.rel.to in
            inmodel.__bases__):
            continue
        yield field

def inclusive_fields(inmodel, except_fields=[]):
    '''
    Returns a generator that yields the fields that belong to the given
    model descendant or any of its ancestors
    
    ``except_fields`` is a list that allows to skip some fields based on theirs 
    names
    '''
    for field, model in inmodel._meta.get_fields_with_model():
        # Field relates to the parent of the model it's on
        if isinstance(field, OneToOneField):
            # Passed model
            if (model is None) and (field.rel.to in inmodel.__bases__):
                continue
            # Ancestor model
            if (model is not None) and (field.rel.to in model.__bases__):
                continue
        if field.name in except_fields:
            continue
        yield field
