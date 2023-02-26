from django.contrib import admin

from .models import Tags


class TagsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'parent', 'url', 'autourl')
    list_filter = ('parent__name', )


admin.site.register(Tags, TagsAdmin)
