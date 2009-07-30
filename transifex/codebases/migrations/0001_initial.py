
from south.db import db
from django.db import models
from codebases.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'Unit'
        db.create_table('codebases_unit', (
            ('name', models.CharField(_('Name'), max_length=100, unique=True)),
            ('last_checkout', models.DateTimeField(null=True, editable=False)),
            ('created', models.DateTimeField(auto_now_add=True, editable=False)),
            ('root', models.CharField(_('Root'), max_length=255)),
            ('modified', models.DateTimeField(auto_now=True, editable=False)),
            ('type', models.CharField(_('Type'), max_length=10)),
            ('id', models.AutoField(primary_key=True)),
        ))
        db.send_create_signal('codebases', ['Unit'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'Unit'
        db.delete_table('codebases_unit')
        
    
    
    models = {
        'codebases.unit': {
            'Meta': {'ordering': "('name',)", 'get_latest_by': "'created'"},
            'created': ('models.DateTimeField', [], {'auto_now_add': 'True', 'editable': 'False'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'last_checkout': ('models.DateTimeField', [], {'null': 'True', 'editable': 'False'}),
            'modified': ('models.DateTimeField', [], {'auto_now': 'True', 'editable': 'False'}),
            'name': ('models.CharField', ["_('Name')"], {'max_length': '100', 'unique': 'True'}),
            'root': ('models.CharField', ["_('Root')"], {'max_length': '255'}),
            'type': ('models.CharField', ["_('Type')"], {'max_length': '10'})
        }
    }
    
    complete_apps = ['codebases']
