from django.contrib import admin
from models import RSSFeed, RSSItem, ShowPredicate

class RSSFeedAdmin(admin.ModelAdmin):
    list_display = ('title', 'unit', 'rss_url')
    list_filter = ('unit',)
    
class RSSItemAdmin(admin.ModelAdmin):
    list_display = ('feed', 'title', 'location_name', 'location_point')
    list_filter = ('feed', )

class ShowPredicateAdmin(admin.ModelAdmin):
    pass

admin.site.register(RSSFeed, RSSFeedAdmin)
admin.site.register(RSSItem, RSSItemAdmin)
admin.site.register(ShowPredicate, ShowPredicateAdmin)