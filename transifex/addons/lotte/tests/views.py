# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.db.models.loading import get_model
from django.utils import simplejson as json
from transifex.txcommon.tests.base import BaseTestCase
from utils import *


Translation = get_model('resources', 'Translation')


class LotteViewsTests(BaseTestCase):

    def setUp(self):
        super(LotteViewsTests, self).setUp()
        self.entity = self.resource.entities[0]

        self.DataTable_params = default_params()

        # Set some custom translation data
        # Source strings
        self.source_string_plural1 = self.source_entity_plural.translations.create(
            string="SourceArabicTrans1",
            language=self.language_en,
            user=self.user["maintainer"], rule=1)
        self.source_string_plural2 = self.source_entity_plural.translations.create(
            string="SourceArabicTrans2",
            language=self.language_en,
            user=self.user["maintainer"], rule=5)
        # Translation strings
        self.source_entity_plural.translations.create(
            string="ArabicTrans0", language=self.language_ar,
            user=self.user["maintainer"], rule=0)
        self.source_entity_plural.translations.create(
            string="ArabicTrans1", language=self.language_ar,
            user=self.user["maintainer"], rule=1)
        self.source_entity_plural.translations.create(
            string="ArabicTrans2", language=self.language_ar,
            user=self.user["maintainer"], rule=2)
        self.source_entity_plural.translations.create(
            string="ArabicTrans3", language=self.language_ar,
            user=self.user["maintainer"], rule=3)
        self.source_entity_plural.translations.create(
            string="ArabicTrans4", language=self.language_ar,
            user=self.user["maintainer"], rule=4)
        self.source_entity_plural.translations.create(
            string="ArabicTrans5", language=self.language_ar,
            user=self.user["maintainer"], rule=5)

        # URLs
        self.snippet_url = reverse('translation_details_snippet',
            args=[self.entity.id, self.language.code])
        self.translate_view_url = reverse('translate_resource',
            args=[self.project.slug, self.resource.slug, self.language.code])
        self.translate_content_arabic_url = reverse('stringset_handling',
            args=[self.project.slug, self.resource.slug, self.language_ar.code])
        self.push_translation = reverse('push_translation',
            args=[self.project.slug, self.language_ar.code])

    def tearDown(self):
        super(LotteViewsTests, self).tearDown()
        self.source_entity_plural.translations.all().delete()

    def test_snippet_entities_data(self):
        """Test the entity details part of the snippet is correct."""
        # Create custom fields in entity
        self.entity.string = "Key1"
        self.entity.context = "Description1"
        self.entity.occurrences = "Occurrences1"
        self.entity.developer_comment = "Comment1"
        self.entity.save()
        # Test the response contents
        resp = self.client['team_member'].get(self.snippet_url)
        self.assertContains(resp, self.entity.string, status_code=200)
        self.assertContains(resp, self.entity.context)
        self.assertContains(resp, self.entity.occurrences)
        self.assertContains(resp, self.entity.developer_comment)
        self.assertTemplateUsed(resp, 'lotte_details_snippet.html')

    def test_snippet_translation_data(self):
        """Test the translation details part of the snippet is correct."""
        # Set some custom data
        self.entity.translations.create(string="StringTrans1",
            language=self.language, user=self.user["team_member"])
        # Test the response contents
        resp = self.client['team_member'].get(self.snippet_url)
        self.assertContains(resp, '0 minutes', status_code=200)

    def test_translate_view(self):
        """Test the basic response of the main view for lotte."""
        # Check page status
        resp = self.client['maintainer'].get(self.translate_view_url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'translate.html')

    def test_plural_data(self):
        """Test that all plural fields are sent."""

        self.assertEqual(Translation.objects.filter(
            source_entity=self.source_entity_plural,
            language=self.language_en).count(), 2)

        self.assertEqual(Translation.objects.filter(
            source_entity=self.source_entity_plural,
            language=self.language_ar).count(), 6)

        resp = self.client['maintainer'].post(
            self.translate_content_arabic_url, self.DataTable_params)
        self.assertContains(resp, 'ArabicTrans1', status_code=200)
        self.assertContains(resp, 'ArabicTrans2')
        self.assertContains(resp, 'ArabicTrans3')
        self.assertContains(resp, 'ArabicTrans4')

    def test_push_plural_translation(self):
        """Test pushing pluralized translations."""
        data1 = {"strings":[{"id":self.source_string_plural1.id,
                            "translations":{
                                "zero":"ArabicTrans0",
                                "one":"ArabicTrans1",
                                "few":"ArabicTrans3",
                                "other":"ArabicTrans5",}
                           },]
               }
        data2 = {"strings":[{"id":self.source_string_plural1.id,
                            "translations":{
                                "zero":"ArabicTrans0_1",
                                "one":"ArabicTrans1_1",
                                "two":"ArabicTrans2_1",
                                "few":"ArabicTrans3_1",
                                "many":"ArabicTrans4_1",}
                           },]
               }
        data3 = {"strings":[{"id":self.source_string_plural1.id,
                            "translations":{
                                "zero":"ArabicTrans0_1",
                                "one":"ArabicTrans1_1",
                                "two":"ArabicTrans2_1",
                                "few":"ArabicTrans3_1",
                                "many":"ArabicTrans4_1",
                                "other":"ArabicTrans5_1",}
                           },]
               }
        data4 = {"strings":[{"id":self.source_string_plural1.id,
                            "translations":{
                                "zero":"",
                                "one":"",
                                "two":"",
                                "few":"",
                                "many":"",
                                "other":"",}
                           },]
               }
        resp1 = self.client['maintainer'].post(self.push_translation,
            json.dumps(data1), content_type='application/json')
        self.assertContains(resp1,
            'Cannot save unless plural translations are either', status_code=200)

        resp2 = self.client['maintainer'].post(self.push_translation,
            json.dumps(data2), content_type='application/json')
        self.assertContains(resp2,
            'Cannot save unless plural translations are either', status_code=200)

        resp3 = self.client['maintainer'].post(self.push_translation,
            json.dumps(data3), content_type='application/json')
        self.assertEqual(resp3.status_code, 200)

        self.assertEqual(Translation.objects.filter(
            source_entity=self.source_entity_plural,
            language=self.language_ar).count(), 6)

        resp4 = self.client['maintainer'].post(self.push_translation,
            json.dumps(data4), content_type='application/json')
        self.assertEqual(resp4.status_code, 200)

        self.assertEqual(Translation.objects.filter(
            source_entity=self.source_entity_plural,
            language=self.language_ar).count(), 0)

        # We push again the data to return to the setup state.
        resp5 = self.client['maintainer'].post(self.push_translation,
            json.dumps(data3), content_type='application/json')
        self.assertEqual(resp3.status_code, 200)
        self.assertEqual(Translation.objects.filter(
            source_entity=self.source_entity_plural,
            language=self.language_ar).count(), 6)

    def test_dt_search_string(self):
        """Test the Datatable's search."""
        self.DataTable_params["sSearch"] = "ArabicTrans"
        resp = self.client['maintainer'].post(
            self.translate_content_arabic_url, self.DataTable_params)
        self.assertContains(resp, 'ArabicTrans', status_code=200)
        self.DataTable_params["sSearch"] = "Empty result"
        resp = self.client['maintainer'].post(
            self.translate_content_arabic_url, self.DataTable_params)
        self.assertNotContains(resp, 'ArabicTrans', status_code=200)

    def test_dt_pagination(self):
        """Test the Datatable's pagination mechanism."""
        self.DataTable_params["iDisplayStart"] = 0
        resp = self.client['maintainer'].post(
            self.translate_content_arabic_url, self.DataTable_params)
        self.assertContains(resp, 'ArabicTrans', status_code=200)

    def test_dt_show_num_entries(self):
        """Test the Datatable's show num entries mechanism."""
        self.DataTable_params["iDisplayLength"] = 20
        resp = self.client['maintainer'].post(
            self.translate_content_arabic_url, self.DataTable_params)
        self.assertContains(resp, 'ArabicTrans', status_code=200)

    def test_filters(self):
        """Test lotte filters one by one."""
        pass
