from django.contrib.gis import admin


from models import Entity, EntityType

class EntityAdmin(admin.GeoModelAdmin):
    list_display = ('title', 'entity_type', 'geometry')
    list_filter = ('entity_type',)

admin.site.register(Entity, EntityAdmin)
admin.site.register(EntityType)