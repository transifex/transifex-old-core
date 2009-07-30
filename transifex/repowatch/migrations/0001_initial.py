
from south.db import db
from django.db import models
from repowatch.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'Watch'
        db.create_table('repowatch_watch', (
            ('component', models.ForeignKey(orm['projects.Component'])),
            ('path', models.CharField(default=None, max_length=128, null=True)),
            ('rev', IntegerTupleField(max_length=64, null=True)),
            ('id', models.AutoField(primary_key=True)),
        ))
        db.send_create_signal('repowatch', ['Watch'])
        
        # Adding ManyToManyField 'Watch.user'
        db.create_table('repowatch_watch_user', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('watch', models.ForeignKey(Watch, null=False)),
            ('user', models.ForeignKey(User, null=False))
        ))
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'Watch'
        db.delete_table('repowatch_watch')
        
        # Dropping ManyToManyField 'Watch.user'
        db.delete_table('repowatch_watch_user')
        
    
    
    models = {
        'auth.user': {
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True'})
        },
        'repowatch.watch': {
            'component': ('models.ForeignKey', ['Component'], {}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'path': ('models.CharField', [], {'default': 'None', 'max_length': '128', 'null': 'True'}),
            'rev': ('IntegerTupleField', [], {'max_length': '64', 'null': 'True'}),
            'user': ('models.ManyToManyField', ['User'], {'related_name': "'watches'"})
        },
        'projects.component': {
            'Meta': {'unique_together': '("project","slug")', 'get_latest_by': "'created'", 'ordering': "('name',)", 'db_table': "'projects_component'", 'permissions': '(("clear_cache","Can clear cache"),("refresh_stats","Can refresh statistics"),("submit_file","Can submit file"),)'},
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True'})
        }
    }
    
    complete_apps = ['repowatch']
