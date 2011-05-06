# -*- coding: utf-8 -*-
import os
from django.core.urlresolvers import reverse
from django.utils import simplejson
from django.contrib.auth.models import User, Permission
from transifex.resources.models import Resource
from transifex.resources.tests.api.base import APIBaseTests
from transifex.projects.models import Project
from transifex.settings import PROJECT_PATH


class TestResourceAPI(APIBaseTests):

    def setUp(self):
        super(TestResourceAPI, self).setUp()
        self.po_file = os.path.join(self.pofile_path, "pt_BR.po")
        self.url_resources = reverse(
            'apiv2_resources', kwargs={'project_slug': 'project1'}
        )
        self.url_resources_private = reverse(
            'apiv2_resources', kwargs={'project_slug': 'project2'}
        )
        self.url_resource = reverse(
            'apiv2_resource',
            kwargs={'project_slug': 'project1', 'resource_slug': 'resource1'}
        )
        self.url_resource_private = reverse(
            'apiv2_resource',
            kwargs={'project_slug': 'project2', 'resource_slug': 'resource1'}
        )
        self.url_new_project = reverse(
            'apiv2_projects'
        )
        self.url_create_resource = reverse(
            'apiv2_resources', kwargs={'project_slug': 'new_pr'}
        )
        self.url_new_resource = reverse(
            'apiv2_resource',
            kwargs={'project_slug': 'new_pr', 'resource_slug': 'r1', }
        )
        self.url_new_translation = reverse(
            'apiv2_translation',
            kwargs={
                'project_slug': 'new_pr',
                'resource_slug': 'new_r',
                'lang_code': 'el'
            }
        )

    def test_get(self):
        res = self.client['anonymous'].get(self.url_resources)
        self.assertEquals(res.status_code, 401)
        res = self.client['registered'].get(
            reverse(
                'apiv2_resource',
                kwargs={'project_slug': 'not_exists', 'resource_slug': 'resource1'}
            )
        )
        self.assertEquals(res.status_code, 404)
        res = self.client['registered'].get(self.url_resources)
        self.assertEquals(res.status_code, 200)
        self.assertFalse('created' in simplejson.loads(res.content)[0])
        res = self.client['registered'].get(self.url_resources)
        self.assertEquals(res.status_code, 200)
        self.assertEquals(len(simplejson.loads(res.content)), 1)
        self.assertFalse('created' in simplejson.loads(res.content)[0])
        res = self.client['registered'].get(self.url_resources_private)
        self.assertEquals(res.status_code, 401)
        res = self.client['maintainer'].get(self.url_resources_private + "?details")
        self.assertEquals(res.status_code, 501)
        res = self.client['maintainer'].get(self.url_resources_private)
        self.assertEquals(res.status_code, 200)
        self.assertEqual(len(simplejson.loads(res.content)), 1)
        self.assertFalse('created' in simplejson.loads(res.content)[0])
        self.assertTrue('slug' in simplejson.loads(res.content)[0])
        self.assertTrue('name' in simplejson.loads(res.content)[0])
        res = self.client['anonymous'].get(self.url_resource)
        self.assertEquals(res.status_code, 401)
        url_not_exists = self.url_resource[:-1] + "none/"
        res = self.client['registered'].get(url_not_exists)
        self.assertEquals(res.status_code, 404)
        res = self.client['registered'].get(self.url_resource_private)
        self.assertEquals(res.status_code, 401)
        res = self.client['maintainer'].get(self.url_resource_private)
        self.assertEquals(res.status_code, 200)
        res = self.client['maintainer'].get(self.url_resource_private)
        self.assertEquals(res.status_code, 200)
        data = simplejson.loads(res.content)
        self.assertEquals(len(data), 4)
        self.assertTrue('slug' in  data)
        self.assertTrue('name' in data)
        self.assertTrue('source_language', data)
        res = self.client['maintainer'].get(self.url_resource_private + "?details")
        self.assertEquals(res.status_code, 200)
        data = simplejson.loads(res.content)
        self.assertTrue('source_language_code' in data)
        self._create_resource()
        res = self.client['registered'].get(self.url_new_resource)
        self.assertEquals(res.status_code, 200)
        data = simplejson.loads(res.content)
        self.assertTrue('source_language' in data)
        res = self.client['registered'].get(
            self.url_new_resource + "content/"
        )
        self.assertEquals(res.status_code, 200)
        data = simplejson.loads(res.content)
        self.assertTrue('content' in data)
        res = self.client['registered'].get(
            self.url_new_resource + "content/?file"
        )
        self.assertEquals(res.status_code, 200)


    def test_post_errors(self):
        res = self.client['anonymous'].post(
            self.url_resource, content_type='application/json'
        )
        self.assertEquals(res.status_code, 401)
        res = self.client['registered'].post(
            self.url_resource, content_type='application/json'
        )
        self.assertEquals(res.status_code, 403)
        self._create_resource()
        url = reverse(
            'apiv2_resource',
            kwargs={'project_slug': 'new_pr', 'resource_slug': 'new_r'}
        )
        res = self.client['registered'].post(
            url, content_type='application/json'
        )
        self.assertContains(res, "POSTing to this url is not allowed", status_code=400)
        res = self.client['registered'].post(
            self.url_create_resource,
            data=simplejson.dumps({
                    'name': "resource1",
                    'slug': 'r1',
                    'source_language': 'el',
                    'foo': 'foo'
            }),
            content_type='application/json'
        )
        self.assertContains(res, "Field 'foo'", status_code=400)
        res = self.client['registered'].post(
            self.url_create_resource,
            data=simplejson.dumps({
                    'name': "resource1",
                    'slug': 'r1',
                    'source_language': 'el',
                    'mimetype': 'text/x-po',
            }),
            content_type='application/json'
        )
        self.assertContains(res, "same slug exists", status_code=400)
        res = self.client['registered'].post(
            self.url_create_resource,
            data=simplejson.dumps({
                    'name': "resource2",
                    'slug': 'r2',
                    'source_language': 'el',
                    'mimetype': 'text/x-po',
            }),
            content_type='application/json'
        )
        self.assertContains(res, "No content", status_code=400)
        self.assertRaises(
            Resource.DoesNotExist,
            Resource.objects.get,
            slug="r2", project__slug="new_pr"
        )
        res = self.client['registered'].post(
            self.url_create_resource,
            data=simplejson.dumps({
                    'name': "resource2",
                    'slug': 'r2',
                    'source_language': 'el',
            }),
            content_type='application/json'
        )
        self.assertContains(res, "Field 'mimetype'", status_code=400)

    def test_post_files(self):
        self._create_project()
        # send files
        f = open(self.po_file)
        res = self.client['registered'].post(
            self.url_create_resource,
            data={
                'name': "resource1",
                'slug': 'r1',
                'source_language': 'el',
                'name': 'name.po',
                'attachment': f
            },
        )
        f.close()
        r = Resource.objects.get(slug='r1', project__slug='new_pr')
        self.assertEquals(len(r.available_languages_without_teams), 1)

    def test_put(self):
        self._create_resource()
        res = self.client['anonymous'].put(
            self.url_create_resource,
            data=simplejson.dumps({}),
            content_type='application/json'
        )
        self.assertEquals(res.status_code, 401)
        res = self.client['registered'].put(
            self.url_create_resource,
            data=simplejson.dumps({}),
            content_type='application/json'
        )
        self.assertContains(res, "No resource", status_code=400)
        url = reverse(
            'apiv2_resource',
            kwargs={'project_slug': 'new_pr_not', 'resource_slug': 'r1'}
        )
        res = self.client['registered'].put(
            url, data=simplejson.dumps({}),
            content_type='application/json'
        )
        self.assertEquals(res.status_code, 404)
        url = reverse(
            'apiv2_resource',
            kwargs={'project_slug': 'new_pr', 'resource_slug': 'r1'}
        )
        res = self.client['registered'].put(
            url, data=simplejson.dumps({}),
            content_type='application/json'
        )
        self.assertContains(res, "Empty request", status_code=400)
        url = reverse(
            'apiv2_resource',
            kwargs={'project_slug': 'new_pr', 'resource_slug': 'r1'}
        )
        res = self.client['registered'].put(
            url,
            data=simplejson.dumps({
                    'source_language': "el_NN",
            }),
            content_type='application/json'
        )
        self.assertEquals(res.status_code, 400)
        res = self.client['registered'].put(
            url,
            data=simplejson.dumps({
                    'source_language': "el",
            }),
            content_type='application/json'
        )
        self.assertEquals(res.status_code, 200)
        res = self.client['registered'].put(
            url,
            data=simplejson.dumps({
                    'mimetype': "text/x-po",
            }),
            content_type='application/json'
        )
        self.assertEquals(res.status_code, 200)
        res = self.client['registered'].put(
            url,
            data=simplejson.dumps({
                    'source_language': "el",
                    'foo': 'foo',
            }),
            content_type='application/json'
        )
        self.assertContains(res,"Field 'foo'", status_code=400)

    def test_delete(self):
        res = self.client['anonymous'].delete(self.url_resource)
        self.assertEquals(res.status_code, 401)
        res = self.client['registered'].delete(self.url_resource)
        self.assertEquals(res.status_code, 403)
        self._create_resource()
        url = reverse(
            'apiv2_resource',
            kwargs={'project_slug': 'new_pr', 'resource_slug': 'r1'}
        )
        res = self.client['registered'].delete(url)
        self.assertEquals(res.status_code, 204)

    def _create_project(self):
        res = self.client['registered'].post(
            self.url_new_project,
            data=simplejson.dumps({
                    'slug': 'new_pr', 'name': 'Project from API',
                    'maintainers': 'registered',
            }),
            content_type='application/json'
        )
        self.assertEquals(res.status_code, 201)

    def _create_resource(self):
        self._create_project()
        with open(self.po_file) as f:
            content = f.read()
        res = self.client['registered'].post(
            self.url_create_resource,
            data=simplejson.dumps({
                    'name': "resource1",
                    'slug': 'r1',
                    'source_language': 'el',
                    'mimetype': 'text/x-po',
                    'content': content,
            }),
            content_type='application/json'
        )
        self.assertEquals(res.status_code, 201)
        r = Resource.objects.get(slug='r1', project__slug='new_pr')
        self.assertEquals(len(r.available_languages_without_teams), 1)


