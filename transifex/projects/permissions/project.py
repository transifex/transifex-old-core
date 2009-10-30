from projects.models import Project
from django.utils.translation import ugettext_lazy as _

import authority
from authority.permissions import BasePermission

class ProjectPermission(BasePermission):

    label = 'project_perm'
    checks = ('maintain', 'submit_file',)

    def maintain(self, project=None, component=None):
        if project:
            if project.maintainers.filter(id=self.user.id):
                return True
        return False
    maintain.short_description=_('Is allowed to maintain this project')

    def submit_file(self, project=None, component=None):
        if project:
            if project.anyone_submit:
                return True
            else:
                return self.browse_project(obj=project)
        return False
    submit_file.short_description=_('Is allowed to submit file to this project')

authority.register(Project, ProjectPermission)