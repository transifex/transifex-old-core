from django import template
from transifex.resources.models import RLStats
from transifex.txcommon.utils import StatBarsPositions

register = template.Library()

@register.inclusion_tag('resources/stats_bar_simple.html')
def progress_for_project(project, language=None, width=100):
    """Render a progressbar for the specified project."""

    if language:
        stats = RLStats.objects.by_project_and_language(project, language)
    else:
        stats = RLStats.objects.by_project(project)

    translated = untranslated = total = 0

    for s in stats:
        translated += s.translated
        untranslated += s.untranslated
        total += s.total

    try:
        translated_perc = translated * 100 / total
    except ZeroDivisionError:
        translated_perc = 100

    untranslated_perc = 100 - translated_perc

    bar_data = [
        ('trans', translated_perc),
        ('untrans', untranslated_perc)
    ]

    return {
        'untrans_percent': untranslated_perc,
        'trans_percent': translated_perc,
        'untrans': untranslated,
        'trans': translated,
        'pos': StatBarsPositions(bar_data, width),
        'width': width
    }
