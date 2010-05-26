# -*- coding: utf-8 -*-
from piston.handler import BaseHandler
from piston.utils import rc
from django.template.defaultfilters import slugify
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from happix.models import TResource, SourceString, TranslationString, StorageFile
from languages.models import Language
from projects.models import Project
from txcommon.log import logger
from django.db import transaction
from uuid import uuid4

class ProjectHandler(BaseHandler):
    """
    API handler for model Project.
    """
    allowed_methods = ('GET','PUT')
    model = Project
    #TODO: Choose the fields we want to return
    exclude = ()

    def update(self, request, project_slug):
        """
        Creates subelement for project, currently supports creating translation resource by UUID of StorageFile
        """
        if "application/json" in request.content_type:
            if "uuid" in request.data:
                uuid = request.data['uuid']
                project = Project.objects.get(slug=project_slug)
                storage_file = StorageFile.objects.get(uuid=uuid,user=request.user)

                translation_resource, created = TResource.objects.get_or_create(
                        slug = "resource-%s" % (slugify(storage_file.name)),
                        name = "Translations of '%s'" % storage_file.name,
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
                    #'redirect':reverse('project.resource',args=[project.slug, translation_resource.slug])
                    'redirect':reverse('translation',args=[project.slug, translation_resource.slug, storage_file.language.code])
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
