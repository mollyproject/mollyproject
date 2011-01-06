# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Feature'
        db.create_table('feature_vote_feature', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user_name', self.gf('django.db.models.fields.TextField')()),
            ('user_email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
            ('title', self.gf('django.db.models.fields.TextField')()),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('up_vote', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('down_vote', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('last_commented', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('is_public', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_removed', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('feature_vote', ['Feature'])


    def backwards(self, orm):
        
        # Deleting model 'Feature'
        db.delete_table('feature_vote_feature')


    models = {
        'feature_vote.feature': {
            'Meta': {'ordering': "('-last_commented', '-created')", 'object_name': 'Feature'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'down_vote': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_removed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_commented': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.TextField', [], {}),
            'up_vote': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'user_email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'user_name': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['feature_vote']
