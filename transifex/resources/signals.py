# -*- coding: utf-8 -*-

from django.dispatch import Signal


post_save_translation = Signal()
post_update_rlstats = Signal()
# Translations are deleted
post_delete_translations = Signal()
