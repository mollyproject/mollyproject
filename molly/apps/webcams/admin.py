from django.contrib import admin

from models import Webcam, WebcamName

class WebcamNameInline(admin.TabularInline):
    model = WebcamName
    fk_name = "webcam"


class WebcamAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'credit',)
    inlines = [
        WebcamNameInline,
    ]


admin.site.register(Webcam, WebcamAdmin)