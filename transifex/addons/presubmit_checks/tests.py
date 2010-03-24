# -*- coding: utf-8 -*-
from StringIO import StringIO
from django.core.urlresolvers import reverse
from txcommon.tests.base import TransifexBaseTestCase

class TestPresubmitChecks(TransifexBaseTestCase):
    def test_main(self):
        def get_file_handle(pof):
            return open(self.component.trans.tm.get_file_path(pof.filename))

        # Select first POFile
        self.pofile = self.pofiles.get(language_code = 'fi')

        # Generate URLs
        url_args = [self.pofile.object.project.slug,
            self.pofile.object.slug, self.pofile.filename]
        self.url_submit = reverse('component_submit_file', args=url_args)

        # Enable submission        
        self.component.allows_submission = True
        self.component.anyone_submit = True
        self.component.save()

        # Try to submit file as translator: should succeed
        resp = self.client['maint'].post(self.url_submit, {'submitted_file':
            get_file_handle(self.pofile),'message':'Test'}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue("File submitted successfully" in resp.content)

        # (6.3) Try to submit file with extension not ending with .po
        stream = StringIO("")
        stream.name = "test.jibberish"
        resp = self.client['maint'].post(self.url_submit, {'submitted_file':
            stream,'message':'Test'}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue("You are only allowed to upload PO files" in resp.content)

        # (6.1) Try to submit empty file
        stream = StringIO("")
        stream.name = "test.po"
        resp = self.client['maint'].post(self.url_submit, {'submitted_file':
            stream,'message':'Test'}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue("You have submitted empty file" in resp.content)

        # (6.4) Try to submit file with DOS newlines
        stream = StringIO("Line1\r\Line2")
        stream.name = "test.po"
        resp = self.client['maint'].post(self.url_submit, {'submitted_file':
            stream,'message':'Test'}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue("file contains DOS newlines" in resp.content)


