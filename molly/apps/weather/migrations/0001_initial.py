# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Weather'
        db.create_table('weather_weather', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('location_id', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('ptype', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('name', self.gf('django.db.models.fields.TextField')(null=True)),
            ('outlook', self.gf('django.db.models.fields.CharField')(max_length=3, null=True)),
            ('published_date', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('observed_date', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('modified_date', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('temperature', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('wind_direction', self.gf('django.db.models.fields.CharField')(max_length=3, null=True)),
            ('wind_speed', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('humidity', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('pressure', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
            ('pressure_state', self.gf('django.db.models.fields.CharField')(max_length=1, null=True)),
            ('visibility', self.gf('django.db.models.fields.CharField')(max_length=2, null=True)),
            ('location', self.gf('django.contrib.gis.db.models.fields.PointField')(null=True)),
            ('min_temperature', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('max_temperature', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('uv_risk', self.gf('django.db.models.fields.CharField')(max_length=1, null=True)),
            ('pollution', self.gf('django.db.models.fields.CharField')(max_length=1, null=True)),
            ('sunset', self.gf('django.db.models.fields.TimeField')(null=True)),
            ('sunrise', self.gf('django.db.models.fields.TimeField')(null=True)),
        ))
        db.send_create_signal('weather', ['Weather'])


    def backwards(self, orm):
        
        # Deleting model 'Weather'
        db.delete_table('weather_weather')


    models = {
        'weather.weather': {
            'Meta': {'object_name': 'Weather'},
            'humidity': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.contrib.gis.db.models.fields.PointField', [], {'null': 'True'}),
            'location_id': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'max_temperature': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'min_temperature': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'modified_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'observed_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'outlook': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True'}),
            'pollution': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True'}),
            'pressure': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'pressure_state': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True'}),
            'ptype': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'published_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'sunrise': ('django.db.models.fields.TimeField', [], {'null': 'True'}),
            'sunset': ('django.db.models.fields.TimeField', [], {'null': 'True'}),
            'temperature': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'uv_risk': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True'}),
            'visibility': ('django.db.models.fields.CharField', [], {'max_length': '2', 'null': 'True'}),
            'wind_direction': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True'}),
            'wind_speed': ('django.db.models.fields.IntegerField', [], {'null': 'True'})
        }
    }

    complete_apps = ['weather']
