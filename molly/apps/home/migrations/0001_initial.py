# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Config'
        db.create_table('home_config', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('key', self.gf('django.db.models.fields.SlugField')(max_length=50, db_index=True)),
            ('value', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('home', ['Config'])

        # Adding model 'UserMessage'
        db.create_table('home_usermessage', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('session_key', self.gf('django.db.models.fields.TextField')()),
            ('message', self.gf('django.db.models.fields.TextField')()),
            ('read', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('when', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('home', ['UserMessage'])


    def backwards(self, orm):
        
        # Deleting model 'Config'
        db.delete_table('home_config')

        # Deleting model 'UserMessage'
        db.delete_table('home_usermessage')


    models = {
        'home.config': {
            'Meta': {'object_name': 'Config'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {})
        },
        'home.usermessage': {
            'Meta': {'object_name': 'UserMessage'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'read': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'session_key': ('django.db.models.fields.TextField', [], {}),
            'when': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['home']
