# -*- coding: utf-8 -*-
from django.dispatch import Signal

post_proj_save_m2m = Signal(providing_args=['instance'])
pre_comp_prep = Signal(providing_args=['instance'])
post_comp_prep = Signal(providing_args=['instance'])
submission_error = Signal(providing_args=['filename', 'message'])

pre_set_stats = Signal(providing_args=['instance'])
post_set_stats = Signal(providing_args=['instance'])

# This is obsolete:
sig_refresh_cache = Signal(providing_args=["component"])
pre_refresh_cache = sig_refresh_cache
post_refresh_cache = Signal(providing_args=["component"])

# This is obsolete:
sig_clear_cache = Signal(providing_args=["component"])
pre_clear_cache = sig_clear_cache
post_clear_cache = Signal(providing_args=["component"])

# These are obsolete:
sig_submit_file_post = Signal(providing_args=["component"])
sig_submit_file = sig_submit_file_post
sig_submit_file_pre  = Signal(providing_args=['filename', 'component', 'user',
    'stream', 'file_dict'])

post_submit_file = sig_submit_file_post
pre_submit_file = sig_submit_file_pre