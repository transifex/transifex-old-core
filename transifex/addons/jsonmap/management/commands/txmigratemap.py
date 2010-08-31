import os
from optparse import make_option

from django.conf import settings
from django.core.management.base import CommandError, BaseCommand
from django.db import models

from txcommon.commands import run_command
from txcommon.log import logger

from jsonmap.models import JSONMap


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--datadir', '-d', default='.tx', dest='datadir', 
            help="Directoty for storing tx data. Default '.tx'."),
        make_option('--filename', '-f', default='txdata', dest='filename', 
            help="Filename target for JSON mapping. Default 'txdata'.")
    )

    args = '<project_slug project_slug ...>'
    help = "Create resources based on a JSON formatted mapping."

    def handle(self, *args, **options):

        # OMG!1! Dirty fix for circular importing issues. Didn't want to dig
        # into it because it's probably not worth, once it's a tmp code.
        from resources.formats import get_i18n_type_from_file
        from resources.formats.pofile import POHandler
        from languages.models import Language
        from projects.models import Project
        from resources.models import Resource

        datadir = options.get('datadir')
        filename = options.get('filename')

        msg = None
        if len(args) == 0:
            jsonmaps = JSONMap.objects.all()
        else:
            jsonmaps = JSONMap.objects.filter(project__slug__in=args)
            if not jsonmaps:
                msg = "No mapping found for given project slug(s): %s" % ', '.join(args)

        if not jsonmaps:
            raise CommandError(msg or "No mapping found in the database.")

        for jsonmap in jsonmaps:
            for r in jsonmap.loads(True)['resources']:
                logger.debug("Pushing resource: %s" % r.get('resource_slug'))

                project = jsonmap.project

                # Path for cached files of project.component
                path = os.path.join(settings.MSGMERGE_DIR,
                    '%s.%s' % (project.slug, jsonmap.slug))

                if os.path.exists(path):

                    resource_slug = r['resource_slug']
                    language = Language.objects.by_code_or_alias_or_none(
                        r['source_lang'])

                    # Create resource and load source language
                    if language:
                        resource, created = Resource.objects.get_or_create(
                                slug = resource_slug,
                                source_language = language,
                                project = project,
                                name = resource_slug)

                        source_file = os.path.join(path, r['source_file'])
                        resource.i18n_type = get_i18n_type_from_file(source_file)
                        resource.save()

                        logger.debug("Inserting source strings from %s (%s) to "
                            "'%s' (%s)." % (r['source_file'], language.code,
                            resource.slug, project))

                        fhandler = POHandler(filename=source_file)
                        fhandler.bind_resource(resource)
                        fhandler.set_language(language)

                        try:
                            fhandler.contents_check(fhandler.filename)
                            fhandler.parse_file(True)
                            strings_added, strings_updated = fhandler.save2db(True)
                        except Exception, e:
                            print "Could not import file '%s': %s" % \
                                (source_file, str(e))

                        logger.debug("Inserting translations for '%s' (%s)." 
                            % (resource.slug, project))

                        # Load translations
                        for code, f in r['translations'].items():
                            language = Language.objects.by_code_or_alias_or_none(code)
                            if language:
                                translation_file = os.path.join(path, f['file'])
                                try:
                                    fhandler = POHandler(filename=translation_file)
                                    fhandler.set_language(language)
                                    fhandler.bind_resource(resource)
                                    fhandler.contents_check(fhandler.filename)
                                    fhandler.parse_file()
                                    strings_added, strings_updated = fhandler.save2db()
                                except Exception, e:
                                    print "Could not import file '%s': %s" % \
                                        (translation_file, str(e))
                else:
                    logger.debug("Mapping '%s' does have canched files at "
                        "%s." % path)


