# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models
from django.conf import settings
from molly.utils.i18n import name_in_language

class Migration(SchemaMigration):

    def forwards(self, orm):

        # Adding model 'EntityName'
        db.create_table('places_entityname', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('entity', self.gf('django.db.models.fields.related.ForeignKey')(related_name='names', to=orm['places.Entity'])),
            ('title', self.gf('django.db.models.fields.TextField')()),
            ('language_code', self.gf('django.db.models.fields.CharField')(max_length=10)),
        ))
        db.send_create_signal('places', ['EntityName'])

        # Adding model 'EntityGroupName'
        db.create_table('places_entitygroupname', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('entity_group', self.gf('django.db.models.fields.related.ForeignKey')(related_name='names', to=orm['places.EntityGroup'])),
            ('title', self.gf('django.db.models.fields.TextField')()),
            ('language_code', self.gf('django.db.models.fields.CharField')(max_length=10)),
        ))
        db.send_create_signal('places', ['EntityGroupName'])

        # Adding model 'EntityTypeName'
        db.create_table('places_entitytypename', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('entity_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='names', to=orm['places.EntityType'])),
            ('language_code', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('verbose_name_singular', self.gf('django.db.models.fields.TextField')()),
            ('verbose_name', self.gf('django.db.models.fields.TextField')()),
            ('verbose_name_plural', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('places', ['EntityTypeName'])
        
        # Convert EntityType names to the new model
        for et in orm.EntityType.objects.all():
            et.names.create(language_code=settings.LANGUAGE_CODE,
                            verbose_name_singular = '%s %s' % (et.article, et.verbose_name),
                            verbose_name=et.verbose_name,
                            verbose_name_plural=et.verbose_name_plural,
                            )

        for eg in orm.EntityGroup.objects.all():
            eg.names.create(language_code=settings.LANGUAGE_CODE,
                            title=eg.title)

        for e in orm.Entity.objects.all():
            e.names.create(language_code=settings.LANGUAGE_CODE,
                            title=e.title)
        
        # Deleting field 'Entity.title'
        db.delete_column('places_entity', 'title')


    def backwards(self, orm):

        # Deleting model 'EntityName'
        db.delete_table('places_entityname')

        # Deleting model 'EntityGroupName'
        db.delete_table('places_entitygroupname')

        # Deleting model 'EntityTypeName'
        db.delete_table('places_entitytypename')


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
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['places.Source']"}),
            'title': ('django.db.models.fields.TextField', [], {}),
        },
        'places.entitygroup': {
            'Meta': {'object_name': 'EntityGroup'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ref_code': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['places.Source']"}),
            'title': ('django.db.models.fields.TextField', [], {})
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
            'subtype_of_completion': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'subtypes_completion'", 'blank': 'True', 'to': "orm['places.EntityType']"}),
            'article': ('django.db.models.fields.CharField', [], {'max_length': 2}),
            'verbose_name': ('django.db.models.fields.TextField', [], {}),
            'verbose_name_plural': ('django.db.models.fields.TextField', [], {})
        },
        'places.entitytypecategory': {
            'Meta': {'object_name': 'EntityTypeCategory'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {})
        },
        'places.entitytypename': {
            'Meta': {'object_name': 'EntityTypeName'},
            'verbose_name_singular': ('django.db.models.fields.TextField', [], {}),
            'entity_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'names'", 'to': "orm['places.EntityType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language_code': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
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
