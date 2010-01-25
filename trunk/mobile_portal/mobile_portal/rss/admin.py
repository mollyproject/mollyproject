from django.contrib import admin
from models import Feed, Item

class FeedAdmin(admin.ModelAdmin):
    list_display = ('title', 'unit', 'rss_url')
    list_filter = ('unit',)
    
class ItemAdmin(admin.ModelAdmin):
    #list_display = ('feed', 'title', 'location_name', 'location_point')
    list_filter = ('feed', )

admin.site.register(Feed, FeedAdmin)
admin.site.register(Item, ItemAdmin)