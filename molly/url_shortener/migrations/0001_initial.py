# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'ShortenedURL'
        db.create_table('url_shortener_shortenedurl', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('path', self.gf('django.db.models.fields.TextField')()),
            ('slug', self.gf('django.db.models.fields.TextField')(max_length=7)),
        ))
        db.send_create_signal('url_shortener', ['ShortenedURL'])


    def backwards(self, orm):
        
        # Deleting model 'ShortenedURL'
        db.delete_table('url_shortener_shortenedurl')


    models = {
        'url_shortener.shortenedurl': {
            'Meta': {'object_name': 'ShortenedURL'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'path': ('django.db.models.fields.TextField', [], {}),
            'slug': ('django.db.models.fields.TextField', [], {'max_length': '7'})
        }
    }

    complete_apps = ['url_shortener']
