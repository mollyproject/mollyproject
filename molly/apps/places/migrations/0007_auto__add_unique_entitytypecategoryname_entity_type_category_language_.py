# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'EntityType.verbose_name_plural'
        db.delete_column('places_entitytype', 'verbose_name_plural')

        # Deleting field 'EntityType.article'
        db.delete_column('places_entitytype', 'article')

        # Deleting field 'EntityType.verbose_name'
        db.delete_column('places_entitytype', 'verbose_name')

        # Deleting field 'EntityGroup.title'
        db.delete_column('places_entitygroup', 'title')

        # Adding unique constraint on 'EntityName', fields ['language_code', 'entity']
        db.create_unique('places_entityname', ['language_code', 'entity_id'])

        # Adding unique constraint on 'EntityGroupName', fields ['entity_group', 'language_code']
        db.create_unique('places_entitygroupname', ['entity_group_id', 'language_code'])

        # Adding unique constraint on 'EntityTypeName', fields ['language_code', 'entity_type']
        db.create_unique('places_entitytypename', ['language_code', 'entity_type_id'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'EntityTypeName', fields ['language_code', 'entity_type']
        db.delete_unique('places_entitytypename', ['language_code', 'entity_type_id'])

        # Removing unique constraint on 'EntityGroupName', fields ['entity_group', 'language_code']
        db.delete_unique('places_entitygroupname', ['entity_group_id', 'language_code'])

        # Removing unique constraint on 'EntityName', fields ['language_code', 'entity']
        db.delete_unique('places_entityname', ['language_code', 'entity_id'])
        
        # Adding field 'EntityGroup.title'
        db.add_column('places_entitygroup', 'title', self.gf('django.db.models.fields.TextField')(default='', blank=True), keep_default=False)
        
        for eg in orm.EntityGroup.objects.all():
            eg.title = name_in_category(eg, 'title')
        
        # Adding field 'Entity.title'
        db.add_column('places_entity', 'title', self.gf('django.db.models.fields.TextField')(default='', blank=True), keep_default=False)

        for e in orm.Entity.objects.all():
            e.title = name_in_category(eg, 'title')
        
        # Adding field 'EntityType.verbose_name_plural'
        db.add_column('places_entitytype', 'verbose_name_plural', self.gf('django.db.models.fields.TextField')(default='', blank=True), keep_default=False)

        # Adding field 'EntityType.article'
        db.add_column('places_entitytype', 'article', self.gf('django.db.models.fields.CharField')(default='', blank=True, max_length=2), keep_default=False)

        # Adding field 'EntityType.verbose_name'
        db.add_column('places_entitytype', 'verbose_name', self.gf('django.db.models.fields.TextField')(default='', blank=True), keep_default=False)

        for e in orm.Entity.objects.all():
            e.article = name_in_category(eg, 'verbose_name_singular').split()[0]
            e.verbose_name = name_in_category(eg, 'verbose_name')
            e.verbose_name_plural = name_in_category(eg, 'verbose_name_plural')


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
            'note': ('django.db.models.fields.TextField', [], {'null': 'True'}),
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
        'places.source': {
            'Meta': {'object_name': 'Source'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'module_name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        }
    }

    complete_apps = ['places']
