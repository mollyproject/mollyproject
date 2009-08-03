from django.contrib.gis import admin


from models import Entity

class EntityAdmin(admin.GeoModelAdmin):
    list_display = ('title', 'entity_type', 'location')
    list_filter = ('entity_type',)

admin.site.register(Entity, EntityAdmin)