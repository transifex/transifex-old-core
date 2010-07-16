# -*- coding: utf-8 -*-
from piston.handler import BaseHandler
from piston.utils import rc
from django.http import HttpResponse
from django.template.defaultfilters import slugify
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from happix.models import Resource, SourceEntity, Translation
from languages.models import Language
from projects.models import Project
from storage.models import StorageFile
from txcommon.log import logger
from django.db import transaction
from uuid import uuid4


class StorageHandler(BaseHandler):
    allowed_methods = ('GET', 'POST', 'DELETE')
    model = StorageFile
    fields = ('language',('language',('code',)),'total_strings','name','created','uuid','mime_type','size')

    def delete(self, request, uuid=None):
        """
        Deletes file by storage UUID
        """
        try:
            StorageFile.objects.get(uuid=uuid, user=request.user).delete()
        except StorageFile.DoesNotExist:
            return rc.NOT_FOUND
        logger.debug("Deleted file %s" % uuid)
        return rc.DELETED

    def read(self, request, uuid=None):
        """
        Returns list of StorageFile objects
        [
            {
                "total_strings": 1102,
                "uuid": "71f4964c-817b-4778-b3e0-693375cb1355",
                "language": {
                    "code": "et"
                },
                "created": "2010-05-13 07:22:36",
                "size": 187619,
                "mime_type": "application/x-gettext",
                "name": "kmess.master.et.po"
            },
            ...
        ]
        """
        retval = StorageFile.objects.filter(user = request.user, bound=False)
        logger.debug("Returned list of users uploaded files: %s" % retval)
        return retval

    def create(self, request, uuid=None):
        """
        API call for uploading a file via POST or updating storage file attributes
        """
        if "application/json" in request.content_type: # Do API calls
            if request.data.keys() == ['language'] and uuid: # API call for changing language
                lang_code = request.data['language'] # TODO: Sanitize
                try:
                    sf = StorageFile.objects.get(uuid = uuid)
                    if lang_code == "": # Set to 'Not detected'
                        sf.language = None
                    else:
                        sf.language = Language.objects.by_code_or_alias(lang_code)
                except StorageFile.DoesNotExist:
                    return rc.NOT_FOUND # Transation file does not exist
                except Language.DoesNotExist:
                    return rc.NOT_FOUND # Translation file not found
                sf.save() # Save the change
                logger.debug("Changed language of file %s (%s) to %s" % (sf.uuid, sf.name, lang_code))
                return rc.ALL_OK
            return rc.BAD_REQUEST # Unknown API call
        elif "multipart/form-data" in request.content_type: # Do file upload
            files=[]
            for name, submitted_file in request.FILES.items():
                submitted_file = submitted_file
                sf = StorageFile()
                sf.name = str(submitted_file.name)
                sf.uuid = str(uuid4())
                file_size = 0
                fh = open(sf.get_storage_path(), 'wb')
                for chunk in submitted_file.chunks():
                    fh.write(chunk)
                    file_size += len(chunk)
                fh.close()
                sf.size = file_size
                # FIXME we should fix this for client calls
                if not request.user.is_anonymous():
                    sf.user = request.user
                if request.data.keys() == ['language']:
                    lang_code = request.data['language']
                    try:
                        sf.language =  Language.objects.by_code_or_alias(lang_code)
                    except Language.DoesNotExist:
                        logger.error("Weird! Selected language code (%s) does "
                            "not match with any language in the database." 
                            % lang_code)
                sf.update_props()
                sf.save()
                logger.debug("Uploaded file %s (%s)" % (sf.uuid, sf.name))
                files.append(dict(uuid=sf.uuid, id=str(sf.id), name=sf.name))
            result=dict(status='Created', files=files)
            # TODO: Not sure, but it looks like a hack. 'return result' 
            # should be enough.
            return HttpResponse(str(result), content_type='text/plain', status=201)
        else: # Unknown content type/API call
            return rc.BAD_REQUEST
