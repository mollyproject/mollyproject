# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'ExternalImage'
        db.create_table('external_media_externalimage', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('etag', self.gf('django.db.models.fields.TextField')(null=True)),
            ('last_modified', self.gf('django.db.models.fields.TextField')(null=True)),
            ('last_updated', self.gf('django.db.models.fields.DateTimeField')()),
            ('width', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
            ('height', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
        ))
        db.send_create_signal('external_media', ['ExternalImage'])

        # Adding model 'ExternalImageSized'
        db.create_table('external_media_externalimagesized', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('external_image', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['external_media.ExternalImage'])),
            ('width', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('height', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50, db_index=True)),
            ('content_type', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('external_media', ['ExternalImageSized'])


    def backwards(self, orm):
        
        # Deleting model 'ExternalImage'
        db.delete_table('external_media_externalimage')

        # Deleting model 'ExternalImageSized'
        db.delete_table('external_media_externalimagesized')


    models = {
        'external_media.externalimage': {
            'Meta': {'object_name': 'ExternalImage'},
            'etag': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'height': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'width': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'})
        },
        'external_media.externalimagesized': {
            'Meta': {'object_name': 'ExternalImageSized'},
            'content_type': ('django.db.models.fields.TextField', [], {}),
            'external_image': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['external_media.ExternalImage']"}),
            'height': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'width': ('django.db.models.fields.PositiveIntegerField', [], {})
        }
    }

    complete_apps = ['external_media']
