from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _

import authority
from authority.permissions import BasePermission
from projects.models import Project
from teams.models import Team
from translations.models import POFile
from txcommon.log import logger

class ProjectPermission(BasePermission):

    label = 'project_perm'
    checks = ('maintain', 'coordinate_team', 'submit_file',)

    def maintain(self, project=None, component=None):
        if project:
            if project.maintainers.filter(id=self.user.id):
                return True
        return False
    maintain.short_description=_('Is allowed to maintain this project')

    def coordinate_team(self, project=None, language=None):
        if project:
            #Maintainer
            if self.maintain(project):
                return True
            if language:
                team = get_object_or_404(Team, project__pk=project.pk,
                    language__code=language.code)
                #Coordinator
                if self.user in team.coordinators.all():
                    return True
        return False
    coordinate_team.short_description=_('Is allowed to coordinate a team project')

    def submit_file(self, obj, any_team=False):
        """
        Verify if an user can submit files for a project.
        
        This method can receive tree kinds of object through the parameter 'obj',
        which can be Project, Team and POFile. Depending on the type of object,
        different checks are done.
        
        The parameter 'any_team' can be used when a it's necessary to verify if
        an user has submit access for at least one project team. If an Project 
        object is passed and the parameter 'any_team' id set as False, the 
        verification of access will just return True for maintainers and writers.
        """
        project, team = None, None
        if obj:
            if isinstance(obj, Project):
                project = obj
            elif isinstance(obj, Team):
                team = obj
                project = team.project
            elif isinstance(obj, POFile):
                project = obj.object.project
                team = Team.objects.get_or_none(project, obj.language_code)
            if project:
                if project.anyone_submit:
                    return True
                #Maintainers
                if self.maintain(project):
                    return True
                #Writers
                perm = '%s.submit_file' % self.label
                if self.has_perm(perm, project):
                    return True
                if team:
                    #Coordinators or members
                    if self.user in team.coordinators.all() or \
                        self.user in team.members.all():
                        return True
                if any_team and not team:
                    for team in project.team_set.all():
                        if self.user in team.coordinators.all() or \
                            self.user in team.members.all():
                            return True
        return False
    submit_file.short_description=_('Is allowed to submit file to this project')


authority.register(Project, ProjectPermission)