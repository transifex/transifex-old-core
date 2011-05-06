# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.utils import simplejson
from transifex.txcommon.tests.base import BaseTestCase
from transifex.resources.models import RLStats, Resource
from django.contrib.auth.models import User, Permission
from transifex.projects.models import Project
from transifex.storage.models import StorageFile
from transifex.storage.tests.api import BaseStorageTests

class ProjectResourceAPITests(BaseStorageTests):
    """
    Test the status codes.
    """
    def test_resource_creation(self):
        """Test creation of resource through the API."""

        self.create_storage()

        data = '{"uuid": "%s"}' % self.uuid
        resp = self.client['registered'].post(reverse('api_project_files',
            args=[self.project.slug]), data, content_type="application/json")
        self.assertTrue('Forbidden access' in resp.content)
        self.assertEqual(resp.status_code, 403)

        resp = self.client['maintainer'].post(reverse('api_project_files',
            args=[self.project.slug]), data, content_type="application/json")
        self.assertEqual(eval(resp.content)['strings_added'], 3)
        self.assertEqual(resp.status_code, 200)

        # To be used in other tests
        self.resource_slug = eval(resp.content)['redirect'].split(
            '/resource/')[1].replace('/','')

        # Some extra check around denormalization
        rls = RLStats.objects.get(resource__project=self.project,
            resource__slug=self.resource_slug, language=self.language_en)

        self.assertEqual(rls.translated, 3)
        self.assertEqual(rls.total, 3)
        self.assertEqual(rls.translated_perc, 100)

    def test_submission_translation(self):
        """Test submission of translation through the API."""

        self.test_resource_creation()

        # Changing language of the storagefile object
        sf = StorageFile.objects.get(uuid=self.uuid)
        sf.language = self.language
        sf.save()

        data = '{"uuid": "%s"}' % self.uuid
        resp = self.client['maintainer'].put(reverse('api_resource_storage',
            args=[self.project.slug, self.resource_slug, self.language.code]),
            data, content_type="application/json")
        self.assertEqual(eval(resp.content)['strings_added'], 3)

        # Some extra check around denormalization
        rls = RLStats.objects.get(resource__project=self.project,
            resource__slug=self.resource_slug, language=self.language)

        resource = Resource.objects.get(project=self.project,
            slug=self.resource_slug)

        self.assertEqual(rls.translated, 3)
        self.assertEqual(rls.total, 3)
        self.assertEqual(rls.translated_perc, 100)

