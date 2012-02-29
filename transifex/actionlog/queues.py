# -*- coding: utf-8 -*-

"""
Redis related stuff for action logs.
"""

from django.db.models import get_model
from django.utils.encoding import force_unicode
from transifex.txcommon.log import logger
from datastores.txredis import TxRedisMapper, redis_exception_handler


def redis_key_for_resource(resource):
    return 'resource:history:%s:%s' % (resource.project_id, resource.slug)


def redis_key_for_project(project):
    return 'project:history:%s' % project.slug


@redis_exception_handler
def log_to_queues(o, user_id, action_time, message):
    """Log actions to redis' queues."""
    Project = get_model('projects', 'Project')
    Resource = get_model('resources', 'Resource')
    if isinstance(o, Project):
        _log_to_recent_project_actions(o, user_id, action_time, message)
        _log_to_project_history(o, action_time, message)
    elif isinstance(o, Resource):
        _log_to_resource_history(o, action_time, message)


def _log_to_recent_project_actions(p, user_id, action_time, message):
    """Log actions that refer to projects to a queue of most recent actions.

    We use redis' list for that. We skip actions that refer to private projects.
    """
    Project = get_model('projects', 'Project')
    if p.private:
        return
    private_slugs = Project.objects.filter(
        private=True
    ).values_list('slug', flat=True)
    for slug in private_slugs:
        if ('/projects/p/%s/' % slug) in message:
            return

    key = 'event_feed'
    data = {
        'name': force_unicode(p)[:200],
        'user_id': user_id,
        'action_time': action_time,
        'message': message
    }
    r = TxRedisMapper()
    r.lpush(key, data=data)
    r.ltrim(key, 0, 11)


@redis_exception_handler
def _log_to_project_history(project, action_time, message):
    """Log a message to a project's history queue."""
    Project = get_model('projects', 'Project')
    key = redis_key_for_project(project)
    data = {
        'action_time': action_time,
        'message': message,
    }
    r = TxRedisMapper()
    r.lpush(key, data=data)
    r.ltrim(key, 0, 4)


@redis_exception_handler
def _log_to_resource_history(resource, action_time, message):
    """Log a message to a respurce's history queue."""
    Resource = get_model('resource', 'Resource')
    key = redis_key_for_resource(resource)
    data = {
        'action_time': action_time,
        'message': message,
    }
    r = TxRedisMapper()
    r.lpush(key, data=data)
    r.ltrim(key, 0, 4)
