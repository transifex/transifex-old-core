# -*- coding: utf-8 -*-
import unittest
from django.core import management
from django.core.urlresolvers import reverse
from django.conf import settings
from django.test.client import Client
from django.contrib.contenttypes.models import ContentType        
from projects.models import Project, Component
from translations.models import POFile
from languages.models import Language

# Languages that should exist on Tx for sure
LANG_CODES = [ 'es', 'fr', 'de', 'el', 'sv', 'pt', 
    'ru', 'ar', 'da', 'hu', 'it', 'is', 'lv', 'lt', 'fi', 'et']

JSON_RESPONSE = "google.visualization.Query.setResponse({'version':'0.6', 're\
qId':'0', 'status':'OK', 'table': {cols:[{id:'lang',label:'Language',type:'st\
ring'},{id:'trans',label:'Translated',type:'number'},{id:'fuzzy',label:'Fuzzy\
',type:'number'}],rows:[{c:[{v:'Estonian (et)'},{v:82},{v:8}]},{c:[{v:'Latvia\
n (lv)'},{v:81},{v:9}]},{c:[{v:'Lithuanian (lt)'},{v:81},{v:9}]},{c:[{v:'Finn\
ish (fi)'},{v:81},{v:9}]},{c:[{v:'Italian (it)'},{v:80},{v:9}]},{c:[{v:'Icela\
ndic (is)'},{v:80},{v:9}]},{c:[{v:'Hungarian (hu)'},{v:80},{v:10}]},{c:[{v:'D\
anish (da)'},{v:79},{v:10}]},{c:[{v:'Arabic (ar)'},{v:79},{v:10}]},{c:[{v:'Ru\
ssian (ru)'},{v:78},{v:10}]},{c:[{v:'Portuguese (pt)'},{v:78},{v:10}]},{c:[{v\
:'Swedish (sv)'},{v:77},{v:11}]},{c:[{v:'Greek (el)'},{v:77},{v:11}]},{c:[{v:\
'French (fr)'},{v:76},{v:11}]}]}});"

REDIRECT_URL = "http://chart.apis.google.com/chart?cht=bhs&chs=350x196&chd=e:\
0ez1z1z1zMzMzMyjyjx6x6xRxRwo,FIFxFxFxFxFxGaGaGaGaGaHCHCHC&chco=78dc7d,dae1ee,\
efefef&chxt=y,r&chxl=0:%7CFrench%20%28fr%29%7CGreek%20%28el%29%7CSwedish%20%2\
8sv%29%7CPortuguese%20%28pt%29%7CRussian%20%28ru%29%7CArabic%20%28ar%29%7CDan\
ish%20%28da%29%7CHungarian%20%28hu%29%7CIcelandic%20%28is%29%7CItalian%20%28i\
t%29%7CFinnish%20%28fi%29%7CLithuanian%20%28lt%29%7CLatvian%20%28lv%29%7CEsto\
nian%20%28et%29%7C1:%7C76%25%7C77%25%7C77%25%7C78%25%7C78%25%7C79%25%7C79%25%\
7C80%25%7C80%25%7C80%25%7C81%25%7C81%25%7C81%25%7C82%25&chbh=9"

class TestCharts(unittest.TestCase):
    def setUp(self):
        management.call_command('txlanguages')

    def test_main(self):
        """
        Test charts
        """
        project, created = Project.objects.get_or_create(slug="foo", 
            name="Foo")
        component, created = Component.objects.get_or_create(slug="default", 
           name="Default", project=project)
        ctype = ContentType.objects.get_for_model(component)
        i = 1
        for lang_code in LANG_CODES:
            pofile, created = POFile.objects.get_or_create(
                object_id=component.id,
                content_type=ctype, 
                filename="test-file-%i-%s" % (i, lang_code),
                is_pot=False)
            pofile.language= Language.objects.by_code_or_alias(code=lang_code)
            pofile.language_code = lang_code
            pofile.set_stats(trans=i+30, fuzzy=5, untrans=5)
            pofile.save()
            i += 1

        c = Client()

        # Check where it redirects to
        resp = c.get(reverse('chart_comp_image', args = [project.slug,
            component.slug]), follow=True)
        hops = resp.redirect_chain
        url, code = hops[0]
        self.assertEqual(url, REDIRECT_URL)

        # Check JSON output
        c = Client()
        resp = c.get(reverse('chart_comp_json', args = [project.slug,
            component.slug]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, JSON_RESPONSE)

        # Check whether image.png URL redirects
        resp = c.get(reverse('chart_comp_image', args = [project.slug,
            component.slug]))
        self.assertEqual(resp.status_code, 302)