class TestProjectAPI(BaseTestCase):

    def setUp(self):
        super(TestProjectAPI, self).setUp()
        self.url_projects = reverse('apiv2_projects')
        self.url_project = reverse('apiv2_project', kwargs={'project_slug': 'foo'})

    def test_get(self):
        res = self.client['anonymous'].get(self.url_projects)
        self.assertEquals(res.status_code, 401)
        res = self.client['maintainer'].get(self.url_projects + "?details")
        self.assertEquals(res.status_code, 501)
        res = self.client['maintainer'].get(self.url_projects)
        self.assertEquals(res.status_code, 200)
        data = simplejson.loads(res.content)
        self.assertEquals(len(data), 7)
        self.assertFalse('created' in data[0])
        self.assertTrue('slug' in data[0])
        self.assertTrue('name' in data[0])
        res = self.client['registered'].get(self.url_projects)
        self.assertEquals(res.status_code, 200)
        data = simplejson.loads(res.content)
        self.assertEquals(len(data), 6)
        res = self.client['anonymous'].get(self.url_project)
        self.assertEquals(res.status_code, 401)
        res = self.client['registered'].get(self.url_project)
        self.assertEquals(res.status_code, 404)
        private_url = "/".join([self.url_projects[:-2], self.project_private.slug, ''])
        res = self.client['registered'].get(private_url)
        self.assertEquals(res.status_code, 401)
        res = self.client['maintainer'].get(private_url)
        self.assertEquals(res.status_code, 200)
        public_url = "/".join([self.url_projects[:-2], self.project.slug, ''])
        res = self.client['registered'].get(public_url + "?details")
        self.assertEquals(res.status_code, 200)
        self.assertEquals(len(simplejson.loads(res.content)), 14)
        self.assertTrue('created' in simplejson.loads(res.content))
        public_url = "/".join(
            [self.url_projects[:-2], self.project.slug, ""]
        )
        res = self.client['registered'].get(public_url)
        self.assertEquals(res.status_code, 200)
        self.assertTrue('slug' in simplejson.loads(res.content))
        self.assertTrue('name' in simplejson.loads(res.content))
        self.assertTrue('description' in simplejson.loads(res.content))
        self.assertEquals(len(simplejson.loads(res.content)), 3)

        # Test pagination
        res = self.client['registered'].get(self.url_projects + "?start=5")
        self.assertEquals(res.status_code, 200)
        data = simplejson.loads(res.content)
        self.assertEquals(len(data), 2)
        res = self.client['registered'].get(self.url_projects + "?end=5")
        self.assertEquals(res.status_code, 200)
        data = simplejson.loads(res.content)
        self.assertEquals(len(data), 4)
        res = self.client['registered'].get(self.url_projects + "?start=a")
        self.assertEquals(res.status_code, 400)
        res = self.client['registered'].get(self.url_projects + "?start=0")
        self.assertEquals(res.status_code, 400)
        res = self.client['registered'].get(self.url_projects + "?end=0")
        self.assertEquals(res.status_code, 400)
        res = self.client['registered'].get(self.url_projects + "?start=1&end=4")
        self.assertEquals(res.status_code, 200)
        data = simplejson.loads(res.content)
        self.assertEquals(len(data), 3)
        res = self.client['registered'].get(self.url_projects + "?start=1&end=4")
        data = simplejson.loads(res.content)
        self.assertEquals(len(data), 3)
        self.assertEquals(res.status_code, 200)

    def test_post(self):
        res = self.client['anonymous'].post(self.url_projects, content_type='application/json')
        self.assertEquals(res.status_code, 401)
        res = self.client['registered'].post(self.url_project, content_type='application/json')
        self.assertContains(res, "POSTing to this url is not allowed", status_code=400)
        res = self.client['registered'].post(self.url_projects)
        self.assertContains(res, "Bad Request", status_code=400)
        res = self.client['registered'].post(
            self.url_projects, simplejson.dumps({'name': 'name of project'}),
            content_type="application/json"
        )
        self.assertContains(res, "Field slug is required to create a new project.", status_code=400)
        res = self.client['registered'].post(
            self.url_projects, simplejson.dumps({'slug': 'slug'}), content_type='application/json'
        )
        self.assertContains(res, "Field name is required to create a new project.", status_code=400)
        res = self.client['registered'].post(
            self.url_projects, simplejson.dumps({
                'slug': 'slug', 'name': 'name', 'owner': 'owner'
            }),
            content_type='application/json'
        )
        self.assertContains(res, "Owner cannot be set explicitly.", status_code=400)
        res = self.client['registered'].post(
            self.url_projects, simplejson.dumps({
                'slug': 'api_project',
                'name': 'Project from API',
                'outsource': 'not_exists',
            }),
            content_type='application/json'
        )
        self.assertContains(res, "Project for outsource does not exist", status_code=400)
        res = self.client['registered'].post(
            self.url_projects, simplejson.dumps({
                'slug': 'api_project', 'name': 'Project from API',
                'maintainers': 'not_exists',
            }),
            content_type='application/json'
        )
        self.assertContains(res, "User", status_code=400)
        res = self.client['registered'].post(
            self.url_projects, simplejson.dumps({
                'slug': 'api_project_maintainers',
                'name': 'Project from API',
                'maintainers': 'registered',
                'none': 'none'
            }),
            content_type='application/json'
        )
        self.assertContains(res, "Field 'none'", status_code=400)
        res = self.client['registered'].post(
            self.url_projects, simplejson.dumps({
                'slug': 'api_project_maintainers',
                'name': 'Project from API',
                'maintainers': 'registered'
            }),
            content_type='application/json'
        )
        self.assertEquals(res.status_code, 201)
        self.assertEquals(len(Project.objects.all()), 8)
        res = self.client['registered'].post(
            self.url_projects, simplejson.dumps({
                'slug': 'api_project', 'name': 'Project from API',
            }),
            content_type='application/json'
        )
        self.assertEquals(res.status_code, 201)
        self.assertEquals(len(Project.objects.all()), 9)
        res = self.client['registered'].post(
            self.url_projects, simplejson.dumps({
                'slug': 'api_project', 'name': 'Project from API',
            }),
            content_type='application/json'
        )
        self.assertEquals(res.status_code, 409)
        # Check permissions
        user = User.objects.get(username='registered')
        user.groups = []
        user.save()
        res = self.client['registered'].post(
            self.url_projects, simplejson.dumps({
                'slug': 'api_project_2', 'name': 'Project from API - second',
            }),
            content_type='application/json'
        )
        self.assertEquals(res.status_code, 403)

    def test_put(self):
        res = self.client['anonymous'].put(
            self.url_project, data=simplejson.dumps({}),
            content_type='application/json'
        )
        self.assertEquals(res.status_code, 401)
        res = self.client['registered'].put(self.url_project)
        self.assertEquals(res.status_code, 400)
        res = self.client['registered'].put(
            self.url_project[:-1] + "1/",
            simplejson.dumps({'name': 'name of project'}),
            content_type="application/json"
        )
        self.assertEquals(res.status_code, 404)
        res = self.client['registered'].post(
            self.url_projects, simplejson.dumps({
                'slug': 'foo', 'name': 'Foo Project',
            }),
            content_type='application/json'
        )
        self.assertEquals(res.status_code, 201)
        res = self.client['registered'].put(
            self.url_project, data=simplejson.dumps({}),
            content_type='application/json'
        )
        self.assertEquals(res.status_code, 403)
        user = User.objects.get(username='registered')
        user.user_permissions.add(
            Permission.objects.get(codename="change_project")
        )
        res = self.client['registered'].put(
            self.url_project,
            data=simplejson.dumps({'foo': 'foo'}),
            content_type='application/json'
        )
        self.assertContains(res, "Field 'foo'", status_code=400)
        res = self.client['registered'].put(
            self.url_project, data=simplejson.dumps({}),
            content_type='application/json'
        )
        self.assertEquals(res.status_code, 200)
        name = 'New name for foo'
        res = self.client['registered'].put(
            self.url_project,
            data=simplejson.dumps({'name': name}),
            content_type='application/json'
        )
        self.assertEquals(res.status_code, 200)
        p_foo = Project.objects.get(slug="foo")
        self.assertEquals(p_foo.name, name)
        res = self.client['registered'].put(
            self.url_project,
            data=simplejson.dumps({'outsource': "foo"}),
            content_type='application/json'
        )
        self.assertContains(res, "Original and outsource projects are the same", status_code=400)
        res = self.client['registered'].put(
            self.url_project,
            data=simplejson.dumps({'outsource': "bar"}),
            content_type='application/json'
        )
        self.assertContains(res, "Project for outsource does not exist", status_code=400)
        res = self.client['registered'].put(
            self.url_project,
            data=simplejson.dumps({'maintainers': 'none, not'}),
            content_type='application/json'
        )
        self.assertContains(res, "User", status_code=400)


    def test_delete(self):
        res = self.client['anonymous'].delete(self.url_project)
        self.assertEquals(res.status_code, 401)
        res = self.client['registered'].delete(self.url_projects)
        self.assertEquals(res.status_code, 403)
        user = User.objects.get(username='registered')
        user.user_permissions.add(
            Permission.objects.get(codename="delete_project")
        )
        res = self.client['registered'].delete(self.url_projects)
        self.assertEquals(res.status_code, 400)
        self.assertContains(res, "Project slug not specified", status_code=400)
        res = self.client['registered'].delete(self.url_project)
        self.assertEquals(res.status_code, 404)
        res = self.client['registered'].post(
            self.url_projects, simplejson.dumps({
                'slug': 'foo', 'name': 'Foo Project',
            }),
            content_type='application/json'
        )
        self.assertEquals(res.status_code, 201)
        res = self.client['registered'].delete(self.url_project)
        self.assertEquals(res.status_code, 204)
