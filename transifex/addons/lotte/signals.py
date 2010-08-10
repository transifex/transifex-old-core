# -*- coding: utf-8 -*-
from django.dispatch import Signal

lotte_init = Signal(providing_args=["request", "resources", "language"])
lotte_done = Signal(providing_args=["request", "resources", "language", "modified"])