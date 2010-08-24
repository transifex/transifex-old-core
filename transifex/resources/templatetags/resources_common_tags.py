from django import template

register = template.Library()

@register.filter(name='entity_translation')
def entity_translation(source_entity, language):
    return source_entity.get_translation(language.code)

