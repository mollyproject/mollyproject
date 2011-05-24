# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting field 'EntityTypeName.article'
        db.delete_column('places_entitytypename', 'article')

        # Adding field 'EntityTypeName.verbose_name_singular'
        db.add_column('places_entitytypename', 'verbose_name_singular', self.gf('django.db.models.fields.TextField')(default=''), keep_default=False)


    def backwards(self, orm):
        
        # User chose to not deal with backwards NULL issues for 'EntityTypeName.article'
        raise RuntimeError("Cannot reverse this migration. 'EntityTypeName.article' and its values cannot be restored.")

        # Deleting field 'EntityTypeName.verbose_name_singular'
        db.delete_column('places_entitytypename', 'verbose_name_singular')


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
            'is_stack': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_sublocation': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
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
            'Meta': {'object_name': 'EntityGroupName'},
            'entity_group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'names'", 'to': "orm['places.EntityGroup']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language_code': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'title': ('django.db.models.fields.TextField', [], {})
        },
        'places.entityname': {
            'Meta': {'object_name': 'EntityName'},
            'entity_group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'names'", 'to': "orm['places.Entity']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language_code': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'title': ('django.db.models.fields.TextField', [], {})
        },
        'places.entitytype': {
            'Meta': {'object_name': 'EntityType'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['places.EntityTypeCategory']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'note': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'show_in_category_list': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'show_in_nearby_list': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'subtype_of': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'subtypes'", 'blank': 'True', 'to': "orm['places.EntityType']"}),
            'subtype_of_completion': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'subtypes_completion'", 'blank': 'True', 'to': "orm['places.EntityType']"})
        },
        'places.entitytypecategory': {
            'Meta': {'object_name': 'EntityTypeCategory'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'places.entitytypecategoryname': {
            'Meta': {'object_name': 'EntityTypeCategoryName'},
            'entity_type_category': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'names'", 'to': "orm['places.EntityTypeCategory']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language_code': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'name': ('django.db.models.fields.TextField', [], {})
        },
        'places.entitytypename': {
            'Meta': {'object_name': 'EntityTypeName'},
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
        'places.source': {
            'Meta': {'object_name': 'Source'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'module_name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        }
    }

    complete_apps = ['places']
