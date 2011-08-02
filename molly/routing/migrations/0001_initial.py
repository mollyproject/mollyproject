# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'CachedRoute'
        db.create_table('routing_cachedroute', (
            ('hash', self.gf('django.db.models.fields.CharField')(unique=True, max_length=56, primary_key=True)),
            ('expires', self.gf('django.db.models.fields.DateTimeField')()),
            ('_cache', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('routing', ['CachedRoute'])


    def backwards(self, orm):
        
        # Deleting model 'CachedRoute'
        db.delete_table('routing_cachedroute')


    models = {
        'routing.cachedroute': {
            'Meta': {'object_name': 'CachedRoute'},
            '_cache': ('django.db.models.fields.TextField', [], {}),
            'expires': ('django.db.models.fields.DateTimeField', [], {}),
            'hash': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '56', 'primary_key': 'True'})
        }
    }

    complete_apps = ['routing']
