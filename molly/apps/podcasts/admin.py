from django.contrib import admin
from models import *

class PodcastCategoryNameInline(admin.TabularInline):
    model = PodcastCategoryName
    fk_name = "podcast_category"

class PodcastCategoryAdmin(admin.ModelAdmin):
    list_display = ('slug', 'name')
    inlines = [
        PodcastCategoryNameInline,
    ]

class PodcastAdmin(admin.ModelAdmin):
    list_display = ('category', 'title')
    list_filter = ('category',)

class PodcastItemAdmin(admin.ModelAdmin):
    list_display = ('podcast', 'title', 'published_date', 'duration')
    list_filter = ('podcast',)


admin.site.register(Podcast, PodcastAdmin)
admin.site.register(PodcastCategory, PodcastCategoryAdmin)
admin.site.register(PodcastItem, PodcastItemAdmin)
admin.site.register(PodcastEnclosure)
