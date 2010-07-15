# -*- coding: utf-8 -*-
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _

import authority
from authority.permissions import BasePermission
from projects.models import Project
from teams.models import Team
from translations.models import POFile
from txcommon.log import logger


def _check_outsource_project(obj):
    """
    Check if the project, which the obj passed by parameter belongs to, has
    outsourced the access control to another project.

    The parameter 'obj' can be an Project, Team or POFile instance.

    Return a tuple '(project, team)'. The 'team' might be None.
    """
    if isinstance(obj, Project):
        if obj.outsource:
            project = obj.outsource
        else:
            project = obj
        team = None
    elif isinstance(obj, Team):
        team = obj
        project = team.project
    elif isinstance(obj, POFile):
        if obj.object.project.outsource:
            project = obj.object.project.outsource
        else:
            project = obj.object.project
        team = Team.objects.get_or_none(project, obj.language_code)

    return (project, team)

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
                # TODO: Changed from get_object_or_404 to this, check implications!
                team = Team.objects.get_or_none(project, language.code)
                #Coordinator
                if team and self.user in team.coordinators.all():
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
            project, team = _check_outsource_project(obj)
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


    def private(self, project=None):
        """Test if a user has access to a private project."""
        if project:
            if project.private:
                # Maintainers, writers (submitters, team coordinators, members)
                return self.maintain(project) or self.submit_file(project,
                     any_team=True)
            else:
                # The project is public so let them continue
                return True
        return False
    private.short_description=_('Is allowed to browse this private project')

authority.register(Project, ProjectPermission)