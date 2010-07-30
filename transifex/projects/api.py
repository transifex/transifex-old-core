# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.db import transaction
from django.http import HttpResponse
from django.utils import simplejson
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import slugify

from piston.handler import BaseHandler
from piston.utils import rc

from actionlog.models import action_logging
from happix.decorators import method_decorator
from happix.libtransifex import pofile, qt
from happix.models import * 
from languages.models import Language
from projects.models import Project
from projects.permissions import *
from projects.permissions.project import ProjectPermission
from storage.models import StorageFile
from teams.models import Team
from txcommon.log import logger
from txcommon.decorators import one_perm_required_or_403
from uuid import uuid4

# Temporary
from txcommon import notifications as txnotification

class ProjectHandler(BaseHandler):
    """
    API handler for model Project.
    """
    allowed_methods = ('GET','POST','PUT','DELETE')
    model = Project
    #TODO: Choose the fields we want to return
    fields = ('slug', 'name', 'description', 'long_description', 'created',
              'anyone_submit', 'bugtracker', ('owner', ('username', 'email')),
              ('resource_set', ('slug', 'name',)))
    exclude = ()

    def read(self, request, project_slug=None):
        """
        Get project details in json format
        """
        if project_slug:
            try:
                project = Project.objects.get(slug=project_slug)
            except Project.DoesNotExist:
                return rc.NOT_FOUND
            return project
        else:
            return Project.objects.all()

    @method_decorator(one_perm_required_or_403(pr_project_add))
    def create(self, request,project_slug=None):
        """
        API call to create new projects via POST.
        """
        if 'application/json' in request.content_type: # we got JSON
            data = getattr(request, 'data', None)
            outsource = mainteners = None
            outsource = data.pop('outsource', {})
            maintainers = data.pop('maintainers', {})
            try:
                p, created = Project.objects.get_or_create(**data)
            except:
                return rc.BAD_REQUEST

            if created:
                # Owner
                p.owner = request.user

                # Outsourcing
                if outsource:
                    try:
                        outsource_project = Project.objects.get(slug=outsource)
                    except Project.DoesNotExist:
                        # maybe fail when wrong user is given?
                        pass
                    p.outsource = outsource_project

                # Handler m2m with maintainers
                if maintainers:
                    for user in maintainers.split(','):
                        try:
                            p.maintainers.add(User.objects.get(username=user))
                        except User.DoesNotExist:
                            # maybe fail when wrong user is given?
                            pass
                p.save()

            return rc.CREATED
        else:
            return rc.BAD_REQUEST

    @method_decorator(one_perm_required_or_403(pr_project_add_change,
        (Project, 'slug__exact', 'project_slug')))
    def update(self, request,project_slug):
        """
        API call to update project details via PUT.
        """

        if 'application/json' in request.content_type: # we got JSON
            data = getattr(request, 'data', None)
            outsource = mainteners = None
            outsource = data.pop('outsource', {})
            maintainers = data.pop('maintainers', {})
            if project_slug:
                try:
                    p = Project.objects.get(slug=project_slug)
                except Project.DoesNotExist:
                    return rc.BAD_REQUEST
                try:
                    for key,value in data.items():
                        setattr(p, key,value)
                    # Outsourcing
                    if outsource:
                        try:
                            outsource_project = Project.objects.get(slug=outsource)
                        except Project.DoesNotExist:
                            # maybe fail when wrong user is given?
                            pass
                        p.outsource = outsource_project

                    # Handler m2m with maintainers
                    if maintainers:
                        # remove existing maintainers
                        p.maintainers.all().clear()
                        # add then all anew
                        for user in maintainers.split(','):
                            try:
                                p.maintainers.add(User.objects.get(username=user))
                            except User.DoesNotExist:
                                # maybe fail when wrong user is given?
                                pass
                    p.save()
                except:
                    return rc.BAD_REQUEST

                return rc.ALL_OK

        return rc.BAD_REQUEST


    @method_decorator(one_perm_required_or_403(pr_project_delete,
        (Project, 'slug__exact', 'project_slug')))
    def delete(self, request,project_slug):
        """
        API call to delete projects via DELETE.
        """
        if project_slug:
            try:
                project = Project.objects.get(slug=project_slug)
            except Project.DoesNotExist:
                return rc.NOT_FOUND

            try:
                project.delete()
            except:
                return rc.INTERNAL_ERROR

            return rc.DELETED
        else:
            return rc.BAD_REQUEST


