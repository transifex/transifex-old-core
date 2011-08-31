# -*- coding: utf-8 -*-

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from notification.models import NoticeType
from transifex.actionlog.models import LogEntry
from transifex.txcommon.tests.base import BaseTestCase, NoticeTypes


class TestActionLog(NoticeTypes, BaseTestCase):

    def test_content_type_model_field(self):
        """Test that the denormalized `content_type_model` field is
        correctly saved.
        """
        u = self.user['maintainer']
        p = self.project
        c = ContentType.objects.get(model='project')
        n = NoticeType.objects.get(label='project_changed')
        log_entry = LogEntry()
        log_entry.user = u
        log_entry.object_id = p.id
        log_entry.content_type = c
        log_entry.action_type = n
        log_entry.save()
        self.assertEquals(log_entry.content_type_model, 'project')

