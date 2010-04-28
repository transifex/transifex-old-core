# -*- coding: utf-8 -*-
from django.dispatch import Signal

webtrans_form_init = Signal(providing_args=["pofile","user"])
webtrans_form_done = Signal(providing_args=["pofile","user"])