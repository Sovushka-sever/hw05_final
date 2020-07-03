import io

from unittest import mock

from PIL.Image import Image
from django.core.files import File
from django.core.files.images import ImageFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms import FileField
from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from posts.forms import PostForm
from posts.models import Post, Group

User = get_user_model()


@override_settings(
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache'
        }
    }
)
class YatubeTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='Osol', email='rs.s@skynet.com', password='qwerty123'
        )
        self.client.force_login(self.user)


    def generate_photo_file(self):
        file = io.BytesIO()
        image = Image.new('RGBA', size=(100, 100), color=(155, 0, 0))
        image.save(file, 'png')
        file.name = 'test_img.png'
        file.seek(0)
        return file

    def check_pages_contains_post(self, post):
        list_urls = {
            'index': reverse('index'),
            'profile': reverse('profile', kwargs={'username': self.user}),
            'post': reverse('post', kwargs={'username': self.user, 'post_id': post.id})
        }
        for val in list_urls.values():
            resp = self.client.get(val)
            self.assertContains(resp, post.text)

    def test_profile(self):
        response = self.client.get(reverse('profile', kwargs={'username': self.user}))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['author'], User)
        self.assertEqual(response.context['author'].username, self.user.username)

    def test_forms(self):
        post_text = 'TestText'
        form_data = {'text': post_text}
        form = PostForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_auth_user_can_new_publish(self):
        post_text = 'TestText'
        post = self.client.post('/new/', {'text': post_text})
        posts_new = Post.objects.filter(author=self.user).filter(text__exact=post_text)
        self.assertIsInstance(posts_new[0], Post)
        self.assertEqual(post.status_code, 302)
        self.assertEqual(posts_new[0].text, post_text)
        self.assertEqual(posts_new[0].author, self.user)
        self.assertEqual(posts_new.count(), 1)

    def test_not_auth_user_cant_publish(self):
        self.client.logout()
        post_text = 'TestText'
        post = self.client.post('/new/', {'text': post_text})
        post_in_db = Post.objects.filter(text__exact=post_text)
        self.assertEqual(post.status_code, 302)
        self.assertEqual(post.url, '/auth/login/?next=/new/')
        self.assertEqual(post_in_db.count(), 0)

    def test_after_post_publication(self):
        post_text = 'TestText'
        post = Post.objects.create(text=post_text, author=self.user)
        self.check_pages_contains_post(post)

    def test_post_editing(self):
        post_text = 'TestText'
        post_group = Group.objects.create(description='test_group', title='test', slug='test_slug')
        post = Post.objects.create(text=post_text, author=self.user, group=post_group)
        new_post_text = 'NewTestText'
        resp = self.client.post(
            reverse('post_edit', args=[self.user.username, post.author_id]),
            data={'text': new_post_text, 'group': post_group.id},
            follow=False
        )
        new_posts = Post.objects.filter(author=self.user).filter(text=new_post_text)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(new_posts.count(), 1)
        for new_post in new_posts:
            self.assertEqual(new_post.group, post_group)
            self.check_pages_contains_post(new_post)

    # Для своего локального проекта напишите тест: возвращает ли сервер код 404, если страница не найдена.
    def test_404_page(self):
        response = self.client.get('1')
        self.assertEqual(response.status_code, 404)


    def test_img(self):
        post_text = 'TestText'
        post_group = Group.objects.create(description='test_group', title='test', slug='test_slug')
        with open('posts/ойвсе.jpg', 'rb') as fp:
            post = Post.objects.create(author=self.user, text=post_text, image=ImageFile(fp, 'image.jpg'), group=post_group)
        response = self.client.get(reverse('post_edit', kwargs={'username': self.user, 'post_id': post.id}))
        # list_urls = [
        #     # reverse('index'),
        #     # reverse('profile', kwargs={'username': self.user}),
        #     # reverse('group_posts', kwargs={'slug': post_group.slug})
        #     reverse('post', kwargs={'username': self.user, 'post_id': post.id})
        # ]
        # # for val in list_urls:
        #     # print(resp.content.decode('utf-8'))
        #     # print(resp.status_code)
        # resp = self.client.get(reverse('group_posts', kwargs={'slug': post_group.slug}))
        # self.assertContains(resp, "<img src=")
        self.assertContains(response, "<img src=")

    def test_no_graphic(self):
        post_text = 'TestText'
        with open('posts/static/not_img.txt', 'rb') as img:
            post = self.client.post("<username>/<int:post_id>/edit/",
                                    {'author': self.user, 'text': 'post with image', 'image': img})
            response = self.client.get('self.user/1/edit/')

            print(response.context['form'].errors)



        # image = SimpleUploadedFile(name='test.jpg', content=b'test', content_type='image/jpeg')
        # test = self.client.post(reverse('new_post'), {'username': self.user, 'text': post_text, 'image': image}, follow=True)
        # print(test)
        # post = Post.objects.filter(author=self.user, text=post_text)
    #     # with open('posts/static/not_img.txt', 'rb') as post_img:
    #     #     post = Post.objects.create(text=post_text, author=self.user, group=post_group, image=post_img)
    #     # self.assertTrue(post.image)
    #     # self.assertContains(response, '<img')
    #     # self.assertFormError(response=response,form=form, field=post_img, errors=errors, msg_prefix='')
    #
    # def test_cache(self):
    #     response = respon(name='index')

# проверяют страницу конкретной записи с картинкой: на странице есть тег <img>
# проверяют, что на главной странице, на странице профайла и на странице группы пост с картинкой отображается корректно, с тегом <img>
# проверяют, что срабатывает защита от загрузки файлов не-графических форматов
# Чтобы в тестах проверить загрузку файла на сервер, нужно отправить файл с помощью тестового клиента:
# >>> with open('posts/file.jpg','rb') as img:
# ...     post = self.client.post("<username>/<int:post_id>/edit/", {'author': self.user, 'text': 'post with image', 'image': img})
# Подсказка
# Для проверки защиты от загрузки «неправильных» файлов достаточно протестировать загрузку на одном «неграфическом» файле: тест покажет, срабатывает ли система защиты.
# Напишите тесты, которые проверяют работу кэша.
# Авторизованный пользователь может подписываться на других пользователей и удалять их из подписок.
# Новая запись пользователя появляется в ленте тех, кто на него подписан и не появляется в ленте тех, кто не подписан на него.
# Только авторизированный пользователь может комментировать посты.