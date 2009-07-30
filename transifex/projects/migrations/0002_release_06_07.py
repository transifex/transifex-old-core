# -*- coding: utf-8 -*-

from south.db import db
from django.db import models
from projects.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding field 'Component.should_calculate'
        db.add_column('projects_component', 'should_calculate', models.BooleanField(_('Calculate statistics?'), default=True))
        
        # Adding field 'Component.submission_type'
        db.add_column('projects_component', 'submission_type', models.CharField(_('Submit to'), max_length=10, blank=True, default=''))
        
    
    
    def backwards(self, orm):
        
        # Deleting field 'Component.should_calculate'
        db.delete_column('projects_component', 'should_calculate')
        
        # Deleting field 'Component.submission_type'
        db.delete_column('projects_component', 'submission_type')
        
    
    
    models = {
        'codebases.unit': {
            'Meta': {'ordering': "('name',)", 'get_latest_by': "'created'"},
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True'})
        },
        'projects.component': {
            'Meta': {'unique_together': '("project","slug")', 'get_latest_by': "'created'", 'ordering': "('name',)", 'db_table': "'projects_component'", 'permissions': '(("clear_cache","Can clear cache"),("refresh_stats","Can refresh statistics"),("submit_file","Can submit file"),)'},
            '_unit': ('models.OneToOneField', ['Unit'], {'editable': 'False', 'null': 'True', 'verbose_name': "_('Unit')", 'db_column': "'unit_id'", 'blank': 'True'}),
            'allows_submission': ('models.BooleanField', ["_('Allows submission')"], {'default': 'False'}),
            'created': ('models.DateTimeField', [], {'auto_now_add': 'True', 'editable': 'False'}),
            'description': ('models.CharField', ["_('Description')"], {'max_length': '255', 'blank': 'True'}),
            'enabled': ('models.BooleanField', ["_('Enabled')"], {'default': 'True', 'editable': 'False'}),
            'file_filter': ('models.CharField', ["_('File filter')"], {'max_length': '50'}),
            'full_name': ('models.CharField', [], {'max_length': '100', 'editable': 'False'}),
            'hidden': ('models.BooleanField', ["_('Hidden')"], {'default': 'False', 'editable': 'False'}),
            'i18n_type': ('models.CharField', ["_('I18n type')"], {'max_length': '20'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'long_description': ('models.TextField', ["_('Long description')"], {'max_length': '1000', 'blank': 'True'}),
            'long_description_html': ('models.TextField', ["_('HTML Description')"], {'max_length': '1000', 'editable': 'False', 'blank': 'True'}),
            'modified': ('models.DateTimeField', [], {'auto_now': 'True', 'editable': 'False'}),
            'name': ('models.CharField', ["_('Name')"], {'max_length': '50'}),
            # It's NOT a real field
            #'pofiles': ('generic.GenericRelation', ['POFile'], {}),
            'project': ('models.ForeignKey', ['Project'], {'verbose_name': "_('Project')"}),
            'releases': ('models.ManyToManyField', ['CollectionRelease'], {'related_name': "'components'", 'null': 'True', 'verbose_name': "_('Releases')", 'blank': 'True'}),
            'should_calculate': ('models.BooleanField', ["_('Calculate statistics?')"], {'default': 'True'}),
            'slug': ('models.SlugField', ["_('Slug')"], {'max_length': '30'}),
            'source_lang': ('models.CharField', ["_('Source language')"], {'max_length': '50'}),
            'submission_type': ('models.CharField', ["_('Submit to')"], {'default': "''", 'max_length': '10', 'blank': 'True'})
        },
        'auth.user': {
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True'})
        },
        'txcollections.collection': {
            'Meta': {'ordering': "('name',)", 'db_table': "'txcollections_collection'", 'get_latest_by': "'created'"},
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True'})
        },
        'txcollections.collectionrelease': {
            'Meta': {'unique_together': "['slug','collection']", 'db_table': "'collections_release'"},
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True'})
        },
        'projects.project': {
            'Meta': {'ordering': "('name',)", 'db_table': "'projects_project'", 'get_latest_by': "'created'"},
            'bug_tracker': ('models.URLField', ["_('Bug tracker')"], {'blank': 'True'}),
            'collections': ('models.ManyToManyField', ['Collection'], {'related_name': "'projects'", 'null': 'True', 'verbose_name': "_('Collections')", 'blank': 'True'}),
            'created': ('models.DateTimeField', [], {'auto_now_add': 'True', 'editable': 'False'}),
            'description': ('models.CharField', ["_('Description')"], {'max_length': '255', 'blank': 'True'}),
            'enabled': ('models.BooleanField', ["_('Enabled')"], {'default': 'True', 'editable': 'False'}),
            'feed': ('models.CharField', ["_('Feed')"], {'max_length': '255', 'blank': 'True'}),
            'hidden': ('models.BooleanField', ["_('Hidden')"], {'default': 'False', 'editable': 'False'}),
            'homepage': ('models.URLField', ["_('Homepage')"], {'verify_exists': 'False', 'blank': 'True'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'long_description': ('models.TextField', ["_('Long description')"], {'max_length': '1000', 'blank': 'True'}),
            'long_description_html': ('models.TextField', ["_('HTML Description')"], {'max_length': '1000', 'editable': 'False', 'blank': 'True'}),
            'maintainers': ('models.ManyToManyField', ['User'], {'related_name': "'projects_maintaining'", 'null': 'True', 'verbose_name': "_('Maintainers')", 'blank': 'False'}),
            'modified': ('models.DateTimeField', [], {'auto_now': 'True', 'editable': 'False'}),
            'name': ('models.CharField', ["_('Name')"], {'max_length': '50'}),
            'slug': ('models.SlugField', ["_('Slug')"], {'unique': 'True', 'max_length': '30'}),
            'tags': ('TagField', [], {'verbose_name': "_('Tags')"})
        }
    }
    
    complete_apps = ['projects']
