# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'PodcastCategory'
        db.create_table('podcasts_podcastcategory', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50, db_index=True)),
            ('name', self.gf('django.db.models.fields.TextField')()),
            ('order', self.gf('django.db.models.fields.IntegerField')(null=True)),
        ))
        db.send_create_signal('podcasts', ['PodcastCategory'])

        # Adding model 'Podcast'
        db.create_table('podcasts_podcast', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50, db_index=True)),
            ('title', self.gf('django.db.models.fields.TextField')(null=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True)),
            ('rss_url', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('last_updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['podcasts.PodcastCategory'], null=True)),
            ('most_recent_item_date', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('medium', self.gf('django.db.models.fields.CharField')(max_length=8, null=True)),
            ('provider', self.gf('django.db.models.fields.TextField')()),
            ('license', self.gf('django.db.models.fields.URLField')(max_length=200, null=True)),
            ('logo', self.gf('django.db.models.fields.URLField')(max_length=200, null=True)),
        ))
        db.send_create_signal('podcasts', ['Podcast'])

        # Adding model 'PodcastItem'
        db.create_table('podcasts_podcastitem', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('podcast', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['podcasts.Podcast'])),
            ('title', self.gf('django.db.models.fields.TextField')(null=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True)),
            ('published_date', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('author', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('duration', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
            ('guid', self.gf('django.db.models.fields.TextField')()),
            ('order', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('license', self.gf('django.db.models.fields.URLField')(max_length=200, null=True)),
        ))
        db.send_create_signal('podcasts', ['PodcastItem'])

        # Adding model 'PodcastEnclosure'
        db.create_table('podcasts_podcastenclosure', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('podcast_item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['podcasts.PodcastItem'])),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('length', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('mimetype', self.gf('django.db.models.fields.TextField')(null=True)),
        ))
        db.send_create_signal('podcasts', ['PodcastEnclosure'])


    def backwards(self, orm):
        
        # Deleting model 'PodcastCategory'
        db.delete_table('podcasts_podcastcategory')

        # Deleting model 'Podcast'
        db.delete_table('podcasts_podcast')

        # Deleting model 'PodcastItem'
        db.delete_table('podcasts_podcastitem')

        # Deleting model 'PodcastEnclosure'
        db.delete_table('podcasts_podcastenclosure')


    models = {
        'podcasts.podcast': {
            'Meta': {'ordering': "('title',)", 'object_name': 'Podcast'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['podcasts.PodcastCategory']", 'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'license': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True'}),
            'logo': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True'}),
            'medium': ('django.db.models.fields.CharField', [], {'max_length': '8', 'null': 'True'}),
            'most_recent_item_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'provider': ('django.db.models.fields.TextField', [], {}),
            'rss_url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'title': ('django.db.models.fields.TextField', [], {'null': 'True'})
        },
        'podcasts.podcastcategory': {
            'Meta': {'ordering': "('order', 'name')", 'object_name': 'PodcastCategory'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'order': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'})
        },
        'podcasts.podcastenclosure': {
            'Meta': {'object_name': 'PodcastEnclosure'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'length': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'mimetype': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'podcast_item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['podcasts.PodcastItem']"}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        'podcasts.podcastitem': {
            'Meta': {'object_name': 'PodcastItem'},
            'author': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'duration': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'guid': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'license': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True'}),
            'order': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'podcast': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['podcasts.Podcast']"}),
            'published_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'title': ('django.db.models.fields.TextField', [], {'null': 'True'})
        }
    }

    complete_apps = ['podcasts']
