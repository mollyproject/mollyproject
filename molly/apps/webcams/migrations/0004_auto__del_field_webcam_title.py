# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting field 'Webcam.title'
        db.delete_column('webcams_webcam', 'title')
        db.delete_column('webcams_webcam', 'credit')
        db.delete_column('webcams_webcam', 'description')


    def backwards(self, orm):
        
        # Adding field 'Webcam.title'
        db.add_column('webcams_webcam', 'title', self.gf('django.db.models.fields.TextField')(default=''), keep_default=False)
        db.add_column('webcams_webcam', 'credit', self.gf('django.db.models.fields.TextField')(default=''), keep_default=False)
        db.add_column('webcams_webcam', 'description', self.gf('django.db.models.fields.TextField')(default=''), keep_default=False)


    models = {
        'webcams.webcam': {
            'Meta': {'object_name': 'Webcam'},
            'fetch_period': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
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
