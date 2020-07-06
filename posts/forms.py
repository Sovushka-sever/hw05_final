from django import forms
from django.utils.translation import gettext_lazy as _
from posts.models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('group', 'text', 'image',)
        labels = {
            'group': _('Сообщество'),
            'text': _('Содержание'),
            'image': _('Изображение'),
        }
        help_texts = {
            'group': _('Выберите сообщество по душе'),
            'text': _('Сообщите миру свои новости'),
            'image': _('Поделитесь фотографиями'),
        }


class CommentForm(forms.ModelForm):
    text = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
            'author': _('Автор'),
            'post': _('Публикация'),
            'text': _('Содержание'),
        }
        help_texts = {
            'text': _('Поделитесь своим мнением'),
        }
