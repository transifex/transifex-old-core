# -*- coding: utf-8 -*-

from south.db import db
from django.db import models
from translations.models import *

class Migration:
    
    def forwards(self, orm):
        db.delete_table('translations_pofile_lock')    
    
    def backwards(self, orm):
        # Adding model 'POFileLock'
        db.create_table('translations_pofile_lock', (
            ('name', models.CharField(max_length=255, null=True)),
            ('created', models.DateTimeField(auto_now_add=True, editable=False)),
            ('enabled', models.BooleanField(default=True)),
            ('modified', models.DateTimeField(auto_now=True, editable=False)),
            ('pofile', models.ForeignKey(orm.POFile, related_name='locks', null=True)),
            ('owner', models.ForeignKey(orm['auth.User'])),
            ('id', models.AutoField(primary_key=True)),
        ))
        db.send_create_signal('translations', ['POFileLock'])    
    
    models = {
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
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
        },
        'translations.pofile': {
            'Meta': {'unique_together': "(('content_type', 'object_id', 'filename'),)"},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'error': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'fuzzy': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'fuzzy_perc': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_msgmerged': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_pot': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['languages.Language']", 'null': 'True'}),
            'language_code': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'rev': ('IntegerTupleField', [], {'max_length': '64', 'null': 'True'}),
            'total': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'trans': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'trans_perc': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'untrans': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'untrans_perc': ('django.db.models.fields.PositiveIntegerField', [], {'default': '100'})
        }
    }
    
    complete_apps = ['translations']
