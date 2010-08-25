from django.core.urlresolvers import reverse
from resources.tests.views.base import ViewsBaseTest

class LotteViewsTests(ViewsBaseTest):

    def setUp(self):
        super(LotteViewsTests, self).setUp()
        self.entity = self.resource.entities[0]
        self.snippet_url = reverse('translation_details_snippet',
            args=[self.entity.id, self.language.code])

            
    def test_snippet_entities_data(self):
        """Test the entity details part of the snippet is correct."""
        # Create custom fields in entity
        self.entity.string = "Key1"
        self.entity.context = "Description1"
        self.entity.occurrences = "Occurrences1"
        self.entity.save()
        # Test the response contents
        resp = self.client['team_member'].get(self.snippet_url)
        self.assertContains(resp, self.entity.string, status_code=200)
        self.assertContains(resp, self.entity.context)
        self.assertContains(resp, self.entity.occurrences)
        self.assertTemplateUsed(resp, 'lotte_details_snippet.html')


    def test_snippet_translation_data(self):
        """Test the translation details part of the snippet is correct."""
        # Set some custom data
        self.entity.translations.create(resource=self.resource, string="StringTrans1",
            language=self.language, user=self.user["team_member"])
        # Test the response contents
        resp = self.client['team_member'].get(self.snippet_url)
        self.assertContains(resp, '0 minutes', status_code=200)
        self.assertContains(resp, 'alt="team_member"')


    def test_translate_view(self):
        """Test the basic response of the main view for lotte."""
        # Check page status
        url = reverse('translate_resource',
            args=[self.project.slug, self.resource.slug, self.language.code])
        resp = self.client['maintainer'].get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'translate.html')

