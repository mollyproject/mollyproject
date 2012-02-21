# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding index on 'EntityTypeName', fields ['language_code']
        db.create_index('places_entitytypename', ['language_code'])

        # Adding index on 'EntityGroupName', fields ['language_code']
        db.create_index('places_entitygroupname', ['language_code'])


    def backwards(self, orm):
        
        # Removing index on 'EntityGroupName', fields ['language_code']
        db.delete_index('places_entitygroupname', ['language_code'])

        # Removing index on 'EntityTypeName', fields ['language_code']
        db.delete_index('places_entitytypename', ['language_code'])


    models = {
        'places.entity': {
            'Meta': {'object_name': 'Entity'},
            '_identifiers': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['places.Identifier']", 'symmetrical': 'False'}),
            '_metadata': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'absolute_url': ('django.db.models.fields.TextField', [], {}),
            'all_types': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'entities'", 'blank': 'True', 'to': "orm['places.EntityType']"}),
            'all_types_completion': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'entities_completion'", 'blank': 'True', 'to': "orm['places.EntityType']"}),
            'geometry': ('django.contrib.gis.db.models.fields.GeometryField', [], {'null': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['places.EntityGroup']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier_scheme': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'identifier_value': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'is_entrance': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'location': ('django.contrib.gis.db.models.fields.PointField', [], {'null': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['places.Entity']", 'null': 'True'}),
            'primary_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['places.EntityType']", 'null': 'True'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['places.Source']"})
        },
        'places.entitygroup': {
            'Meta': {'object_name': 'EntityGroup'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ref_code': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['places.Source']"})
        },
        'places.entitygroupname': {
            'Meta': {'unique_together': "(('entity_group', 'language_code'),)", 'object_name': 'EntityGroupName'},
            'entity_group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'names'", 'to': "orm['places.EntityGroup']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language_code': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'title': ('django.db.models.fields.TextField', [], {})
        },
        'places.entityname': {
            'Meta': {'unique_together': "(('entity', 'language_code'),)", 'object_name': 'EntityName'},
            'entity': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'names'", 'to': "orm['places.Entity']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language_code': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'title': ('django.db.models.fields.TextField', [], {})
        },
        'places.entitytype': {
            'Meta': {'object_name': 'EntityType'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['places.EntityTypeCategory']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'note': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'show_in_category_list': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'show_in_nearby_list': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'subtype_of': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'subtypes'", 'blank': 'True', 'to': "orm['places.EntityType']"}),
            'subtype_of_completion': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'subtypes_completion'", 'blank': 'True', 'to': "orm['places.EntityType']"})
        },
        'places.entitytypecategory': {
            'Meta': {'object_name': 'EntityTypeCategory'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {})
        },
        'places.entitytypename': {
            'Meta': {'unique_together': "(('entity_type', 'language_code'),)", 'object_name': 'EntityTypeName'},
            'entity_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'names'", 'to': "orm['places.EntityType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language_code': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'verbose_name': ('django.db.models.fields.TextField', [], {}),
            'verbose_name_plural': ('django.db.models.fields.TextField', [], {}),
            'verbose_name_singular': ('django.db.models.fields.TextField', [], {})
        },
        'places.identifier': {
            'Meta': {'object_name': 'Identifier'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'scheme': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '256'})
        },
        'places.journey': {
            'Meta': {'object_name': 'Journey'},
            'external_ref': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'route': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['places.Route']"}),
            'runs_from': ('django.db.models.fields.DateField', [], {}),
            'runs_in_school_holidays': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'runs_in_termtime': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'runs_on_bank_holidays': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'runs_on_friday': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'runs_on_monday': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'runs_on_non_bank_holidays': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'runs_on_saturday': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'runs_on_sunday': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'runs_on_thursday': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'runs_on_tuesday': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'runs_on_wednesday': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'runs_until': ('django.db.models.fields.DateField', [], {}),
            'vehicle': ('django.db.models.fields.TextField', [], {})
        },
        'places.route': {
            'Meta': {'object_name': 'Route'},
            'external_ref': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'operator': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'service_id': ('django.db.models.fields.TextField', [], {}),
            'service_name': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'stops': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['places.Entity']", 'through': "orm['places.StopOnRoute']", 'symmetrical': 'False'})
        },
        'places.scheduledstop': {
            'Meta': {'ordering': "['order']", 'object_name': 'ScheduledStop'},
            'activity': ('django.db.models.fields.CharField', [], {'default': "'B'", 'max_length': '1'}),
            'entity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['places.Entity']"}),
            'fare_stage': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'journey': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['places.Journey']"}),
            'order': ('django.db.models.fields.IntegerField', [], {}),
            'sta': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'}),
            'std': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'}),
            'times_estimated': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'places.source': {
            'Meta': {'object_name': 'Source'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'module_name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'places.stoponroute': {
            'Meta': {'ordering': "['order']", 'object_name': 'StopOnRoute'},
            'entity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['places.Entity']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.IntegerField', [], {}),
            'route': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['places.Route']"})
        }
    }

    complete_apps = ['places']
