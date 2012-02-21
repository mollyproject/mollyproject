from django.contrib import admin
from models import Feed, Item

class FeedAdmin(admin.ModelAdmin):
    list_display = ('title', 'entity', 'rss_url')
    # excluded because not used and causes performance
    # problems when you have 47622 entities...
    exclude = ('entity',)

class ItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'last_modified', 'feed')
    list_filter = ('feed', 'last_modified')

admin.site.register(Feed, FeedAdmin)
admin.site.register(Item, ItemAdmin)
