from io import BytesIO

from PIL import Image
from django.core.cache import cache
from django.core.files.images import ImageFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from posts.forms import PostForm
from posts.models import Post, Group, Comment

User = get_user_model()


class YatubeTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='Osol', email='rs.s@skynet.com', password='qwerty123'
        )
        self.client.force_login(self.user)

    def check_pages_contains_post(self, post):
        list_urls = {
            'index': reverse('index'),
            'profile': reverse('profile', kwargs={'username': self.user}),
            'post': reverse('post', kwargs={'username': self.user, 'post_id': post.id})
        }
        for val in list_urls.values():
            resp = self.client.get(val)
            self.assertContains(resp, post.text)

    def generate_image(self):
        file = BytesIO()
        image = Image.new('RGBA', size=(100, 100), color=(155, 0, 0))
        image.save(file, 'png')
        file.name = 'test.jpg'
        file.seek(0)
        return file

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
        cache.clear()
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

    def test_404_page(self):
        response = self.client.get('1')
        self.assertEqual(response.status_code, 404)

    def test_img(self):
        post_text = 'TestText'
        post_group = Group.objects.create(description='test_group', title='test', slug='test_slug')

        file = self.generate_image()
        post = Post.objects.create(author=self.user, text=post_text, image=ImageFile(file, 'test.jpg'), group=post_group)

        response = self.client.get(reverse('post_edit', kwargs={'username': self.user, 'post_id': post.id}))
        self.assertContains(response, "<img src=")

    def test_img_display(self):
        cache.clear()
        post_text = 'TestText'
        post_group = Group.objects.create(description='test_group', title='test', slug='test_slug')
        file = self.generate_image()
        post = Post.objects.create(author=self.user, text=post_text, image=ImageFile(file, 'test.jpg'),
                                   group=post_group)
        list_urls = [
            reverse('index'),
            reverse('profile', kwargs={'username': self.user}),
            reverse('group_posts', kwargs={'slug': post_group.slug}),
            reverse('post', kwargs={'username': self.user, 'post_id': post.id})
        ]
        for val in list_urls:
            resp = self.client.get(val)
            self.assertContains(resp, "<img")

    def test_no_graphic(self):
        file = SimpleUploadedFile(content=b'test', name='test_file.txt')
        post = self.client.post('/new/',
                                {'author': self.user, 'text': 'the post does not contain an image', 'image': file})
        form = PostForm(post)
        self.assertFalse(form.is_valid())

    def test_not_auth_user_cant_comment(self):
        self.client.logout()
        comment_text = 'TestText'
        post = Post.objects.create(author=self.user, text='post_text')
        comment = self.client.post(reverse('add_comment', args=[self.user.username, post.author_id]), data={'text': comment_text}, )
        comment_in_db = Comment.objects.filter(text__exact=comment_text)
        self.assertEqual(comment.status_code, 302)
        self.assertEqual(comment_in_db.count(), 0)


class YatubeTestCache(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='Osol', email='rs.s@skynet.com', password='qwerty123'
        )
        self.client.force_login(self.user)

    def test_cache(self):
        response = self.client.get(reverse('index'))
        post_text = 'TestText'
        post = self.client.post('/new/', {'author': self.user, 'text': post_text})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, post_text)
        cache.clear()
        response_new = self.client.get(reverse('index'))
        self.assertContains(response_new, post_text)


# Авторизованный пользователь может подписываться на других пользователей и удалять их из подписок.
# Новая запись пользователя появляется в ленте тех, кто на него подписан и не появляется в ленте тех, кто не подписан на него.
