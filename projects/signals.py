from django.dispatch import Signal

pre_comp_prep = Signal(providing_args=['instance'])
post_comp_prep = Signal(providing_args=['instance'])
