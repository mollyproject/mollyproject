from django.contrib import admin

from models import Webcam

class WeatherAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'credit',)

admin.site.register(Webcam, WeatherAdmin)