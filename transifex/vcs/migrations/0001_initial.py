
from south.db import db
from django.db import models
from vcs.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'VcsUnit'
        db.create_table('vcs_vcsunit', (
            ('unit_ptr', orm['vcs.VcsUnit:unit_ptr']),
            ('branch', orm['vcs.VcsUnit:branch']),
            ('web_frontend', orm['vcs.VcsUnit:web_frontend']),
        ))
        db.send_create_signal('vcs', ['VcsUnit'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'VcsUnit'
        db.delete_table('vcs_vcsunit')
        
    
    
    models = {
        'codebases.unit': {
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_checkout': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'root': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'vcs.vcsunit': {
            'branch': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'unit_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['codebases.Unit']", 'unique': 'True', 'primary_key': 'True'}),
            'web_frontend': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        }
    }
    
    complete_apps = ['vcs']
