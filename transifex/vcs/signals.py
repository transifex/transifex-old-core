from django.dispatch import Signal

# Reporting tool signals
pre_prepare_repo = Signal(providing_args=['instance'])
post_prepare_repo = Signal(providing_args=['instance'])
