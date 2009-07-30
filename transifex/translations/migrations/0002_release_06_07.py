# -*- coding: utf-8 -*-

from south.db import db
from django.db import models
from translations.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding field 'POFile.rev'
        db.add_column('translations_pofile', 'rev', IntegerTupleField(max_length=64, null=True))
        
        # Changing field 'POFile.filename'
        db.alter_column('translations_pofile', 'filename', models.CharField(max_length=255, null=False, db_index=True))
        
        # Changing field 'POFile.is_pot'
        db.alter_column('translations_pofile', 'is_pot', models.BooleanField(default=False, editable=False, db_index=True))
        
    
    
    def backwards(self, orm):
        
        # Deleting field 'POFile.rev'
        db.delete_column('translations_pofile', 'rev')
        
        # Changing field 'POFile.filename'
        db.alter_column('translations_pofile', 'filename', models.CharField(max_length=255, null=False))
        
        # Changing field 'POFile.is_pot'
        db.alter_column('translations_pofile', 'is_pot', models.BooleanField(default=False, editable=False))
        
    
    
    models = {
        'auth.user': {
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True'})
        },
        'translations.pofilelock': {
            'Meta': {'unique_together': "('pofile','owner')", 'db_table': "'translations_pofile_lock'"},
            'created': ('models.DateTimeField', [], {'auto_now_add': 'True', 'editable': 'False'}),
            'enabled': ('models.BooleanField', [], {'default': 'True'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'modified': ('models.DateTimeField', [], {'auto_now': 'True', 'editable': 'False'}),
            'name': ('models.CharField', [], {'max_length': '255', 'null': 'True'}),
            'owner': ('models.ForeignKey', ['User'], {}),
            'pofile': ('models.ForeignKey', ['POFile'], {'related_name': "'locks'", 'null': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label','model'),)", 'db_table': "'django_content_type'"},
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True'})
        },
        'translations.pofile': {
            'Meta': {'unique_together': '("content_type","object_id","filename")', 'get_latest_by': "'created'", 'ordering': "('language__name',)", 'db_table': "'translations_pofile'"},
            'content_type': ('models.ForeignKey', ['ContentType'], {}),
            'created': ('models.DateTimeField', [], {'auto_now_add': 'True', 'editable': 'False'}),
            'enabled': ('models.BooleanField', [], {'default': 'True', 'editable': 'False'}),
            'error': ('models.BooleanField', [], {'default': 'False', 'editable': 'False'}),
            'filename': ('models.CharField', [], {'max_length': '255', 'null': 'False', 'db_index': 'True'}),
            'fuzzy': ('models.PositiveIntegerField', [], {'default': '0'}),
            'fuzzy_perc': ('models.PositiveIntegerField', [], {'default': '0', 'editable': 'False'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'is_msgmerged': ('models.BooleanField', [], {'default': 'True', 'editable': 'False'}),
            'is_pot': ('models.BooleanField', [], {'default': 'False', 'editable': 'False', 'db_index': 'True'}),
            'language': ('models.ForeignKey', ['Language'], {'null': 'True'}),
            'language_code': ('models.CharField', [], {'max_length': '20', 'null': 'True'}),
            'modified': ('models.DateTimeField', [], {'auto_now': 'True', 'editable': 'False'}),
            'object_id': ('models.PositiveIntegerField', [], {}),
            'rev': ('IntegerTupleField', [], {'max_length': '64', 'null': 'True'}),
            'total': ('models.PositiveIntegerField', [], {'default': '0'}),
            'trans': ('models.PositiveIntegerField', [], {'default': '0'}),
            'trans_perc': ('models.PositiveIntegerField', [], {'default': '0', 'editable': 'False'}),
            'untrans': ('models.PositiveIntegerField', [], {'default': '0'}),
            'untrans_perc': ('models.PositiveIntegerField', [], {'default': '100', 'editable': 'False'})
        },
        'languages.language': {
            'Meta': {'ordering': "('name',)", 'db_table': "'translations_language'"},
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True'})
        }
    }
    
    complete_apps = ['translations']
