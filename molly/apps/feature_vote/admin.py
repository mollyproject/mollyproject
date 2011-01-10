from django.contrib import admin
from models import *


class FeatureAdmin(admin.ModelAdmin):
    list_display = ('title', 'user_name', 'user_email', 'description', 'net_votes', 'is_public', 'is_removed')
    list_filter = ('is_public', 'is_removed')

admin.site.register(Feature, FeatureAdmin)
