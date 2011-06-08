# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'Feature.implemented_on'
        db.add_column('feature_vote_feature', 'implemented_on', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'Feature.implemented_on'
        db.delete_column('feature_vote_feature', 'implemented_on')


    models = {
        'feature_vote.feature': {
            'Meta': {'ordering': "('-last_commented', '-created')", 'object_name': 'Feature'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'down_vote': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'implemented_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
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
