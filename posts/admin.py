from django.contrib import admin
# from django.contrib.flatpages.admin import FlatPageAdmin
# from django.contrib.flatpages.models import FlatPage
# from ckeditor.widgets import CKEditorWidget
# from django.db import models
from .models import Post, Group, Comment


class PostAdmin(admin.ModelAdmin):
    list_display = ('pk', 'text', 'pub_date', 'author', 'group')
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'


class GroupAdmin(admin.ModelAdmin):
    pass


class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'created')
    list_filter = ('created',)
    search_fields = ('text',)
    empty_value_display = '-пусто-'


# class FlatPageCustom(FlatPageAdmin):
#     formfield_overrides = {
#         models.TextField: {'widget': CKEditorWidget}
#     }
#

admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Comment, CommentAdmin)

