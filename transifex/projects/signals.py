from django.dispatch import Signal

post_proj_save_m2m = Signal(providing_args=['instance'])
pre_comp_prep = Signal(providing_args=['instance'])
post_comp_prep = Signal(providing_args=['instance'])
submission_error = Signal(providing_args=['filename', 'message'])

pre_set_stats = Signal(providing_args=['instance'])
post_set_stats = Signal(providing_args=['instance'])

sig_refresh_cache = Signal(providing_args=["component"])
sig_clear_cache = Signal(providing_args=["component"])
sig_submit_file = Signal(providing_args=["component"])