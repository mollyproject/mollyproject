# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Batch'
        db.create_table('batch_processing_batch', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.TextField')()),
            ('local_name', self.gf('django.db.models.fields.TextField')()),
            ('provider_name', self.gf('django.db.models.fields.TextField')()),
            ('method_name', self.gf('django.db.models.fields.TextField')()),
            ('cron_stmt', self.gf('django.db.models.fields.TextField')()),
            ('enabled', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('_metadata', self.gf('django.db.models.fields.TextField')(default='null')),
            ('last_run', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('pending', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('currently_running', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('log', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('batch_processing', ['Batch'])


    def backwards(self, orm):
        
        # Deleting model 'Batch'
        db.delete_table('batch_processing_batch')


    models = {
        'batch_processing.batch': {
            'Meta': {'object_name': 'Batch'},
            '_metadata': ('django.db.models.fields.TextField', [], {'default': "'null'"}),
            'cron_stmt': ('django.db.models.fields.TextField', [], {}),
            'currently_running': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_run': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'local_name': ('django.db.models.fields.TextField', [], {}),
            'log': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'method_name': ('django.db.models.fields.TextField', [], {}),
            'pending': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'provider_name': ('django.db.models.fields.TextField', [], {}),
            'title': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['batch_processing']
