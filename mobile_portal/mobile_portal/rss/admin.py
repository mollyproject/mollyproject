from django.contrib import admin
from models import RSSFeed

class RSSFeedAdmin(admin.ModelAdmin):
    list_display = ('title', 'unit', 'rss_url')
    list_filter = ('unit',)
    
admin.site.register(RSSFeed, RSSFeedAdmin)