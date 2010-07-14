# -*- coding: utf-8 -*-
from piston.handler import BaseHandler
from piston.utils import rc
from django.template.defaultfilters import slugify
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from happix.models import Resource, SourceEntity, Translation
from languages.models import Language
from projects.models import Project
from projects.permissions import *
from storage.models import StorageFile
from txcommon.log import logger
from txcommon.decorators import one_perm_required_or_403
from django.db import transaction
from uuid import uuid4
from happix.decorators import method_decorator

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
            import ipdb;ipdb.set_trace()
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
                owner = User.objects.get(username = request.user)
                p.owner = owner

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

    allowed_methods = ('POST')

    def create(self, request, project_slug):
        """
        Creates subelement for project, currently supports creating translation resource by UUID of StorageFile
        """
        if "application/json" in request.content_type:
            if "uuid" in request.data:
                uuid = request.data['uuid']
                project = Project.objects.get(slug=project_slug)
                storage_file = StorageFile.objects.get(uuid=uuid,user=request.user)

                translation_resource, created = Resource.objects.get_or_create(
                        slug = "resource-%s" % (slugify(storage_file.name)),
                        name = "Translations of '%s'" % storage_file.name,
                        source_language = storage_file.language,
                        project = project,
                )

                logger.debug("Going to insert strings from %s (%s) to %s/%s" % (storage_file.name, storage_file.uuid, project.slug, translation_resource.slug))
                try:
                    strings_added, strings_updated = translation_resource.merge_translation_file(storage_file)
                except Language.DoesNotExist:
                    request.user.message_set.create(
                        message="We could not guess the language of uploaded file")
                else:
                    messages = []
                    if strings_added > 0:
                        messages.append("%i strings added" % strings_added)
                    if strings_updated > 0:
                        messages.append("%i strings updated" % strings_updated)
                    request.user.message_set.create(
                        message=",".join(messages))
                retval= {
                    'added':strings_added,
                    'updated':strings_updated,
                    #'redirect':reverse('resource_detail',args=[project.slug, translation_resource.slug])
                    'redirect':reverse('translate',args=[project.slug, translation_resource.slug, storage_file.language.code])
                }
                logger.debug("Extraction successful, returning: %s" % retval)

                # Set StorageFile to 'bound' status, which means that it is bound to some translation resource
                # This also means it will not be shown in 'Uploaded files' box anymore
                storage_file.bound = True
                storage_file.save()
                return retval
            else:
                return rc.BAD_REQUEST
        else:
            return rc.BAD_REQUEST
