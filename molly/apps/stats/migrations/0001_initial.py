# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Hit'
        db.create_table('stats_hit', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('session_key', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('user_agent', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('device_id', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('ip_address', self.gf('django.db.models.fields.IPAddressField')(max_length=15)),
            ('referer', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('full_path', self.gf('django.db.models.fields.TextField')()),
            ('requested', self.gf('django.db.models.fields.DateTimeField')()),
            ('response_time', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('local_name', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('view_name', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('status_code', self.gf('django.db.models.fields.CharField')(max_length=3)),
            ('redirect_to', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('traceback', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('stats', ['Hit'])


    def backwards(self, orm):
        
        # Deleting model 'Hit'
        db.delete_table('stats_hit')


    models = {
        'stats.hit': {
            'Meta': {'object_name': 'Hit'},
            'device_id': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'full_path': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip_address': ('django.db.models.fields.IPAddressField', [], {'max_length': '15'}),
            'local_name': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'redirect_to': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'referer': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'requested': ('django.db.models.fields.DateTimeField', [], {}),
            'response_time': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'session_key': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'status_code': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'traceback': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'user_agent': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'view_name': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['stats']
