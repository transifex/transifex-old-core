
from south.db import db
import os
from django.db import models
from vcs.models import *

class Migration:

    depends_on = (
        ("codebases", "0001_initial"),
    )

    def forwards(self, orm):

        for unit in VcsUnit.objects.filter(type='svn'):
            if unit.branch == 'trunk':
                unit.root = os.path.join(unit.root, 'trunk')
            else:
                unit.root = os.path.join(unit.root, 'branches/%s' % unit.branch)
            unit.branch = '';
            unit.save()

    def backwards(self, orm):

        for unit in VcsUnit.objects.filter(type='svn'):
            if unit.root.endswith('/trunk'):
                unit.root = unit.root.split('/trunk')[0]
                unit.branch = 'trunk'
            elif '/branches/' in unit.root:
                unit.root = unit.root.split('/branches/')[0]
                unit.branch = unit.root.split('/branches/')[1]
            unit.save()
    
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
