from django.contrib.gis import admin
from models import (Entity, EntityName, EntityType, EntityTypeName, EntityGroup,
                    EntityGroupName)

class EntityTypeNameInline(admin.TabularInline):
    model = EntityTypeName
    fk_name = "entity_type"


class EntityGroupNameInline(admin.TabularInline):
    model = EntityGroupName
    fk_name = "entity_group"


class EntityNameInline(admin.TabularInline):
    model = EntityName
    fk_name = "entity"


class EntityTypeAdmin(admin.ModelAdmin):
    inlines = [
        EntityTypeNameInline,
    ]


class EntityGroupAdmin(admin.ModelAdmin):
    inlines = [
        EntityGroupNameInline,
    ]


class EntityAdmin(admin.OSMGeoAdmin):
    list_display = ('title', 'absolute_url', 'primary_type')
    list_filter = ('source', 'primary_type', )
    inlines = [
        EntityNameInline,
    ]


admin.site.register(Entity, EntityAdmin)
admin.site.register(EntityType, EntityTypeAdmin)
admin.site.register(EntityGroup, EntityGroupAdmin)
