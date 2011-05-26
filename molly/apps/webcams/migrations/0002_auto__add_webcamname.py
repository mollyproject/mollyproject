# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'WebcamName'
        db.create_table('webcams_webcamname', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('webcam', self.gf('django.db.models.fields.related.ForeignKey')(related_name='names', to=orm['webcams.Webcam'])),
            ('language_code', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('title', self.gf('django.db.models.fields.TextField')()),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('credit', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('webcams', ['WebcamName'])


    def backwards(self, orm):
        
        # Deleting model 'WebcamName'
        db.delete_table('webcams_webcamname')


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
        },
        'webcams.webcamname': {
            'Meta': {'object_name': 'WebcamName'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language_code': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'title': ('django.db.models.fields.TextField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'credit': ('django.db.models.fields.TextField', [], {}),
            'webcam': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'names'", 'to': "orm['webcams.Webcam']"})
        }
    }

    complete_apps = ['webcams']
