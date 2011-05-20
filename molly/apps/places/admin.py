from django.contrib.gis import admin
from models import Entity, EntityType, EntityGroup


class EntityAdmin(admin.OSMGeoAdmin):
    list_display = ('title', 'absolute_url', 'primary_type')
    list_filter = ('source', 'primary_type', )

admin.site.register(Entity, EntityAdmin)
admin.site.register(EntityType)
admin.site.register(EntityGroup)
