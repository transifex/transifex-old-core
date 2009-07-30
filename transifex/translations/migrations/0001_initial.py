# -*- coding: utf-8 -*-

from south.db import db
from django.db import models
from translations.models import *

class Migration:
    
    def forwards(self, orm):
        
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
        
        # Adding model 'POFile'
        db.create_table('translations_pofile', (
            ('modified', models.DateTimeField(auto_now=True, editable=False)),
            ('untrans', models.PositiveIntegerField(default=0)),
            ('total', models.PositiveIntegerField(default=0)),
            ('fuzzy_perc', models.PositiveIntegerField(default=0, editable=False)),
            ('language', models.ForeignKey(orm['languages.Language'], null=True)),
            ('created', models.DateTimeField(auto_now_add=True, editable=False)),
            ('error', models.BooleanField(default=False, editable=False)),
            ('enabled', models.BooleanField(default=True, editable=False)),
            ('is_msgmerged', models.BooleanField(default=True, editable=False)),
            ('object_id', models.PositiveIntegerField()),
            ('filename', models.CharField(max_length=255, null=False)),
            ('is_pot', models.BooleanField(default=False, editable=False)),
            ('trans_perc', models.PositiveIntegerField(default=0, editable=False)),
            ('content_type', models.ForeignKey(orm['contenttypes.ContentType'])),
            ('language_code', models.CharField(max_length=20, null=True)),
            ('untrans_perc', models.PositiveIntegerField(default=100, editable=False)),
            ('fuzzy', models.PositiveIntegerField(default=0)),
            ('trans', models.PositiveIntegerField(default=0)),
            ('id', models.AutoField(primary_key=True)),
        ))
        db.send_create_signal('translations', ['POFile'])
        
        # Creating unique_together for [content_type, object_id, filename] on POFile.
        db.create_unique('translations_pofile', ['content_type_id', 'object_id', 'filename'])
        
        # Creating unique_together for [pofile, owner] on POFileLock.
        db.create_unique('translations_pofile_lock', ['pofile_id', 'owner_id'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'POFileLock'
        db.delete_table('translations_pofile_lock')
        
        # Deleting model 'POFile'
        db.delete_table('translations_pofile')
        
        # Deleting unique_together for [content_type, object_id, filename] on POFile.
        db.delete_unique('translations_pofile', ['content_type_id', 'object_id', 'filename'])
        
        # Deleting unique_together for [pofile, owner] on POFileLock.
        db.delete_unique('translations_pofile_lock', ['pofile_id', 'owner_id'])
        
    
    
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
            'filename': ('models.CharField', [], {'max_length': '255', 'null': 'False'}),
            'fuzzy': ('models.PositiveIntegerField', [], {'default': '0'}),
            'fuzzy_perc': ('models.PositiveIntegerField', [], {'default': '0', 'editable': 'False'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'is_msgmerged': ('models.BooleanField', [], {'default': 'True', 'editable': 'False'}),
            'is_pot': ('models.BooleanField', [], {'default': 'False', 'editable': 'False'}),
            'language': ('models.ForeignKey', ['Language'], {'null': 'True'}),
            'language_code': ('models.CharField', [], {'max_length': '20', 'null': 'True'}),
            'modified': ('models.DateTimeField', [], {'auto_now': 'True', 'editable': 'False'}),
            'object_id': ('models.PositiveIntegerField', [], {}),
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
