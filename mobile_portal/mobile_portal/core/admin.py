from django.contrib import admin
from models import *

class FeedAdmin(admin.ModelAdmin):
    list_display = ('category', 'url', 'last_fetched')
    list_filter = ('category',)

admin.site.register(Profile)
admin.site.register(Feed, FeedAdmin)
admin.site.register(FrontPageLink)
admin.site.register(Placemarks)
admin.site.register(ExternalImage)
admin.site.register(ExternalImageSized)
