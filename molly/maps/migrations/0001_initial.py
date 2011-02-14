# encoding: utf-8
import datetime
from south.db import db
from south.models import MigrationHistory
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # this is a custom migration because we changed the name of the app that
        # the models belong to 
        if MigrationHistory.objects.filter(app_name='osm').count() == 0:
            # Adding model 'GeneratedMap'
            db.create_table('osm_generatedmap', (
                ('hash', self.gf('django.db.models.fields.CharField')(unique=True, max_length=16, primary_key=True)),
                ('generated', self.gf('django.db.models.fields.DateTimeField')()),
                ('last_accessed', self.gf('django.db.models.fields.DateTimeField')()),
                ('_metadata', self.gf('django.db.models.fields.TextField')(blank=True)),
                ('faulty', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ))
            db.send_create_signal('maps', ['GeneratedMap'])
    
            # Adding model 'OSMTile'
            db.create_table('osm_osmtile', (
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('xtile', self.gf('django.db.models.fields.IntegerField')()),
                ('ytile', self.gf('django.db.models.fields.IntegerField')()),
                ('zoom', self.gf('django.db.models.fields.IntegerField')()),
                ('last_fetched', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ))
            db.send_create_signal('maps', ['OSMTile'])
    
            # Adding unique constraint on 'OSMTile', fields ['xtile', 'ytile', 'zoom']
            db.create_unique('osm_osmtile', ['xtile', 'ytile', 'zoom'])
    
            # Adding model 'OSMUpdate'
            db.create_table('osm_osmupdate', (
                ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('contributor_name', self.gf('django.db.models.fields.TextField')(blank=True)),
                ('contributor_email', self.gf('django.db.models.fields.TextField')(blank=True)),
                ('contributor_attribute', self.gf('django.db.models.fields.BooleanField')(default=False)),
                ('entity', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['places.Entity'])),
                ('submitted', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
                ('old', self.gf('django.db.models.fields.TextField')()),
                ('new', self.gf('django.db.models.fields.TextField')()),
                ('notes', self.gf('django.db.models.fields.TextField')(blank=True)),
                ('approved', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ))
            db.send_create_signal('maps', ['OSMUpdate'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'OSMTile', fields ['xtile', 'ytile', 'zoom']
        db.delete_unique('osm_osmtile', ['xtile', 'ytile', 'zoom'])

        # Deleting model 'GeneratedMap'
        db.delete_table('osm_generatedmap')

        # Deleting model 'OSMTile'
        db.delete_table('osm_osmtile')

        # Deleting model 'OSMUpdate'
        db.delete_table('osm_osmupdate')


    models = {
        'osm.generatedmap': {
            'Meta': {'object_name': 'GeneratedMap'},
            '_metadata': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'faulty': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'generated': ('django.db.models.fields.DateTimeField', [], {}),
            'hash': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '16', 'primary_key': 'True'}),
            'last_accessed': ('django.db.models.fields.DateTimeField', [], {})
        },
        'osm.osmtile': {
            'Meta': {'unique_together': "(('xtile', 'ytile', 'zoom'),)", 'object_name': 'OSMTile'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_fetched': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'xtile': ('django.db.models.fields.IntegerField', [], {}),
            'ytile': ('django.db.models.fields.IntegerField', [], {}),
            'zoom': ('django.db.models.fields.IntegerField', [], {})
        },
        'osm.osmupdate': {
            'Meta': {'object_name': 'OSMUpdate'},
            'approved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'contributor_attribute': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'contributor_email': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'contributor_name': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'entity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['places.Entity']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'new': ('django.db.models.fields.TextField', [], {}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'old': ('django.db.models.fields.TextField', [], {}),
            'submitted': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
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

    complete_apps = ['maps']
