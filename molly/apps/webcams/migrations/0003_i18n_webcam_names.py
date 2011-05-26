# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models
from django.conf import settings
from molly.utils.i18n import name_in_language

class Migration(DataMigration):

    def forwards(self, orm):
        """
        Move webcam names to i18n object
        """
        for webcam in orm.Webcam.objects.all():
            webcam.names.create(language_code=settings.LANGUAGE_CODE,
                                title=webcam.title,
                                credit=webcam.credit,
                                description=webcam.description)


    def backwards(self, orm):
        """
        Move i18n names to webcam object
        """
        for webcam in orm.Webcam.objects.all():
            webcam.title = name_in_language(webcam, 'title')
            webcam.description = name_in_language(webcam, 'description')
            webcam.credit = name_in_language(webcam, 'credit')

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
            'credit': ('django.db.models.fields.TextField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'webcam': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'names'", 'to': "orm['webcams.Webcam']"})
        }
    }

    complete_apps = ['webcams']
