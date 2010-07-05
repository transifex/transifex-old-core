# -*- coding: utf-8 -*-
from django.dispatch import Signal

webtrans_form_init = Signal(providing_args=["request","pofile"])
webtrans_form_done = Signal(providing_args=["request","pofile"])