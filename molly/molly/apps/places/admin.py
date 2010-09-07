from django.contrib.gis import admin


from models import Entity, EntityType

class EntityAdmin(admin.GeoModelAdmin):
    list_display = ('title', 'absolute_url', 'primary_type')
    list_filter = ('source', 'primary_type', )

admin.site.register(Entity, EntityAdmin)
admin.site.register(EntityType)