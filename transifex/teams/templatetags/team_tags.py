# -*- coding: utf-8 -*-
from django import template
from transifex.resources.models import RLStats
from transifex.teams.models import Team
from transifex.txcommon.utils import StatBarsPositions

register = template.Library()

@register.filter
def language_has_team(lang_code, project):
    """
    Return if the specific language has a corresponding team for the project.

    Example: {% if language_obj.code|language_has_team:stat.object.project %}
    """

    return Team.objects.get_or_none(project, lang_code)


@register.inclusion_tag("resources/stats_bar_simple.html")
def get_team_progress(team, width=100):
    """
    Display a progress bar for the specified team.
    """

    stats = RLStats.objects.by_project_and_language(
        team.project, team.language
    )

    translated = 0
    untranslated = 0
    total = 0

    for s in stats:
        translated += s.translated
        untranslated += s.untranslated
        total += s.total

    translated_perc = translated * 100 / total
    untranslated_perc = 100 - translated_perc

    return {
        'untrans_percent': untranslated_perc,
        'trans_percent': translated_perc,
        'untrans': untranslated,
        'trans': translated,
        'pos': StatBarsPositions([('trans', translated_perc), ('untrans', untranslated_perc)], width),
        'width': width
    }
