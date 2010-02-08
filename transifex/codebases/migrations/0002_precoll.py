
from south.db import db
from django.db import models
from codebases.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Changing field 'Unit.name'
        # (to signature: django.db.models.fields.CharField(unique=True, max_length=100))
        db.alter_column('codebases_unit', 'name', orm['codebases.unit:name'])
        
        # Changing field 'Unit.last_checkout'
        # (to signature: django.db.models.fields.DateTimeField(null=True))
        db.alter_column('codebases_unit', 'last_checkout', orm['codebases.unit:last_checkout'])
        
        # Changing field 'Unit.created'
        # (to signature: django.db.models.fields.DateTimeField(auto_now_add=True, blank=True))
        db.alter_column('codebases_unit', 'created', orm['codebases.unit:created'])
        
        # Changing field 'Unit.type'
        # (to signature: django.db.models.fields.CharField(max_length=10))
        db.alter_column('codebases_unit', 'type', orm['codebases.unit:type'])
        
        # Changing field 'Unit.modified'
        # (to signature: django.db.models.fields.DateTimeField(auto_now=True, blank=True))
        db.alter_column('codebases_unit', 'modified', orm['codebases.unit:modified'])
        
        # Changing field 'Unit.root'
        # (to signature: django.db.models.fields.CharField(max_length=255))
        db.alter_column('codebases_unit', 'root', orm['codebases.unit:root'])
        
    
    
    def backwards(self, orm):
        
        # Changing field 'Unit.name'
        # (to signature: models.CharField(_('Name'), unique=True, max_length=100))
        db.alter_column('codebases_unit', 'name', orm['codebases.unit:name'])
        
        # Changing field 'Unit.last_checkout'
        # (to signature: models.DateTimeField(null=True, editable=False))
        db.alter_column('codebases_unit', 'last_checkout', orm['codebases.unit:last_checkout'])
        
        # Changing field 'Unit.created'
        # (to signature: models.DateTimeField(auto_now_add=True, editable=False))
        db.alter_column('codebases_unit', 'created', orm['codebases.unit:created'])
        
        # Changing field 'Unit.type'
        # (to signature: models.CharField(_('Type'), max_length=10))
        db.alter_column('codebases_unit', 'type', orm['codebases.unit:type'])
        
        # Changing field 'Unit.modified'
        # (to signature: models.DateTimeField(auto_now=True, editable=False))
        db.alter_column('codebases_unit', 'modified', orm['codebases.unit:modified'])
        
        # Changing field 'Unit.root'
        # (to signature: models.CharField(_('Root'), max_length=255))
        db.alter_column('codebases_unit', 'root', orm['codebases.unit:root'])
        
    
    
    models = {
        'codebases.unit': {
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_checkout': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'root': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        }
    }
    
    complete_apps = ['codebases']
