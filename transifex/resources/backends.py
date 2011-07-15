# -*- coding: utf-8 -*-

"""
Various backend commands for resource models.

These are used by views and the API.
"""

from itertools import ifilter
from django.utils.translation import ugettext as _
from django.db import IntegrityError
from transifex.txcommon.log import logger
from transifex.resources.models import Resource
from transifex.resources.formats import FormatError
from transifex.resources.formats.registry import registry


class BackendError(Exception):
    pass


class ResourceBackendError(BackendError):
    pass


class FormatsBackendError(BackendError):
    pass


class ResourceBackend(object):
    """Backend for resources.

    This class handles creating new resources.
    """

    def create(self, project, slug, name, method, source_language,
               content, user=None, extra_data={}):
        """Create a new resource.

        Any extra arguments will be passed to the Resource initialization
        method as is.

        There is no transaction used. The caller is supposed to handle this.

        Args:
            project: A Project instance which the resource will belong to.
            slug: The slug of the resource.
            name: The name of the resource.
            method: The i18n method of theresource.
            source_language: A Language instance of the source langauge set.
            content: The content of the resource's source file.
            user: The user that creates the resource.
            extra_data: Any extra info for the Resource constructor.
        Returns:
            A two-elements tuple. The first element is the number of added
            strings and the second the number of updated strings.
        """
        # save resource
        try:
            r = Resource(
                project=project, source_language=source_language,
                slug=slug, name=name
            )
            r.i18n_method = method
            for key in ifilter(lambda k: k != "content", extra_data.iterkeys()):
                setattr(r, key, extra_data[key])
        except Exception, e:
            logger.warning(
                "Error while creating resource %s for project %s: %s" % (
                    slug, project.slug, e.message
                ), exc_info=True
            )
            raise ResourceBackendError(_("Invalid arguments given."))
        try:
            r.save()
        except IntegrityError, e:
            logger.warning("Error creating resource %s: %s" % (r, e.message))
            raise ResourceBackendError(
                "A resource with the same slug exists in this project."
            )

        # save source entities
        try:
            fb = FormatsBackend(r, source_language, user)
        except AttributeError, e:
            raise ResourceBackendError(
                "The content type of the request is not valid."
            )
        try:
            return fb.import_source(content, method)
        except FormatsBackendError, e:
            raise ResourceBackendError(e.message)
        except Exception, e:
            logger.error(
                "Unexamined exception raised: %s" % e.message, exc_info=True
            )
            raise ResourceBackendError(e.message)


class FormatsBackend(object):
    """Backend for formats operations."""

    def __init__(self, resource, language, user):
        """Initializer.

        Args:
            resource: The resource the translations will belong to.
            language: The language of the translation.
        """
        self.resource = resource
        self.language = language
        self.user = user

    def import_source(self, content, method):
        """Parse some content which is of a particular i18n type and save
        it to the database.

        Args:
            content: The content to parse.
            method: The i18n type of the content.
        Returns:
            A two-element tuple (pair). The first element is the number of
            strings added and the second one is the number of those updated.
        """
        handler = self._get_handler(method)
        return self._import_content(handler, content, True)

    def import_translation(self, content):
        """Parse a translation file for a resource.

        Args:
            content: The content to parse.
        Returns:
            A two element tuple(pair). The first element is the number of
            strings added and the second one is the number of those upadted.
        """
        handler = self._get_handler(self.resource.i18n_method)
        return self._import_content(handler, content, False)

    def _get_handler(self, method):
        """Get the appropriate hanlder for the method.

        Args:
            The i18n method used.
        """
        return registry.handler_for(method)

    def _import_content(self, handler, content, is_source):
        """Import content to the database.

        Args:
            content: The content to save.
            is_source: A flag to indicate a source or a translation file.
        Returns:
            A two element tuple(pair). The first element is the number of
            strings added and the second one is the number of those upadted.
        """
        if handler is None:
            msg = "Invalid i18n method used: %s" % method
            logger.warning(msg)
            raise FormatsBackendError(msg)
        try:
            handler.bind_resource(self.resource)
            handler.set_language(self.language)
            handler.bind_content(content)
            handler.parse_file(is_source=is_source)
            return handler.save2db(is_source=is_source, user=self.user)
        except FormatError, e:
            raise FormatsBackendError(e.message)


def content_from_uploaded_file(files, encoding='UTF-8'):
    """Get the content of an uploaded file.

    We only return the content of the first file.

    Args:
        files: A dictionary with file objects. Probably, request.FILES.
        encoding: The encoding of the file.
    Returns:
        The content of the file as a unicode string.
    """
    files = files.values()
    if not files:
        return u''
    return files[0].read().decode('UTF-8')

