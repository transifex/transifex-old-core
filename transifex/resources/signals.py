# -*- coding: utf-8 -*-

from django.dispatch import Signal

post_save_translation = Signal(providing_args=['resource', 'language', 'copyrights', ])
