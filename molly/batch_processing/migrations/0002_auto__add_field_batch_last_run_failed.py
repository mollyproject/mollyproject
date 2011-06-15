# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'Batch.last_run_failed'
        db.add_column('batch_processing_batch', 'last_run_failed', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'Batch.last_run_failed'
        db.delete_column('batch_processing_batch', 'last_run_failed')


    models = {
        'batch_processing.batch': {
            'Meta': {'object_name': 'Batch'},
            '_metadata': ('django.db.models.fields.TextField', [], {'default': "'null'"}),
            'cron_stmt': ('django.db.models.fields.TextField', [], {}),
            'currently_running': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_run': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'last_run_failed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'local_name': ('django.db.models.fields.TextField', [], {}),
            'log': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'method_name': ('django.db.models.fields.TextField', [], {}),
            'pending': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'provider_name': ('django.db.models.fields.TextField', [], {}),
            'title': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['batch_processing']