class ProjectResourceHandler(BaseHandler):
    """
    API handler for creating resources under projects
    """

    allowed_methods = ('POST', 'PUT')

    @method_decorator(one_perm_required_or_403(pr_resource_add_change,
        (Project, 'slug__exact', 'project_slug')))
    def create(self, request, project_slug):
        """
        Create resource for project by UUID of StorageFile.
        """
        if "application/json" in request.content_type:
            if "uuid" in request.data:
                uuid = request.data['uuid']
                project = Project.objects.get(slug=project_slug)
                storagefile = StorageFile.objects.get(uuid=uuid)

                resource, created = Resource.objects.get_or_create(
                        slug = "resource-%s" % (slugify(storagefile.name)),
                        name = "Translations of '%s'" % storagefile.name,
                        source_language = storagefile.language,
                        project = project,
                        source_file=storagefile
                )
                # update l10n_method
                if created:
                    method = L10n_method.objects.get_by_filename(storagefile.get_storage_path())
                    if not method:
                        request.user.message_set.create(message=_("Error: We couldn't"
                        " find a suitable localization method for this file."))
                        return rc.BAD_REQUEST
                    resource.l10n_method = method
                    resource.save()

                logger.debug("Going to insert strings from %s (%s) to %s/%s" %
                    (storagefile.name, storagefile.uuid, project.slug,
                    resource.slug))

                strings_added, strings_updated = 0, 0
                parser = storagefile.find_parser()
                fhandler = parser(filename=storagefile.get_storage_path())
                fhandler.bind_resource(resource)
                fhandler.parse_file(True)
                try:
                    strings_added, strings_updated = fhandler.save2db(True)
                except:
                    request.user.message_set.create(message=_("Error importing"
                        " file."))
                    return rc.BAD_REQUEST
                else:
                    messages = []
                    if strings_added > 0:
                        messages.append(_("%i strings added") % strings_added)
                    if strings_updated > 0:
                        messages.append(_("%i strings updated") % strings_updated)
                    request.user.message_set.create(
                        message=",".join(messages))
                retval= {
                    'strings_added': strings_added,
                    'strings_updated': strings_updated,
                    'redirect': reverse('resource_detail',args=[project_slug, 
                        resource.slug])
                    }
                logger.debug("Extraction successful, returning: %s" % retval)

                # Set StorageFile to 'bound' status, which means that it is 
                # bound to some translation resource
                storagefile.bound = True
                storagefile.save()

                # ActionLog & Notification
                if created:
                    nt = 'project_resource_added'
                else:
                    nt = 'project_resource_changed'
                context = {'project': project,
                           'resource': resource}
                object_list = [project, resource]
                action_logging(request.user, object_list, nt, context=context)
                if settings.ENABLE_NOTICES:
                    txnotification.send_observation_notices_for(project,
                            signal=nt, extra_context=context)

                return HttpResponse(simplejson.dumps(retval),
                    mimetype='application/json')

            else:
                return rc.BAD_REQUEST
        else:
            return rc.BAD_REQUEST

    def update(self, request, project_slug, resource_slug, language_code=None):
        """
        Update resource translations of a project by the UUID of a StorageFile.
        """
        try:
            project = Project.objects.get(slug=project_slug)
        except Project.DoesNotExist:
            return rc.NOT_FOUND

        # Permissions handling
        team = Team.objects.get_or_none(project, language_code)
        check = ProjectPermission(request.user)
        if not check.submit_translations(team or project):
            return rc.FORBIDDEN

        if "application/json" in request.content_type:
            if "uuid" in request.data:
                uuid = request.data['uuid']
                resource = Resource.objects.get(slug=resource_slug,
                    project=project)
                storagefile = StorageFile.objects.get(uuid=uuid)
                language = storagefile.language

                logger.debug("Going to insert strings from %s (%s) to %s/%s" %
                    (storagefile.name, storagefile.uuid, project_slug, 
                    resource.slug))

                strings_added, strings_updated = 0, 0
                parser = storagefile.find_parser()
                language = storagefile.language
                fhandler = parser(filename=storagefile.get_storage_path())
                fhandler.set_language(language)
                fhandler.bind_resource(resource)
                fhandler.parse_file()

                try:
                    strings_added, strings_updated = fhandler.save2db()
                except:
                    request.user.message_set.create(message=_("Error importing"
                       " file."))
                    return rc.BAD_REQUEST

                else:
                    messages = []
                    if strings_added > 0:
                        messages.append(_("%i strings added") % strings_added)
                    if strings_updated > 0:
                        messages.append(_("%i strings updated") % strings_updated)
                    request.user.message_set.create(
                        message=",".join(messages))

                retval= {
                    'strings_added':strings_added,
                    'strings_updated':strings_updated,
                    'redirect':reverse('resource_detail',args=[project_slug, 
                        resource.slug])
                    }

                logger.debug("Extraction successful, returning: %s" % retval)

                # Set StorageFile to 'bound' status, which means that it is 
                # bound to some translation resource
                storagefile.bound = True
                storagefile.save()

                # If any string added/updated
                if retval['strings_added'] > 0 or retval['strings_updated'] > 0:
                    # ActionLog & Notification
                    nt = 'project_resource_translated'
                    context = {'project': project,
                                'resource': resource,
                                'language': language}
                    object_list = [project, resource, language]
                    action_logging(request.user, object_list, nt, context=context)
                    if settings.ENABLE_NOTICES:
                        txnotification.send_observation_notices_for(project,
                                signal=nt, extra_context=context)

                return HttpResponse(simplejson.dumps(retval),
                    mimetype='application/json')
            else:
                return rc.BAD_REQUEST
        else:
            return rc.BAD_REQUEST
