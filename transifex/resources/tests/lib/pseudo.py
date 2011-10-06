# -*- coding: utf-8 -*-
import os
from django.conf import settings
from django.core.urlresolvers import reverse
from transifex.resources.formats import get_i18n_handler_from_type
from transifex.resources.models import Resource
from transifex.languages.models import Language
from transifex.txcommon import import_to_python
from transifex.txcommon.tests import base


FORMATS = {
    'PO':{
        'file': os.path.join(settings.TX_ROOT, 
            'resources/tests/lib/pofile/pseudo.pot'),
        'pseudo_messages':{
            'XXX': [u'msgstr "xxxLocationsxxx"'],
            'BRACKETS': [u'msgstr "[Locations]"'],
            'UNICODE': [u'"Ŭşḗř %(name)s <b>ḓǿḗş ƞǿŧ</b> ħȧṽḗ ȧ',
                u'%i ḿǿŧǿřƈẏƈŀḗş ȧŧ:\\n'],
            'PLANGUAGE': [u'"ÜקÜséקér %(name)s <b>dôéקôés nôקôt</b>', 
                u'%i môקôtôקôrcýקýcléקés åקåt:\\n'],
            'MIXED': [u'[Ŀôקôƈåקåŧïôקïôƞş]',
                u'%i ḿôקôŧôקôřƈýקýƈŀéקéş åקåŧ:\\n']
            }

        },
    'QT':{
        'file': os.path.join(settings.TX_ROOT, 
            'resources/tests/lib/qt/pseudo.ts'),
        'pseudo_messages':{
            'XXX': [u'<translation>xxxSTARTxxx</translation>'],
            'BRACKETS': [u'<translation>[START]</translation>'],
            'UNICODE': [u'<numerusform>&lt;b&gt;%n ƒīŀḗ.&lt;/b&gt;</numerusform>'],
            'PLANGUAGE': [u'<numerusform>&lt;b&gt;%n fïקïléקé'],
            'MIXED': [u'<translation>[ŞŦÅקÅŘŦ]</translation>',
                u'ŧħïקïş şýקýşŧéקéḿ&lt;/b&gt;]']
            }
        },
    'PROPERTIES':{
        'file': os.path.join(settings.TX_ROOT, 
            'resources/tests/lib/javaproperties/pseudo.properties'),
        'pseudo_messages':{
            'XXX': [u'Key00=xxxValue00xxx'],
            'BRACKETS': [u'Key00=[Value00]'],
            'UNICODE': [u'Key01=<b>Ƥȧɠḗ</b> %s ǿƒ %s'],
            'PLANGUAGE': [u'Key01=<b>Påקågéקé</b> %s ôקôf %s'],
            'MIXED': [u'Key00=[Ṽåקåŀüéקüé00]']
            }
        },
    'INI':{
        'file': os.path.join(settings.TX_ROOT, 
            'resources/tests/lib/joomla_ini/pseudo.ini'),
        'pseudo_messages':{
            'XXX': [u'KEY1="xxxTranslationxxx"'],
            'BRACKETS': [u'KEY1="[Translation]"'],
            'UNICODE': [u'KEY2="<b>Ƥȧɠḗ</b> %s ǿƒ %s"'],
            'PLANGUAGE': [u'KEY2="<b>Påקågéקé</b> %s ôקôf %s"'],
            'MIXED': [u'KEY2="[<b>Ƥåקåɠéקé</b> %s ôקôƒ %s]"']
            }
        },

    # FIXME: Waiting for fixes in the format.
    #'DESKTOP':{
        #'file': os.path.join(settings.TX_ROOT, 
            #'resources/tests/lib/desktop/data/okular.desktop'),
        #'pseudo_messages':{
            #'XXX': [u''],
            #'BRACKETS': [u''],
            #'UNICODE': [u''],
            #'PLANGUAGE': [u'']
            #}
        #}
    }


class PseudoTestCase(base.BaseTestCase):
    """
    Test the generation of several Pseudo translation file types for different
    i18n formats.
    """

    def test_pseudo_file(self):
        """Test Pseudo translation generation based on FORMATS var dict."""
        for i18n_type, v in FORMATS.items():
            
            #if i18n_type != "INI": continue

            # Set i18n_type for resource
            self.resource.i18n_type = i18n_type
            self.resource.save()

            # Set a file, resource and language for the resource
            parser = get_i18n_handler_from_type(i18n_type)
            handler = parser(v['file'], resource=self.resource,
                language=self.language)
            handler.parse_file(is_source=True)
            handler.save2db(is_source=True)

            # For each pseudo type that exists, try to generate files in the
            # supported i18n formats supported.
            for pseudo_type in settings.PSEUDO_TYPES.keys():
                
                #if pseudo_type != "MIXED": continue

                # Get Pseudo type class
                pseudo_class = import_to_python(
                    settings.PSEUDO_TYPE_CLASSES[pseudo_type])

                # Create a PseudoType instance and set it into the handler
                handler.bind_pseudo_type(pseudo_class(self.resource.i18n_type))

                # Compile file and check encoding
                handler.compile()
                file_content = handler.compiled_template
                if type(file_content) != unicode:
                    file_content = file_content.decode('utf-8')

                #FIXME: We have a bug related to spaces being escaped in 
                # .properties files. This can be dropped after fixing it.
                if i18n_type == 'PROPERTIES' and \
                    pseudo_type in ['PLANGUAGE', 'UNICODE']:
                    file_content = file_content.replace('\\ ', ' ')

                # Assert expected value in the generated file
                for message in v['pseudo_messages'][pseudo_type]:
                    print file_content
                    print "-----------------"
                    print message
                    print i18n_type
                    print pseudo_type
                    print "-----------------"
                    self.assertTrue(message in file_content)


    def test_pseudo_file_api_calls(self):
        """Test Pseudo translation requests through the API."""
        source_language = self.project.resources.all()[0].source_language
        for i18n_type, v in FORMATS.items():
            resource_slug = 'resource_%s' % i18n_type.lower()
            resource_url = reverse('apiv2_resources', kwargs={
                    'project_slug': self.project.slug})

            # Creating resource using the API
            f = open(v['file'])
            res = self.client['maintainer'].post(
                resource_url,
                data={
                    'slug': resource_slug,
                    'source_language': source_language.code,
                    'name': resource_slug,
                    'mimetype': settings.I18N_METHODS[i18n_type]['mimetype'],
                    'attachment': f},
                )
            f.close()
            
            print '-----------------------'
            print i18n_type
            print settings.I18N_METHODS[i18n_type]['mimetype']
            print res.content
            print '-----------------------'

            # Pseudo file API URL
            url = reverse('apiv2_pseudo_content', args=[self.project.slug, 
                resource_slug])
            
            for pseudo_type in settings.PSEUDO_TYPES:
                # Get resource file using a specific pseudo type
                resp = self.client['registered'].get(url, 
                    data={'pseudo_type':pseudo_type})

                # Get response and check encoding
                resp_content = eval(resp.content)['content']
                if type(resp_content) != unicode:
                    resp_content = resp_content.decode('utf-8')

                #FIXME: We have a bug related to spaces being escaped in 
                # .properties files. This can be dropped after fixing it.
                if i18n_type == 'PROPERTIES' and \
                    pseudo_type in ['PLANGUAGE', 'UNICODE']:
                    resp_content = resp_content.replace('\\ ', ' ')

                # Assert expected value in the generated file
                for message in v['pseudo_messages'][pseudo_type]:
                    self.assertTrue(message in resp_content)
