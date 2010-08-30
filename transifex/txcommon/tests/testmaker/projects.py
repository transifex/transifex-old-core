#coding: utf-8
from django.core import management
from django.test import TestCase
from django_addons.autodiscover import autodiscover_notifications



class TestmakerBase(TestCase):
    fixtures = ["sample_data", "sample_users", "sample_site", "sample_languages"]


class TestmakerAnonymous(TestmakerBase):

    # Homepage
    def test__128272158449(self):
        r = self.client.get('/', {})
        self.assertEqual(r.status_code, 200)
        self.assertTrue(u"id_username" in r.content)
        self.assertEqual(unicode(r.context["user"]), u"""AnonymousUser""")
        self.assertEqual(unicode(r.context["signup_url"]), u"""/accounts/register/""")


class TestmakerLoggedIn(TestmakerBase):

    def setUp(self, *args, **kwargs):
        super(TestmakerLoggedIn, self).setUp(*args, **kwargs)
        # Login
        r = self.client.post('/accounts/login/',
            {'username': 'editor', 'password': 'editor', 'blogin': 'Sign in', 'next': '/', })
        
    # Homepage

    def test__128272158449(self):
        r = self.client.get('/', {})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'editor')
  
    # Projects

    def test_projects_128272193615(self):
        r = self.client.get('/projects/', {})
        self.assertEqual(r.status_code, 200)
        self.assertTrue("Example Project" in r.content)

    def test_projectspexample_128272202817(self):
        r = self.client.get('/projects/p/example/', {})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(unicode(r.context["project"]), u"""Example Project""")
        self.assertEqual(unicode(r.context["languages"][0]), u"""Afrikaans (af)""")


    def test_projectspexampleeditaccess_12828136919(self):
        r = self.client.get('/projects/p/example/edit/access/', {})
        self.assertEqual(r.status_code, 200)

    # Timeline

    def test_projectspexampletimeline_12828136955(self):
        r = self.client.get('/projects/p/example/timeline/', {})
        self.assertEqual(r.status_code, 200)

    def test_projectspexampletimeline_128281374911(self):
        r = self.client.get('/projects/p/example/timeline/', {'action_time': '', 'action_type': '2', })
        self.assertEqual(r.status_code, 200)

    # Widgets

    def test_projectspexamplewidgets_12828136967(self):
        r = self.client.get('/projects/p/example/widgets/', {})
        self.assertEqual(r.status_code, 200)

    def test_projectspexampleresourcetransifexdefaultdjangopochart_128281369682(self):
        r = self.client.get('/projects/p/example/resource/transifexdefaultdjangopo/chart/', {})
        self.assertEqual(r.status_code, 200)

    def test_projectspexampleresourcetransifexdefaultdjangopochartinc_js_128281369702(self):
        r = self.client.get('/projects/p/example/resource/transifexdefaultdjangopo/chart/inc_js/', {})
        self.assertEqual(r.status_code, 200)

    def test_projectspexampleresourcetransifexdefaultdjangopochartimage_png_12828136972(self):
        r = self.client.get('/projects/p/example/resource/transifexdefaultdjangopo/chart/image_png/', {})
        self.assertEqual(r.status_code, 302)

    def test_projectspexampleresourcetransifexdefaultdjangopochartjson_128281369791(self):
        r = self.client.get('/projects/p/example/resource/transifexdefaultdjangopo/chart/json/', {'tqx': 'reqId:0', })
        self.assertEqual(r.status_code, 200)

    # Teams

    def test_projectspexampleteams_128281369378(self):
        r = self.client.get('/projects/p/example/teams/', {})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(unicode(r.context["project"]), u"""Example Project""")
        self.assertTrue("Afrikaans (af)" in unicode(r.context["team_request_form"]))

    def test_projectspexampleteamsadd_128281371426(self):
        r = self.client.get('/projects/p/example/teams/add/', {})
        self.assertEqual(r.status_code, 200)
        
    def test_projectspexampleteamsadd_128281371653(self):
        r = self.client.post('/projects/p/example/teams/add/', {'language': '', 'creator': '', 'mainlist': '', 'save_team': 'Save team', 'members_text': '', 'next': '', 'project': '1', 'coordinators': '|', 'coordinators_text': '', 'members': '|', }, follow=True)
        self.assertContains(r, 'This field is required', status_code=200)

    def test_ajaxajax_lookupusers_128281371984(self):
        r = self.client.get('/ajax/ajax_lookup/users', {'q': 'ed', 'timestamp': '1282813719831', 'limit': '150', })
        self.assertContains(r, 'editor', status_code=200)

    def test_projectspexampleteamsadd_128281372177(self):
        r = self.client.post('/projects/p/example/teams/add/', {'language': '1', 'creator': '1', 'mainlist': '', 'save_team': 'Save team', 'members_text': '', 'next': '', 'project': '1', 'coordinators': '|1|', 'coordinators_text': '', 'members': '|', }, follow=True)
        self.assertEqual(r.status_code, 200)

        r = self.client.get('/projects/p/example/team/af/', {})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(unicode(r.context["team_access_requests"]), u"""[]""")
        self.assertEqual(unicode(r.context["team"]), u"""example.af""")

        r = self.client.get('/projects/p/example/team/af/delete/', {})
        self.assertEqual(r.status_code, 200)

    def test_projectspexampleteamafdelete_128282090157(self):
        r = self.client.post('/projects/p/example/team/af/delete/', {'team_delete': "Yes, I'm sure!", })
        r = self.client.get('/projects/p/example/team/af/', {})
        self.assertEqual(r.status_code, 404)

    # Edit project

    def test_projectspexampleedit_128281375582(self):
        r = self.client.get('/projects/p/example/edit/', {})
        self.assertEqual(r.status_code, 200)

    def test_projectspexampleedit_128281375684(self):
        r = self.client.post('/projects/p/example/edit/', {'project-feed': '', 'project-name': 'Example Project', 'project-tags': '', 'project-maintainers_text': '', 'project-long_description': '', 'project-maintainers': '|1|', 'project-description': 'This is an example project', 'project-bug_tracker': '', 'project-homepage': 'http://www.example.com/', 'project-slug': 'example', }, follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertTrue('projects/p/example/' in r.redirect_chain[0][0])


    # Create resource

    def test_apistorage_128281378077(self):
        r = self.client.post('/api/storage/', {'language': 'af', })
    def test_projectspexample_128281378221(self):
        r = self.client.post('/projects/p/example/', {'create_form-source_file_0': 'af', 'create_form-source_file_1': '7', 'create_resource': 'Create Resource', 'create_form-source_file-uuid': '348a8c41-72d0-4203-b994-0bfaba9a5e7e', })
    def test_apiprojectexamplefiles_128281378257(self):
        r = self.client.post('/api/project/example/files/', {'{"uuid":"348a8c41-72d0-4203-b994-0bfaba9a5e7e"}': '', })
    def test_projectspexampleresource2po_128281378344(self):
        r = self.client.get('/projects/p/example/resource/2po/', {})

    # Other

    def test_faviconico_128281378356(self):
        r = self.client.get('/favicon.ico', {})
        self.assertNotEqual(r.status_code, 404)

