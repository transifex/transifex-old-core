# -*- coding: utf-8 -*-

from __future__ import absolute_import

import datetime
import hashlib
import logging
import uuid

import raven
from raven import Client
from raven.conf import defaults
from raven.contrib.django import DjangoClient
from raven.utils import get_versions
from raven.utils.encoding import transform, shorten, to_string

class TxRavenClient(Client):
    """Custom Raven client for Transifex"""

    def capture(self, event_type, data=None, date=None, time_spent=None,
            event_id=None, extra=None, stack=None, **kwargs):
        """
        Overrides capture() method in Raven Client to save the value for
        'tx_bad_upload_file' key in extra argument as it is in logger.error()
        and similar other logging methods.
        """
        if data is None:
            data = {}
        if extra is None:
            extra = {}
        if not date:
            date = datetime.datetime.utcnow()
        if stack is None:
            stack = self.auto_log_stacks

        if '.' not in event_type:
            # Assume it's a builtin
            event_type = 'raven.events.%s' % event_type

        handler = self.get_handler(event_type)
        result = handler.capture(**kwargs)

        # data (explicit) culprit takes over auto event detection
        culprit = result.pop('culprit', None)
        if data.get('culprit'):
            culprit = data['culprit']

        for k, v in result.iteritems():
            if k not in data:
                data[k] = v

        if stack and 'sentry.interfaces.Stacktrace' not in data:
            if stack is True:
                frames = iter_stack_frames()

            else:
                frames = stack

            data.update({
                'sentry.interfaces.Stacktrace': {
                    'frames': varmap(lambda k, v: shorten(v,
                        string_length=self.string_max_length,
                        list_length=self.list_max_length),
                    get_stack_info(frames))
                },
            })

        if 'sentry.interfaces.Stacktrace' in data and not culprit:
            culprit = get_culprit(data['sentry.interfaces.Stacktrace'][
                'frames'], self.include_paths, self.exclude_paths)

        if not data.get('level'):
            data['level'] = logging.ERROR
        data['modules'] = get_versions(self.include_paths)
        data['server_name'] = self.name
        data.setdefault('extra', {})
        data.setdefault('level', logging.ERROR)

        # Shorten lists/strings
        for k, v in extra.iteritems():
            if k != 'tx_bad_upload_file':
                data['extra'][k] = shorten(v,
                        string_length=self.string_max_length,
                        list_length=self.list_max_length)
            else:
                data['extra'][k] = transform(v)

        if culprit:
            data['culprit'] = culprit

        if 'checksum' not in data:
            checksum_bits = handler.get_hash(data)
        else:
            checksum_bits = data['checksum']

        if isinstance(checksum_bits, (list, tuple)):
            checksum = hashlib.md5()
            for bit in checksum_bits:
                checksum.update(to_string(bit))
            checksum = checksum.hexdigest()
        else:
            checksum = checksum_bits

        data['checksum'] = checksum

        # create ID client-side so that it can be passed to application
        event_id = uuid.uuid4().hex

        # Run the data through processors
        for processor in self.get_processors():
            data.update(processor.process(data))

        # Make sure all data is coerced
        data = transform(data)

        if 'message' not in data:
            data['message'] = handler.to_string(data)

        data.update({
            'timestamp': date,
            'time_spent': time_spent,
            'event_id': event_id,
        })
        data.setdefault('project', self.project)
        data.setdefault('site', self.site)

        self.send(**data)

        return (event_id, checksum)

class TxDjangoClient(TxRavenClient, DjangoClient):
    pass



