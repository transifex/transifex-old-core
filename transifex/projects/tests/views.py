# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from transifex.txcommon.tests import base, utils

class ProjectViewsTests(base.BaseTestCase):

    # Note: The Project lookup field is tested elsewhere.
    def setUp(self, *args, **kwargs):
        super(ProjectViewsTests, self).setUp(*args, **kwargs)
        self.url_acc = reverse('project_access_control_edit', args=[self.project.slug])

    def test_project_outsource_good(self):
        """Test that a private project is visible to its maintainer."""
        resp = self.client['maintainer'].get(self.url_acc, {})
        self.assertContains(resp, "Test Project", status_code=200)
        self.assertContains(resp, "Test Private Project", status_code=200)


    def test_project_outsource_bad(self):
        # Private project is not visible to another maintainer
        self.assertTrue(self.user['registered'] not in self.project_private.maintainers.all())
        self.project.maintainers.add(self.user['registered'])
        self.assertTrue(self.user['registered'] in self.project.maintainers.all())
        resp = self.client['registered'].get(self.url_acc, {})
        self.assertContains(resp, "Test Project", status_code=200)
        self.assertNotContains(resp, "Test Private Project", status_code=200)
        
        # Private project cannot be used by another maintainer to outsource
        resp = self.client['registered'].post(self.url_acc, {
            'outsource': self.project_private.id,
            'submit_access_control': 'Save Access Control Settings',
            'access_control': 'outsourced_access',
            'next': '/projects/p/desktop-effects/edit/access/', })
        self.assertFalse(self.project.outsource)
        self.assertTemplateUsed(resp, "projects/project_form_access_control.html")
        self.assertContains(resp, "Select a valid choice.")

    def test_delete_project(self):
        url = reverse('project_delete', args=[self.project.slug])
        resp = self.client['maintainer'].get(url)
        self.assertContains(resp, "Say goodbye")
        resp = self.client['maintainer'].post(url, follow=True)
        self.assertContains(resp, "was deleted.")
        # Test messages:
        self.assertContains(resp, "message_success")

