
from south.db import db
from django.db import models
from txcollections.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Changing field 'Collection.slug'
        db.alter_column('txcollections_collection', 'slug', models.SlugField(_('Slug'), unique=True, max_length=30))
        
    
    def backwards(self, orm):
        
        # Changing field 'Collection.slug'
        db.alter_column('txcollections_collection', 'slug', models.SlugField(_('Slug'), max_length=30))
        
    
    
    models = {
        'txcollections.collectionrelease': {
            'Meta': {'unique_together': "['slug','collection']", 'db_table': "'collections_release'"},
            'collection': ('models.ForeignKey', ['Collection'], {'related_name': "'releases'"}),
            'created': ('models.DateTimeField', [], {'auto_now_add': 'True', 'editable': 'False'}),
            'description': ('models.CharField', ["_('Description')"], {'max_length': '255', 'blank': 'True'}),
            'develfreeze_date': ('models.DateTimeField', ["_('Devel freeze date')"], {'null': 'True', 'blank': 'True'}),
            'enabled': ('models.BooleanField', ["_('Enabled')"], {'default': 'True', 'editable': 'False'}),
            'hidden': ('models.BooleanField', ["_('Hidden')"], {'default': 'False', 'editable': 'False'}),
            'homepage': ('models.URLField', [], {'verify_exists': 'False', 'blank': 'True'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'long_description': ('models.TextField', ["_('Long description')"], {'max_length': '1000', 'blank': 'True'}),
            'long_description_html': ('models.TextField', ["_('HTML Description')"], {'max_length': '1000', 'editable': 'False', 'blank': 'True'}),
            'modified': ('models.DateTimeField', [], {'auto_now': 'True', 'editable': 'False'}),
            'name': ('models.CharField', ["_('Name')"], {'max_length': '50'}),
            'release_date': ('models.DateTimeField', ["_('Release date')"], {'null': 'True', 'blank': 'True'}),
            'slug': ('models.SlugField', ["_('Slug')"], {'max_length': '30'}),
            'stringfreeze_date': ('models.DateTimeField', ["_('String freeze date')"], {'null': 'True', 'blank': 'True'})
        },
        'txcollections.collection': {
            'Meta': {'ordering': "('name',)", 'db_table': "'txcollections_collection'", 'get_latest_by': "'created'"},
            'created': ('models.DateTimeField', [], {'auto_now_add': 'True', 'editable': 'False'}),
            'description': ('models.CharField', ["_('Description')"], {'max_length': '255', 'blank': 'True'}),
            'enabled': ('models.BooleanField', ["_('Enabled')"], {'default': 'True', 'editable': 'False'}),
            'hidden': ('models.BooleanField', ["_('Hidden')"], {'default': 'False', 'editable': 'False'}),
            'homepage': ('models.URLField', ["_('Homepage')"], {'verify_exists': 'False', 'blank': 'True'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'long_description': ('models.TextField', ["_('Long description')"], {'max_length': '1000', 'blank': 'True'}),
            'long_description_html': ('models.TextField', ["_('HTML Description')"], {'max_length': '1000', 'editable': 'False', 'blank': 'True'}),
            'modified': ('models.DateTimeField', [], {'auto_now': 'True', 'editable': 'False'}),
            'name': ('models.CharField', ["_('Name')"], {'max_length': '50'}),
            'slug': ('models.SlugField', ["_('Slug')"], {'unique': 'True', 'max_length': '30'}),
            'tags': ('TagField', [], {})
        }
    }
    
    complete_apps = ['txcollections']
