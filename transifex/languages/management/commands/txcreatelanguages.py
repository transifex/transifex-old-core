"""
This is an obsoleted file left for backwards compatibility reasons.
"""
# -*- coding: utf-8 -*-
import warnings
from django.core.management import  call_command
from django.core.management.base import NoArgsCommand

class Command(NoArgsCommand):
    """
    Call the txlanguages with default arguments and let it do the rest
    """
    help = 'Create or Update the default languages.'

    requires_model_validation = False
    can_import_settings = True

    def handle_noargs(self, **options):
        """
        Just call the txlanguages management command
        """
        warnings.warn("Deprecated.\n\nUse txlanguages management command instead.",
            DeprecationWarning)
        call_command('txlanguages')