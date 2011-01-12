# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):

        # Adding model 'Source'
        db.create_table('places_source', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('module_name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('last_updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('places', ['Source'])

        # Adding model 'EntityType'
        db.create_table('places_entitytype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50, db_index=True)),
            ('article', self.gf('django.db.models.fields.CharField')(max_length=2)),
            ('verbose_name', self.gf('django.db.models.fields.TextField')()),
            ('verbose_name_plural', self.gf('django.db.models.fields.TextField')()),
            ('show_in_nearby_list', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('show_in_category_list', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('note', self.gf('django.db.models.fields.TextField')(null=True)),
        ))
        db.send_create_signal('places', ['EntityType'])

        # Adding M2M table for field subtype_of on 'EntityType'
        db.create_table('places_entitytype_subtype_of', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_entitytype', models.ForeignKey(orm['places.entitytype'], null=False)),
            ('to_entitytype', models.ForeignKey(orm['places.entitytype'], null=False))
        ))
        db.create_unique('places_entitytype_subtype_of', ['from_entitytype_id', 'to_entitytype_id'])

        # Adding M2M table for field subtype_of_completion on 'EntityType'
        db.create_table('places_entitytype_subtype_of_completion', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_entitytype', models.ForeignKey(orm['places.entitytype'], null=False)),
            ('to_entitytype', models.ForeignKey(orm['places.entitytype'], null=False))
        ))
        db.create_unique('places_entitytype_subtype_of_completion', ['from_entitytype_id', 'to_entitytype_id'])

        # Adding model 'Identifier'
        db.create_table('places_identifier', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('scheme', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=256)),
        ))
        db.send_create_signal('places', ['Identifier'])

        # Adding model 'Entity'
        db.create_table('places_entity', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['places.Source'])),
            ('primary_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['places.EntityType'], null=True)),
            ('location', self.gf('django.contrib.gis.db.models.fields.PointField')(null=True)),
            ('geometry', self.gf('django.contrib.gis.db.models.fields.GeometryField')(null=True)),
            ('_metadata', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('absolute_url', self.gf('django.db.models.fields.TextField')()),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['places.Entity'], null=True)),
            ('is_sublocation', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_stack', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('identifier_scheme', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('identifier_value', self.gf('django.db.models.fields.CharField')(max_length=256)),
        ))
        db.send_create_signal('places', ['Entity'])

        # Adding M2M table for field all_types on 'Entity'
        db.create_table('places_entity_all_types', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('entity', models.ForeignKey(orm['places.entity'], null=False)),
            ('entitytype', models.ForeignKey(orm['places.entitytype'], null=False))
        ))
        db.create_unique('places_entity_all_types', ['entity_id', 'entitytype_id'])

        # Adding M2M table for field all_types_completion on 'Entity'
        db.create_table('places_entity_all_types_completion', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('entity', models.ForeignKey(orm['places.entity'], null=False)),
            ('entitytype', models.ForeignKey(orm['places.entitytype'], null=False))
        ))
        db.create_unique('places_entity_all_types_completion', ['entity_id', 'entitytype_id'])

        # Adding M2M table for field _identifiers on 'Entity'
        db.create_table('places_entity__identifiers', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('entity', models.ForeignKey(orm['places.entity'], null=False)),
            ('identifier', models.ForeignKey(orm['places.identifier'], null=False))
        ))
        db.create_unique('places_entity__identifiers', ['entity_id', 'identifier_id'])


    def backwards(self, orm):

        # Deleting model 'Source'
        db.delete_table('places_source')

        # Deleting model 'EntityType'
        db.delete_table('places_entitytype')

        # Removing M2M table for field subtype_of on 'EntityType'
        db.delete_table('places_entitytype_subtype_of')

        # Removing M2M table for field subtype_of_completion on 'EntityType'
        db.delete_table('places_entitytype_subtype_of_completion')

        # Deleting model 'Identifier'
        db.delete_table('places_identifier')

        # Deleting model 'Entity'
        db.delete_table('places_entity')

        # Removing M2M table for field all_types on 'Entity'
        db.delete_table('places_entity_all_types')

        # Removing M2M table for field all_types_completion on 'Entity'
        db.delete_table('places_entity_all_types_completion')

        # Removing M2M table for field _identifiers on 'Entity'
        db.delete_table('places_entity__identifiers')


    models = {
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

    complete_apps = ['places']
