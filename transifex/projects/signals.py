from django.dispatch import Signal

post_proj_save_m2m = Signal(providing_args=['instance'])
pre_comp_prep = Signal(providing_args=['instance'])
post_comp_prep = Signal(providing_args=['instance'])
submission_error = Signal(providing_args=['filename', 'message'])
