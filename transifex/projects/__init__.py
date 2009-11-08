from projects import signals
from txcommon.log import logger

def _updatecomponents(project):
    """
    Look through the components for a specific project and update them based 
    on the project changes
    """
    pass

def _projectpostm2mhandler(sender, **kwargs):
    if 'instance' in kwargs:
        _updatecomponents(kwargs['instance'])

signals.post_proj_save_m2m.connect(_projectpostm2mhandler)