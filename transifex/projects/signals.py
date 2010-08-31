# -*- coding: utf-8 -*-
from django.dispatch import Signal

post_proj_save_m2m = Signal(providing_args=['instance'])
pre_comp_prep = Signal(providing_args=['instance'])
post_comp_prep = Signal(providing_args=['instance'])
submission_error = Signal(providing_args=['filename', 'message'])

pre_set_stats = Signal(providing_args=['instance'])
post_set_stats = Signal(providing_args=['instance'])

# Resource signals
post_resource_save = Signal(providing_args=['instance', 'created', 'user'])
post_resource_delete = Signal(providing_args=['instance', 'user'])

# SL Submit Translations signal
pre_submit_translation = Signal(providing_args=['instance'])
post_submit_translation = Signal(providing_args=['request', 'resource', 'language', 'modified'])

# This is obsolete:
sig_refresh_cache = Signal(providing_args=["resource"])
pre_refresh_cache = sig_refresh_cache
post_refresh_cache = Signal(providing_args=["resource"])

# This is obsolete:
sig_clear_cache = Signal(providing_args=["resource"])
pre_clear_cache = sig_clear_cache
post_clear_cache = Signal(providing_args=["resource"])

# These are obsolete:
sig_submit_file_post = Signal(providing_args=["resource"])
sig_submit_file = sig_submit_file_post
sig_submit_file_pre  = Signal(providing_args=['filename', 'resource', 'user',
    'stream', 'file_dict'])

post_submit_file = sig_submit_file_post
pre_submit_file = sig_submit_file_pre
