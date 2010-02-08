
from south.db import db
from django.db import models
from txcollections.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Deleting model 'collectionrelease'
        db.delete_table('collections_release')
        
        # Deleting model 'collection'
        db.delete_table('txcollections_collection')
        
    
    
    def backwards(self, orm):
        
        # Adding model 'collectionrelease'
        db.create_table('collections_release', (
            ('slug', orm['txcollections.collection:slug']),
            ('description', orm['txcollections.collection:description']),
            ('created', orm['txcollections.collection:created']),
            ('long_description_html', orm['txcollections.collection:long_description_html']),
            ('enabled', orm['txcollections.collection:enabled']),
            ('modified', orm['txcollections.collection:modified']),
            ('collection', orm['txcollections.collection:collection']),
            ('long_description', orm['txcollections.collection:long_description']),
            ('release_date', orm['txcollections.collection:release_date']),
            ('stringfreeze_date', orm['txcollections.collection:stringfreeze_date']),
            ('hidden', orm['txcollections.collection:hidden']),
            ('homepage', orm['txcollections.collection:homepage']),
            ('id', orm['txcollections.collection:id']),
            ('develfreeze_date', orm['txcollections.collection:develfreeze_date']),
            ('name', orm['txcollections.collection:name']),
        ))
        db.send_create_signal('txcollections', ['collectionrelease'])
        
        # Adding model 'collection'
        db.create_table('txcollections_collection', (
            ('description', orm['txcollections.collection:description']),
            ('tags', orm['txcollections.collection:tags']),
            ('id', orm['txcollections.collection:id']),
            ('slug', orm['txcollections.collection:slug']),
            ('name', orm['txcollections.collection:name']),
            ('created', orm['txcollections.collection:created']),
            ('long_description_html', orm['txcollections.collection:long_description_html']),
            ('enabled', orm['txcollections.collection:enabled']),
            ('modified', orm['txcollections.collection:modified']),
            ('long_description', orm['txcollections.collection:long_description']),
            ('hidden', orm['txcollections.collection:hidden']),
            ('homepage', orm['txcollections.collection:homepage']),
        ))
        db.send_create_signal('txcollections', ['collection'])
        
    
    
    models = {
        
    }
    
    complete_apps = ['txcollections']
