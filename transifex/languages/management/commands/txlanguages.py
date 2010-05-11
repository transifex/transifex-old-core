# -*- coding: utf-8 -*-
"""
File containing the necessary mechanics for the txlanguages management command.
"""
from optparse import make_option, OptionParser
import sys
import simplejson
from django.core import serializers
from django.core.management.base import (BaseCommand, LabelCommand, CommandError)
from languages.models import Language

_DEFAULT_FIXTURE = 'languages/fixtures/sample_languages.json'

_help_text = ('Create, Update, or Export the default languages.\n'
        '\t--export [filename] for export to stdout or to the filename '
        '(filename is optional)\n'
        '\t--import [filename] to import from a file. If not given will try '
        'to load data from the default fixture file (%s)\n' %
        _DEFAULT_FIXTURE)


class Command(LabelCommand):
    """
    Management Command Class about language updates
    """
    help = _help_text
    option_list = LabelCommand.option_list + (
        make_option('--import', action='store_true',
                    dest='doimport', default=False,
            help='Import data from a file or from the default '),
        make_option('--export', action='store_true',
                    dest='doexport', default=False,
            help='Be more verbose in reporting progress.'),
        make_option('--verbose', action='store_true',
                dest='verbose', default=False,
        help='Be more verbose in reporting progress.'),
    )
    
    requires_model_validation = False
    can_import_settings = True

    def handle(self, *args, **options):
        verbose = options.get('verbose')
        doimport = options.get('doimport')
        doexport = options.get('doexport')
        
        if doimport and doexport:
            raise CommandError("The arguments '--import' and '--export' can "
                "not be used simultaneously.")

        if doimport:
            import_lang(filename=get_filename(args), verbose=verbose)
            return
        if doexport:
            export_lang(filename=get_filename(args), verbose=verbose)
            return

        #default functionality of previous version.
        import_lang(verbose=verbose)

def export_lang(filename=None, verbose=False):
    """
    Export the already existing languages

    Just like the dumpdata does but just for a specific model it serializes the
    models contents and depending on the filename it either writes to it or to
    stdout.
    """
    data = serializers.serialize("json", Language.objects.all().order_by('id'),
        indent=2)
    if filename:
        storefile = None
        try:
            storefile = open(filename, 'w')
            storefile.write(data)
        except:
            pass
        if storefile:
            storefile.close()
    else:
        print data

def import_lang(filename=None, verbose=False):
    """
    Import languages

    Input (optional) : filepath(relative or full) to the json file
    If not given load the default fixture.

    Its logic is simple:
        1) Open the fixture file
        2) Read the json data
        3) For each model's object at the json data update references in the db
    """

    if not filename:
        filename=_DEFAULT_FIXTURE

    try:
        datafile = open(filename, 'r')
    except IOError:
        print 'Cannot open ', filename
        return
    except:
        print "Unexpected error:", sys.exc_info()[0]
        return

    data = simplejson.load(datafile)
    if verbose:
        fill_the_database_verbose(data)
    else:
        fill_the_database_silently(data)

def fill_the_database_verbose(data):
    """
    Update the language object and be verbose about it.
    """
    for obj in data:
        fields = obj['fields']
        lang, created = Language.objects.get_or_create(code=fields['code'])
        if created:
            print 'Creating %s language (%s)' % (fields['name'], fields['code'])
        else:
            print 'Updating %s language (%s)' % (fields['name'], fields['code'])
        fill_language_data(lang, fields)

def fill_the_database_silently(data):
    """
    Update the language object without producing any more noise.
    """
    for obj in data:
        fields = obj['fields']
        lang, created = Language.objects.get_or_create(code=fields['code'])
        fill_language_data(lang, fields)

def fill_language_data(lang, fields):
    """
    Based on the fields update the lang object.
    """
    lang.code_aliases = fields['code_aliases']
    lang.name = fields['name']
    lang.specialchars = fields['specialchars']
    lang.nplurals = fields['nplurals']
    lang.pluralequation = fields['pluralequation']
    lang.description = fields['description']
    lang.save()

def get_filename(args):
    ret=None
    try:
        ret=args[0]
    except:
        pass
    return ret