class TestTranslationAPI(APIBaseTests):

    def setUp(self):
        super(TestTranslationAPI, self).setUp()
        self.po_file = os.path.join(self.pofile_path, "pt_BR.po")
        self.url_resources = reverse(
            'apiv2_resources', kwargs={'project_slug': 'project1'}
        )
        self.url_resources_private = reverse(
            'apiv2_resources', kwargs={'project_slug': 'project2'}
        )
        self.url_resource = reverse(
            'apiv2_resource',
            kwargs={'project_slug': 'project1', 'resource_slug': 'resource1'}
        )
        self.url_resource_private = reverse(
            'apiv2_resource',
            kwargs={'project_slug': 'project2', 'resource_slug': 'resource1'}
        )
        self.url_new_project = reverse(
            'apiv2_projects'
        )
        self.url_create_resource = reverse(
            'apiv2_resources', kwargs={'project_slug': 'new_pr'}
        )
        self.url_new_resource = reverse(
            'apiv2_resource',
            kwargs={'project_slug': 'new_pr', 'resource_slug': 'r1', }
        )
        self.url_new_translation = reverse(
            'apiv2_translation',
            kwargs={
                'project_slug': 'new_pr',
                'resource_slug': 'new_r',
                'lang_code': 'el'
            }
        )

    def test_get_translation(self):
        res = self.client['anonymous'].get(self.url_new_translation)
        self.assertEquals(res.status_code, 401)
        res = self.client['registered'].get(
            reverse(
                'apiv2_translation',
                kwargs={
                    'project_slug': 'project1',
                    'resource_slug': 'resource-not',
                    'lang_code': 'en_US',
                }
            )
        )
        self.assertEquals(res.status_code, 404)
        res = self.client['registered'].get(
            reverse(
                'apiv2_translation',
                kwargs={
                    'project_slug': 'project1',
                    'resource_slug': 'resource1',
                    'lang_code': 'en_US',
                }
            )
        )
        self.assertEquals(len(simplejson.loads(res.content)), 2)
        self.assertEquals(res.status_code, 200)
        url = "".join([
                reverse(
                    'apiv2_translation',
                    kwargs={
                        'project_slug': 'project1',
                        'resource_slug': 'resource1',
                            'lang_code': 'en_US',
                    }),
                "?file"
        ])
        res = self.client['registered'].get(url)
        self.assertEquals(res.status_code, 200)

    def test_put_translations(self):
        self._create_resource()
        # test strings
        res = self.client['registered'].post(
            reverse(
                'apiv2_translation',
                kwargs={
                    'project_slug': 'new_pr',
                    'resource_slug': 'r1',
                    'lang_code': 'el_GR',
                }
            )
        )
        self.assertEquals(res.status_code, 405)
        res = self.client['registered'].put(
            reverse(
                'apiv2_translation',
                kwargs={
                    'project_slug': 'new_pr',
                    'resource_slug': 'r1',
                    'lang_code': 'el_GR',
                }
            )
        )
        self.assertContains(res, "No file", status_code=400)
        with open(self.po_file) as f:
            content = f.read()
        res = self.client['registered'].put(
            reverse(
                'apiv2_translation',
                kwargs={
                    'project_slug': 'new_pr_not',
                    'resource_slug': 'r1',
                    'lang_code': 'el',
                }
            ),
            data=simplejson.dumps([{
                    'content': content,
            }]),
            content_type='application/json'
        )
        self.assertEquals(res.status_code, 404)
        r = Resource.objects.get(slug="r1", project__slug="new_pr")
        self.assertEquals(len(r.available_languages_without_teams), 1)
        res = self.client['registered'].put(
            reverse(
                'apiv2_translation',
                kwargs={
                    'project_slug': 'new_pr',
                    'resource_slug': 'r1',
                    'lang_code': 'el',
                }
            ),
            data=simplejson.dumps({
                    'content': content,
            }),
            content_type='application/json'
        )
        self.assertEquals(res.status_code, 200)
        self.assertEquals(len(r.available_languages_without_teams), 1)
        res = self.client['registered'].put(
            reverse(
                'apiv2_translation',
                kwargs={
                    'project_slug': 'new_pr',
                    'resource_slug': 'r1',
                    'lang_code': 'enb'
                }
            ),
            data=simplejson.dumps({
                    'content': content,
            }),
            content_type='application/json'
        )
        self.assertContains(res, "language code", status_code=400)

        # test files
        res = self.client['registered'].put(
            reverse(
                'apiv2_translation',
                kwargs={
                    'project_slug': 'new_pr',
                    'resource_slug': 'r1',
                    'lang_code': 'fi'
                }
            ),
            data={},
        )
        self.assertContains(res, "No file", status_code=400)
        f = open(self.po_file)
        res = self.client['registered'].put(
            reverse(
                'apiv2_translation',
                kwargs={
                    'project_slug': 'new_pr',
                    'resource_slug': 'r1',
                    'lang_code': 'fi'
                }
            ),
            data={
                'name': 'name.po',
                'attachment': f
            },
        )
        f.close()
        self.assertEquals(res.status_code, 200)
        self.assertEquals(len(r.available_languages_without_teams), 2)

        res = self.client['anonymous'].post(self.url_new_translation)
        self.assertEquals(res.status_code, 401)

        f = open(self.po_file)
        res = self.client['registered'].put(
            reverse(
                'apiv2_translation',
                kwargs={
                    'project_slug': 'new_pr',
                    'resource_slug': 'r1',
                    'lang_code': 'el',
                }
            ),
            data={
                'name': 'name.po',
                'attachment': f
            },
        )
        f.close()
        self.assertEquals(res.status_code, 200)

    def _create_project(self):
        res = self.client['registered'].post(
            self.url_new_project,
            data=simplejson.dumps({
                    'slug': 'new_pr', 'name': 'Project from API',
                    'maintainers': 'registered',
            }),
            content_type='application/json'
        )
        self.assertEquals(res.status_code, 201)

    def _create_resource(self):
        self._create_project()
        with open(self.po_file) as f:
            content = f.read()
        res = self.client['registered'].post(
            self.url_create_resource,
            data=simplejson.dumps({
                    'name': "resource1",
                    'slug': 'r1',
                    'source_language': 'el',
                    'mimetype': 'text/x-po',
                    'content': content,
            }),
            content_type='application/json'
        )
        self.assertEquals(res.status_code, 201)
        r = Resource.objects.get(slug='r1', project__slug='new_pr')
        self.assertEquals(len(r.available_languages_without_teams), 1)
