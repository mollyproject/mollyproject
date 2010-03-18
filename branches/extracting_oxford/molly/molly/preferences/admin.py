from django.contrib import admin

from models import Preferences

class PreferencesAdmin(admin.ModelAdmin):
    list_display = ('user', 'session_key', 'default_preferences',)

admin.site.register(Preferences, PreferencesAdmin)