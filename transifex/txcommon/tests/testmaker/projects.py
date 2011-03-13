#coding: utf-8
from django.core import management
from django.test import TestCase
from django_addons.autodiscover import autodiscover_notifications
from transifex.txcommon.tests.base import BaseTestCase


class TestmakerBase(BaseTestCase):
    #fixtures = ["sample_data", "sample_users", "sample_site", "sample_languages"]
    pass


class TestmakerAnonymous(TestmakerBase):

    # Homepage
    def test__128272158449(self):
        r = self.client["anonymous"].get('/', {})
        self.assertEqual(r.status_code, 200)
        self.assertTrue("id_username" in r.content)


class TestmakerLoggedIn(TestmakerBase):

    def setUp(self, *args, **kwargs):
        super(TestmakerLoggedIn, self).setUp(*args, **kwargs)
        self.c = self.client["team_member"]
        # Login
        r = self.c.post('/accounts/login/',
            {'username': 'editor', 'password': 'editor', 'blogin': 'Sign in', 'next': '/', })

    # Homepage

    def test__128272158449(self):
        r = self.c.get('/', {})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'editor')

    # Projects

    def test_projects_128272193615(self):
        r = self.c.get('/projects/', {})
        self.assertEqual(r.status_code, 200)
        self.assertTrue("Test Project" in r.content)

    def test_projectspexample_128272202817(self):
        r = self.c.get('/projects/p/project1/', {})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(unicode(r.context["project"]), u"""Test Project""")
        self.assertEqual(unicode(r.context["languages"][0]), u"""Afrikaans (af)""")


    def test_projectspexampleeditaccess_12828136919(self):
        r = self.c.get('/projects/p/project1/edit/access/', {})
        self.assertEqual(r.status_code, 200)

    # Timeline

    def test_projectspexampletimeline_12828136955(self):
        r = self.c.get('/projects/p/project1/timeline/', {})
        self.assertEqual(r.status_code, 200)

    def test_projectspexampletimeline_128281374911(self):
        r = self.c.get('/projects/p/project1/timeline/', {'action_time': '', 'action_type': '2', })
        self.assertEqual(r.status_code, 200)

    # Widgets

    def test_projectspexamplewidgets_12828136967(self):
        r = self.c.get('/projects/p/project1/widgets/', {})
        self.assertEqual(r.status_code, 200)

    def test_projectspexampleresourceresource1chart_128281369682(self):
        r = self.c.get('/projects/p/project1/resource/resource1/chart/', {})
        self.assertEqual(r.status_code, 200)

    def test_projectspexampleresourceresource1chartinc_js_128281369702(self):
        r = self.c.get('/projects/p/project1/resource/resource1/chart/inc_js/', {})
        self.assertEqual(r.status_code, 200)

    def test_projectspexampleresourceresource1chartimage_png_12828136972(self):
        r = self.c.get('/projects/p/project1/resource/resource1/chart/image_png/', {})
        self.assertEqual(r.status_code, 302)

    def test_projectspexampleresourceresource1chartjson_128281369791(self):
        r = self.c.get('/projects/p/project1/resource/resource1/chart/json/', {'tqx': 'reqId:0', })
        self.assertEqual(r.status_code, 200)

    # Teams

    def test_projectspexampleteams_128281369378(self):
        r = self.c.get('/projects/p/project1/teams/', {})
        self.assertEqual(r.status_code, 200)
        self.assertTrue("Afrikaans (af)" in unicode(r.context["team_request_form"]))

    def test_projectspexampleteamsadd_128281371426(self):
        r = self.c.get('/projects/p/project1/teams/add/', {})
        self.assertEqual(r.status_code, 200)

    def test_projectspexampleteamsadd_128281371653(self):
        r = self.c.post('/projects/p/project1/teams/add/', {'language': '', 'creator': '', 'mainlist': '', 'save_team': 'Save team', 'members_text': '', 'next': '', 'project': '1', 'coordinators': '|', 'coordinators_text': '', 'members': '|', }, follow=True)
        self.assertContains(r, 'This field is required', status_code=200)

    def test_ajaxajax_lookupusers_128281371984(self):
        r = self.c.get('/ajax/ajax_lookup/users', {'q': 'ed', 'timestamp': '1282813719831', 'limit': '150', })
        self.assertContains(r, 'editor', status_code=200)

    def test_projectspexampleteamsadd_128281372177(self):
        r = self.c.post('/projects/p/project1/teams/add/', {'language': '1', 'creator': '1', 'mainlist': '', 'save_team': 'Save team', 'members_text': '', 'next': '', 'project': '1', 'coordinators': '|1|', 'coordinators_text': '', 'members': '|', }, follow=True)
        self.assertEqual(r.status_code, 200)

        r = self.c.get('/projects/p/project1/team/af/', {})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(unicode(r.context["team_access_requests"]), u"""[]""")
        self.assertEqual(unicode(r.context["team"]), u"""project1.af""")

        r = self.c.get('/projects/p/project1/team/af/delete/', {})
        self.assertEqual(r.status_code, 200)

    def test_projectspexampleteamafdelete_128282090157(self):
        r = self.c.post('/projects/p/project1/team/af/delete/', {'team_delete': "Yes, I'm sure!", })
        r = self.c.get('/projects/p/project1/team/af/', {})
        self.assertEqual(r.status_code, 404)

    # Edit project

    def test_projectspexampleedit_128281375582(self):
        r = self.c.get('/projects/p/project1/edit/', {})
        self.assertEqual(r.status_code, 200)

    def test_projectspexampleedit_128281375684(self):
        r = self.c.post('/projects/p/project1/edit/', {'project-feed': '', 'project-name': 'Test Project', 'project-tags': '', 'project-maintainers_text': '', 'project-long_description': '', 'project-maintainers': '|1|', 'project-description': 'This is a test project', 'project-bug_tracker': '', 'project-homepage': 'http://www.example.com/', 'project-slug': 'project1', }, follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertTrue('projects/p/project1/' in r.redirect_chain[0][0])


    # Create resource

    def test_apistorage_128281378077(self):
        r = self.c.post('/api/storage/', {'language': 'af', })
    def test_projectspexample_128281378221(self):
        r = self.c.post('/projects/p/project1/', {'create_form-source_file_0': 'af', 'create_form-source_file_1': '7', 'create_resource': 'Create Resource', 'create_form-source_file-uuid': '348a8c41-72d0-4203-b994-0bfaba9a5e7e', })
    def test_apiprojectexamplefiles_128281378257(self):
        r = self.c.post('/api/project/example/files/', {'{"uuid":"348a8c41-72d0-4203-b994-0bfaba9a5e7e"}': '', })
    def test_projectspexampleresource2po_128281378344(self):
        r = self.c.get('/projects/p/project1/resource/2po/', {})

    # Other

    def test_faviconico_128281378356(self):
        r = self.c.get('/favicon.ico', {})
        self.assertNotEqual(r.status_code, 404)

