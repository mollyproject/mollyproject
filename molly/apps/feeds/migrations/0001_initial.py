# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Tag'
        db.create_table('feeds_tag', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=128)),
        ))
        db.send_create_signal('feeds', ['Tag'])

        # Adding model 'Feed'
        db.create_table('feeds_feed', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.TextField')()),
            ('unit', self.gf('django.db.models.fields.CharField')(max_length=10, null=True, blank=True)),
            ('rss_url', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50, db_index=True)),
            ('last_modified', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('ptype', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('provider', self.gf('django.db.models.fields.CharField')(max_length=128)),
        ))
        db.send_create_signal('feeds', ['Feed'])

        # Adding M2M table for field tags on 'Feed'
        db.create_table('feeds_feed_tags', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('feed', models.ForeignKey(orm['feeds.feed'], null=False)),
            ('tag', models.ForeignKey(orm['feeds.tag'], null=False))
        ))
        db.create_unique('feeds_feed_tags', ['feed_id', 'tag_id'])

        # Adding model 'vCard'
        db.create_table('feeds_vcard', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uri', self.gf('django.db.models.fields.TextField')()),
            ('name', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('address', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('telephone', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('location', self.gf('django.contrib.gis.db.models.fields.PointField')(null=True)),
            ('entity', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['places.Entity'], null=True, blank=True)),
        ))
        db.send_create_signal('feeds', ['vCard'])

        # Adding model 'Series'
        db.create_table('feeds_series', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('feed', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['feeds.Feed'])),
            ('guid', self.gf('django.db.models.fields.TextField')()),
            ('title', self.gf('django.db.models.fields.TextField')()),
            ('unit', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['feeds.vCard'], null=True, blank=True)),
        ))
        db.send_create_signal('feeds', ['Series'])

        # Adding M2M table for field tags on 'Series'
        db.create_table('feeds_series_tags', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('series', models.ForeignKey(orm['feeds.series'], null=False)),
            ('tag', models.ForeignKey(orm['feeds.tag'], null=False))
        ))
        db.create_unique('feeds_series_tags', ['series_id', 'tag_id'])

        # Adding model 'Item'
        db.create_table('feeds_item', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('feed', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['feeds.Feed'])),
            ('title', self.gf('django.db.models.fields.TextField')()),
            ('guid', self.gf('django.db.models.fields.TextField')()),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('link', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('last_modified', self.gf('django.db.models.fields.DateTimeField')()),
            ('ptype', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('organiser', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='organising_set', null=True, to=orm['feeds.vCard'])),
            ('speaker', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='speaking_set', null=True, to=orm['feeds.vCard'])),
            ('venue', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='venue_set', null=True, to=orm['feeds.vCard'])),
            ('contact', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='contact_set', null=True, to=orm['feeds.vCard'])),
            ('series', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['feeds.Series'], null=True, blank=True)),
            ('ordinal', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('track', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('dt_start', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('dt_end', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('dt_has_time', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('feeds', ['Item'])

        # Adding M2M table for field tags on 'Item'
        db.create_table('feeds_item_tags', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('item', models.ForeignKey(orm['feeds.item'], null=False)),
            ('tag', models.ForeignKey(orm['feeds.tag'], null=False))
        ))
        db.create_unique('feeds_item_tags', ['item_id', 'tag_id'])


    def backwards(self, orm):
        
        # Deleting model 'Tag'
        db.delete_table('feeds_tag')

        # Deleting model 'Feed'
        db.delete_table('feeds_feed')

        # Removing M2M table for field tags on 'Feed'
        db.delete_table('feeds_feed_tags')

        # Deleting model 'vCard'
        db.delete_table('feeds_vcard')

        # Deleting model 'Series'
        db.delete_table('feeds_series')

        # Removing M2M table for field tags on 'Series'
        db.delete_table('feeds_series_tags')

        # Deleting model 'Item'
        db.delete_table('feeds_item')

        # Removing M2M table for field tags on 'Item'
        db.delete_table('feeds_item_tags')


    models = {
        'feeds.feed': {
            'Meta': {'ordering': "('title',)", 'object_name': 'Feed'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'provider': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'ptype': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'rss_url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['feeds.Tag']", 'symmetrical': 'False', 'blank': 'True'}),
            'title': ('django.db.models.fields.TextField', [], {}),
            'unit': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'})
        },
        'feeds.item': {
            'Meta': {'ordering': "('-last_modified',)", 'object_name': 'Item'},
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'contact_set'", 'null': 'True', 'to': "orm['feeds.vCard']"}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'dt_end': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'dt_has_time': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'dt_start': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'feed': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['feeds.Feed']"}),
            'guid': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {}),
            'link': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'ordinal': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'organiser': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'organising_set'", 'null': 'True', 'to': "orm['feeds.vCard']"}),
            'ptype': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'series': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['feeds.Series']", 'null': 'True', 'blank': 'True'}),
            'speaker': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'speaking_set'", 'null': 'True', 'to': "orm['feeds.vCard']"}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['feeds.Tag']", 'symmetrical': 'False', 'blank': 'True'}),
            'title': ('django.db.models.fields.TextField', [], {}),
            'track': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'venue': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'venue_set'", 'null': 'True', 'to': "orm['feeds.vCard']"})
        },
        'feeds.series': {
            'Meta': {'object_name': 'Series'},
            'feed': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['feeds.Feed']"}),
            'guid': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['feeds.Tag']", 'symmetrical': 'False', 'blank': 'True'}),
            'title': ('django.db.models.fields.TextField', [], {}),
            'unit': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['feeds.vCard']", 'null': 'True', 'blank': 'True'})
        },
        'feeds.tag': {
            'Meta': {'object_name': 'Tag'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'feeds.vcard': {
            'Meta': {'object_name': 'vCard'},
            'address': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'entity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['places.Entity']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.contrib.gis.db.models.fields.PointField', [], {'null': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'telephone': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'uri': ('django.db.models.fields.TextField', [], {})
        },
        'places.entity': {
            'Meta': {'ordering': "('title',)", 'object_name': 'Entity'},
            '_identifiers': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['places.Identifier']", 'symmetrical': 'False'}),
            '_metadata': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'absolute_url': ('django.db.models.fields.TextField', [], {}),
            'all_types': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'entities'", 'blank': 'True', 'to': "orm['places.EntityType']"}),
            'all_types_completion': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'entities_completion'", 'blank': 'True', 'to': "orm['places.EntityType']"}),
            'geometry': ('django.contrib.gis.db.models.fields.GeometryField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier_scheme': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'identifier_value': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'is_stack': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_sublocation': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'location': ('django.contrib.gis.db.models.fields.PointField', [], {'null': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['places.Entity']", 'null': 'True'}),
            'primary_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['places.EntityType']", 'null': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['places.Source']"}),
            'title': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'places.entitytype': {
            'Meta': {'ordering': "('verbose_name',)", 'object_name': 'EntityType'},
            'article': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'note': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'show_in_category_list': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'show_in_nearby_list': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'subtype_of': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'subtypes'", 'blank': 'True', 'to': "orm['places.EntityType']"}),
            'subtype_of_completion': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'subtypes_completion'", 'blank': 'True', 'to': "orm['places.EntityType']"}),
            'verbose_name': ('django.db.models.fields.TextField', [], {}),
            'verbose_name_plural': ('django.db.models.fields.TextField', [], {})
        },
        'places.identifier': {
            'Meta': {'object_name': 'Identifier'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'scheme': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '256'})
        },
        'places.source': {
            'Meta': {'object_name': 'Source'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'module_name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        }
    }

    complete_apps = ['feeds']
