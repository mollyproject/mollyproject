# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Geocode'
        db.create_table('geolocation_geocode', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('lon', self.gf('django.db.models.fields.FloatField')(null=True)),
            ('lat', self.gf('django.db.models.fields.FloatField')(null=True)),
            ('query', self.gf('django.db.models.fields.TextField')(null=True)),
            ('_results', self.gf('django.db.models.fields.TextField')(default='null')),
            ('updated', self.gf('django.db.models.fields.DateTimeField')()),
            ('local_name', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('geolocation', ['Geocode'])


    def backwards(self, orm):
        
        # Deleting model 'Geocode'
        db.delete_table('geolocation_geocode')


    models = {
        'geolocation.geocode': {
            'Meta': {'object_name': 'Geocode'},
            '_results': ('django.db.models.fields.TextField', [], {'default': "'null'"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lat': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'local_name': ('django.db.models.fields.TextField', [], {}),
            'lon': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'query': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {})
        }
    }

    complete_apps = ['geolocation']
