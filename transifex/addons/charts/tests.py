# -*- coding: utf-8 -*-
import unittest
from django.core import management
from django.core.urlresolvers import reverse
from django.conf import settings
from django.test.client import Client
from django.contrib.contenttypes.models import ContentType        
from transifex.languages.models import Language
from transifex.projects.models import Project
from transifex.txcommon.tests.base import BaseTestCase


JSON_RESPONSE = "google.visualization.Query.setResponse({'version':'0.6', 'reqId':'0', 'status':'OK', 'table': {cols:[{id:'lang',label:'Language',type:'string'},{id:'trans',label:'Translated',type:'number'}],rows:[]}});"

REDIRECT_URL = "http://chart.apis.google.com/chart?cht=bhs&chs=350x14&chd=s:&chco=78dc7d,dae1ee,efefef&chxt=y,r&chxl=0:%7C%7C1:%7C&chbh=9"

class TestCharts(BaseTestCase):

    def test_img(self):
        resp = self.client['anonymous'].get(reverse('chart_resource_image',
            args=[self.project.slug, self.resource.slug]), follow=True)
        hops = resp.redirect_chain
        url, code = hops[0]
        self.assertEqual(url, REDIRECT_URL)

    def test_json(self):
        # Check JSON output
        resp = self.client['anonymous'].get(reverse('chart_resource_json',
            args=[self.project.slug, self.resource.slug]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, JSON_RESPONSE)

    def test_img_redirect(self):
        # Check whether image.png URL redirects
        resp = self.client['anonymous'].get(reverse('chart_resource_image',
            args=[self.project.slug, self.resource.slug]))
        self.assertEqual(resp.status_code, 302)

