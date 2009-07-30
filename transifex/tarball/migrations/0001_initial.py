
from south.db import db
from django.db import models
from tarball.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'Tarball'
        db.create_table('tarball_tarball', (
            ('unit_ptr', models.OneToOneField(orm['codebases.Unit'])),
        ))
        db.send_create_signal('tarball', ['Tarball'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'Tarball'
        db.delete_table('tarball_tarball')
        
    
    
    models = {
        'codebases.unit': {
            'Meta': {'ordering': "('name',)", 'get_latest_by': "'created'"},
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True'})
        },
        'tarball.tarball': {
            'Meta': {'ordering': "('name',)", 'get_latest_by': "'created'", '_bases': ['codebases.models.Unit']},
            'unit_ptr': ('models.OneToOneField', ["orm['codebases.Unit']"], {})
        }
    }
    
    complete_apps = ['tarball']
