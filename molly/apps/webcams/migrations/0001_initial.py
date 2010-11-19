# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Webcam'
        db.create_table('webcams_webcam', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50, db_index=True)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('fetch_period', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('title', self.gf('django.db.models.fields.TextField')()),
            ('description', self.gf('django.db.models.fields.TextField')(null=True)),
            ('credit', self.gf('django.db.models.fields.TextField')(null=True)),
        ))
        db.send_create_signal('webcams', ['Webcam'])


    def backwards(self, orm):
        
        # Deleting model 'Webcam'
        db.delete_table('webcams_webcam')


    models = {
        'webcams.webcam': {
            'Meta': {'ordering': "('title',)", 'object_name': 'Webcam'},
            'credit': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'fetch_period': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'title': ('django.db.models.fields.TextField', [], {}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['webcams']
