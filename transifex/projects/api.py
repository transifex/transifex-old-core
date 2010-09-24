# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.db import transaction
from django.http import HttpResponse, HttpResponseServerError
from django.utils import simplejson
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import slugify

from piston.handler import BaseHandler
from piston.utils import rc, throttle

from actionlog.models import action_logging
from languages.models import Language
from projects.models import Project
from projects.permissions import *
from projects.permissions.project import ProjectPermission
from projects.signals import post_submit_translation
from resources.decorators import method_decorator
from resources.formats import get_i18n_type_from_file, pofile, qt
from resources.models import * 
from storage.models import StorageFile
from teams.models import Team
from txcommon.log import logger
from txcommon.decorators import one_perm_required_or_403
from transifex.api.utils import BAD_REQUEST
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
              ('resources', ('slug', 'name',)))
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
                return BAD_REQUEST("Project not found")

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
            return BAD_REQUEST("Unsupported request")

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
                    return BAD_REQUEST("Project not found")
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
                except Exception, e:
                    return BAD_REQUEST("Error parsing request data: %s" % e)

                return rc.ALL_OK

        return BAD_REQUEST("Unsupported request")


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

    @throttle(100, 60*60)
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
                resource_slug = None
                if "slug" in request.data:
                    resource_slug = request.data['slug']

                resource, created = Resource.objects.get_or_create(
                        slug = resource_slug or slugify(storagefile.name),
                        source_language = storagefile.language,
                        project = project
                )

                if created:
                    resource.name = resource_slug or storagefile.name
                    resource.save()

                # update i18n_type
                i18n_type = get_i18n_type_from_file(storagefile.get_storage_path())
                if not i18n_type:
                    return BAD_REQUEST("File type not supported.")

                resource.i18n_type = i18n_type
                resource.save()

                logger.debug("Going to insert strings from %s (%s) to %s/%s" %
                    (storagefile.name, storagefile.uuid, project.slug,
                    resource.slug))

                strings_added, strings_updated = 0, 0
                parser = storagefile.find_parser()
                fhandler = parser(filename=storagefile.get_storage_path())
                fhandler.bind_resource(resource)
                fhandler.set_language(storagefile.language)

                try:
                    fhandler.contents_check(fhandler.filename)
                    fhandler.parse_file(True)
                    strings_added, strings_updated = fhandler.save2db(True)
                except Exception, e:
                    resource.delete()
                    return BAD_REQUEST("Resource not created. Could not "
                        "import file: %s" % e)
                else:
                    messages = []
                    if strings_added > 0:
                        messages.append(_("%i strings added") % strings_added)
                    if strings_updated > 0:
                        messages.append(_("%i strings updated") % strings_updated)
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
                    mimetype='text/plain')

            else:
                return BAD_REQUEST("Request data missing.")
        else:
            return BAD_REQUEST("Unsupported request")

    def update(self, request, project_slug, resource_slug, language_code=None):
        """
        Update resource translations of a project by the UUID of a StorageFile.
        """
        try:
            project = Project.objects.get(slug=project_slug)
            resource = Resource.objects.get(slug=resource_slug, 
                project=project)
        except (Project.DoesNotExist, Resource.DoesNotExist):
            return rc.NOT_FOUND

        # Permissions handling
        team = Team.objects.get_or_none(project, language_code)
        check = ProjectPermission(request.user)
        if not check.submit_translations(team or project) or not \
            resource.accept_translations:
            return rc.FORBIDDEN

        if "application/json" in request.content_type:
            if "uuid" in request.data:
                uuid = request.data['uuid']
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
                fhandler.contents_check(fhandler.filename)


                try:
                    fhandler.parse_file()
                    strings_added, strings_updated = fhandler.save2db()
                except Exception, e:
                    return BAD_REQUEST("Error importing file: %s" % e)
                else:
                    messages = []
                    if strings_added > 0:
                        messages.append(_("%i strings added") % strings_added)
                    if strings_updated > 0:
                        messages.append(_("%i strings updated") % strings_updated)
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
                    modified = True
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
                else:
                    modified=False

                post_submit_translation.send(None, request=request,
                    resource=resource, language=language, modified=modified)

                return HttpResponse(simplejson.dumps(retval),
                    mimetype='application/json')
            else:
                return BAD_REQUEST("Missing request data.")
        else:
            return BAD_REQUEST("Unsupported request")
