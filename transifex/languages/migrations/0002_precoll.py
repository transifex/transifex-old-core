
from south.db import db
from django.db import models
from languages.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Changing field 'Language.code_aliases'
        # (to signature: django.db.models.fields.CharField(max_length=100, null=True))
        db.alter_column('translations_language', 'code_aliases', orm['languages.language:code_aliases'])
        
        # Changing field 'Language.code'
        # (to signature: django.db.models.fields.CharField(unique=True, max_length=50))
        db.alter_column('translations_language', 'code', orm['languages.language:code'])
        
        # Changing field 'Language.description'
        # (to signature: django.db.models.fields.CharField(max_length=255, blank=True))
        db.alter_column('translations_language', 'description', orm['languages.language:description'])
        
        # Changing field 'Language.pluralequation'
        # (to signature: django.db.models.fields.CharField(max_length=255, blank=True))
        db.alter_column('translations_language', 'pluralequation', orm['languages.language:pluralequation'])
        
        # Changing field 'Language.name'
        # (to signature: django.db.models.fields.CharField(unique=True, max_length=50))
        db.alter_column('translations_language', 'name', orm['languages.language:name'])
        
        # Changing field 'Language.specialchars'
        # (to signature: django.db.models.fields.CharField(max_length=255, blank=True))
        db.alter_column('translations_language', 'specialchars', orm['languages.language:specialchars'])
        
        # Changing field 'Language.nplurals'
        # (to signature: django.db.models.fields.SmallIntegerField())
        db.alter_column('translations_language', 'nplurals', orm['languages.language:nplurals'])
        
    
    
    def backwards(self, orm):
        
        # Changing field 'Language.code_aliases'
        # (to signature: models.CharField(_('Code aliases'), max_length=100, null=True))
        db.alter_column('translations_language', 'code_aliases', orm['languages.language:code_aliases'])
        
        # Changing field 'Language.code'
        # (to signature: models.CharField(_('Code'), unique=True, max_length=50))
        db.alter_column('translations_language', 'code', orm['languages.language:code'])
        
        # Changing field 'Language.description'
        # (to signature: models.CharField(_('Description'), max_length=255, blank=True))
        db.alter_column('translations_language', 'description', orm['languages.language:description'])
        
        # Changing field 'Language.pluralequation'
        # (to signature: models.CharField(_("Plural Equation"), max_length=255, blank=True))
        db.alter_column('translations_language', 'pluralequation', orm['languages.language:pluralequation'])
        
        # Changing field 'Language.name'
        # (to signature: models.CharField(_('Name'), unique=True, max_length=50))
        db.alter_column('translations_language', 'name', orm['languages.language:name'])
        
        # Changing field 'Language.specialchars'
        # (to signature: models.CharField(_("Special Chars"), max_length=255, blank=True))
        db.alter_column('translations_language', 'specialchars', orm['languages.language:specialchars'])
        
        # Changing field 'Language.nplurals'
        # (to signature: models.SmallIntegerField(_("Number of Plurals")))
        db.alter_column('translations_language', 'nplurals', orm['languages.language:nplurals'])
        
    
    
    models = {
        'languages.language': {
            'Meta': {'db_table': "'translations_language'"},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'code_aliases': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100', 'null': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'nplurals': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'pluralequation': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'specialchars': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        }
    }
    
    complete_apps = ['languages']
