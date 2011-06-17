# -*- coding: utf-8 -*-

from transifex.txcommon.tests.base import BaseTestCase
from transifex.resources.formats.registry import _FormatsRegistry

class TestRegistry(BaseTestCase):

    def setUp(self):
        super(TestRegistry, self).setUp()
        methods = {
            'PO': {
                'description': 'PO file handler',
                'file-extensions': '.po, .pot',
                'mimetype': 'text/x-po, application/x-gettext, application/x-po',
            }, 'QT': {
                    'description': 'Qt Files',
                    'mimetype': 'application/xml',
                    'file-extensions': '.ts'
            },
        }
        handlers = {
            'PO': 'resources.formats.pofile.POHandler',
            'QT': 'resources.formats.qt.LinguistHandler',
        }
        self.registry = _FormatsRegistry(methods=methods, handlers=handlers)

    def test_register(self):
        from transifex.resources.formats.joomla import JoomlaINIHandler
        self.registry.add_handler('INI', JoomlaINIHandler)
        self.assertEquals(len(self.registry.handlers.keys()), 3)
        self.assertIn('INI', self.registry.handlers.keys())
        j = self.registry.handler_for('INI')
        self.assertIsInstance(j, JoomlaINIHandler)

    def test_extensions(self):
        extensions = self.registry.extensions_for('PO')
        self.assertEquals(len(extensions), 2)
        self.assertEquals(extensions[0], '.po')
        self.assertEquals(extensions[1], '.pot')

    def test_mimetypes(self):
        mimetypes = self.registry.mimetypes_for('PO')
        self.assertEquals(len(mimetypes), 3)
        self.assertEquals(mimetypes[0], 'text/x-po')
        self.assertEquals(mimetypes[1], 'application/x-gettext')
        self.assertEquals(mimetypes[2], 'application/x-po')
