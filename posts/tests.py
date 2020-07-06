from io import BytesIO
from PIL import Image
from django.core.cache import cache
from django.core.files.images import ImageFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from posts.forms import PostForm
from posts.models import Post, Group, Comment, Follow

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
            'post': reverse(
                'post',
                kwargs={'username': self.user, 'post_id': post.id}
            )
        }
        for url_value in list_urls.values():
            with self.subTest(url_value=url_value):
                resp = self.client.get(url_value)
                self.assertContains(resp, post.text)

    def generate_image(self):
        file = BytesIO()
        image = Image.new('RGBA', size=(100, 100), color=(155, 0, 0))
        image.save(file, 'png')
        file.name = 'test.jpg'
        file.seek(0)
        return file

    def test_profile(self):
        response = self.client.get(reverse(
            'profile',
            kwargs={'username': self.user})
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['author'], User)
        self.assertEqual(
            response.context['author'].username,
            self.user.username
        )

    def test_forms(self):
        post_text = 'TestText'
        form_data = {'text': post_text}
        form = PostForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_auth_user_can_new_publish(self):
        post_text = 'TestText'
        post = self.client.post('/new/', {'text': post_text})
        posts_new = Post.objects.filter(
            author=self.user).filter(text__exact=post_text)
        self.assertIsInstance(posts_new[0], Post)
        self.assertEqual(post.status_code, 302)
        self.assertEqual(posts_new[0].text, post_text)
        self.assertEqual(posts_new[0].author, self.user)
        self.assertEqual(posts_new.count(), 1)

    def test_not_auth_user_cant_publish(self):
        self.client.logout()
        post_text = 'TestText'
        post = self.client.post(reverse('new_post'), data={'text': post_text})
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
        post_group = Group.objects.create(
            description='test_group',
            title='test',
            slug='test_slug'
        )
        post = Post.objects.create(
            text=post_text,
            author=self.user,
            group=post_group
        )
        new_post_text = 'NewTestText'
        resp = self.client.post(
            reverse('post_edit', args=[self.user.username, post.author_id]),
            data={'text': new_post_text, 'group': post_group.id},
            follow=False
        )
        new_posts = Post.objects.filter(
            author=self.user).filter(text=new_post_text)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(new_posts.count(), 1)
        for new_post in new_posts:
            with self.subTest(new_post=new_post):
                self.assertEqual(new_post.group, post_group)
                self.check_pages_contains_post(new_post)

    def test_404_page(self):
        response = self.client.get('1')
        self.assertEqual(response.status_code, 404)

    def test_img(self):
        post_text = 'TestText'
        post_group = Group.objects.create(
            description='test_group',
            title='test',
            slug='test_slug'
        )
        file = self.generate_image()
        post = Post.objects.create(
            author=self.user,
            text=post_text,
            image=ImageFile(file, 'test.jpg'),
            group=post_group
        )
        response = self.client.get(reverse(
            'post_edit',
            kwargs={'username': self.user, 'post_id': post.id})
        )
        self.assertContains(response, "<img src=")

    def test_img_display(self):
        cache.clear()
        post_text = 'TestText'
        post_group = Group.objects.create(
            description='test_group',
            title='test',
            slug='test_slug'
        )
        file = self.generate_image()
        post = Post.objects.create(
            author=self.user,
            text=post_text,
            image=ImageFile(file, 'test.jpg'),
            group=post_group
        )
        list_urls = [
            reverse('index'),
            reverse('profile', kwargs={'username': self.user}),
            reverse('group_posts', kwargs={'slug': post_group.slug}),
            reverse('post', kwargs={'username': self.user, 'post_id': post.id})
        ]
        for url_value in list_urls:
            with self.subTest(url_value=url_value):
                resp = self.client.get(url_value)
                self.assertContains(resp, "<img")

    def test_no_graphic(self):

        file = SimpleUploadedFile(content=b'test', name='test_file.txt')
        response = self.client.post(
            reverse('new_post'),
            {
                'author': self.user,
                'text': 'the post does not contain an image',
                'image': file
            },
            follow=True
        )
        self.assertFormError(
            response,
            'form',
            field='image',
            errors=[
                'Загрузите правильное изображение. '
                'Файл, который вы загрузили, поврежден или не является изображением.'
            ]
        )

    def test_not_auth_user_cant_comment(self):
        self.client.logout()
        comment_text = 'TestText'
        post = Post.objects.create(author=self.user, text='post_text')
        comment = self.client.post(reverse(
            'add_comment',
            args=[self.user.username, post.author_id]),
            data={'text': comment_text},
        )
        comment_in_db = Comment.objects.filter(text__exact=comment_text)
        self.assertEqual(comment.status_code, 302)
        self.assertEqual(comment_in_db.count(), 0)

    def test_auth_user_can_new_comment(self):
        comment_text = 'TestText'
        post = Post.objects.create(author=self.user, text='post_text')
        self.client.post(reverse(
            'add_comment',
            args=[self.user.username, post.author_id]),
            data={'text': comment_text},
        )
        comment_in_db = Comment.objects.filter(
            author=self.user).filter(text__exact=comment_text)
        self.assertTrue(self.user.is_authenticated)
        self.assertTrue(comment_in_db.exists())

    def test_authorized_user_could_subscribe_unsubscribe(self):
        test_user = User.objects.create_user(
            username='Subscribed',
            email='rs2.s@skynet.com',
            password='qwerty123'
        )
        self.client.get(reverse(
            'profile_follow',
            kwargs={'username': test_user.username})
        )
        subscribed = Follow.objects.filter(user=self.user, author=test_user)

        self.assertEqual(subscribed.count(), 1)

        self.client.get(reverse(
            'profile_unfollow',
            kwargs={'username': test_user.username})
        )
        unsubscribed = Follow.objects.filter(user=self.user, author=test_user)

        self.assertFalse(unsubscribed.exists())

    def test_user_post_in_following_feed(self):
        post_text = "test_text"
        user_post_text = "user post text"

        test_user = User.objects.create_user(
            username='Subscribed',
            email='rs2.s@skynet.com',
            password='qwerty123'
        )
        test_client = Client()
        test_client.force_login(test_user)

        Post.objects.create(text=post_text, author=test_user)
        Post.objects.create(text=user_post_text, author=self.user)

        self.client.get(reverse(
            'profile_follow',
            kwargs={'username': test_user.username})
        )

        response = self.client.get(reverse('follow_index'))
        test_user_response = test_client.get(reverse('follow_index'))

        self.assertNotContains(test_user_response, user_post_text)
        self.assertContains(response, post_text)


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
        self.client.post(
            reverse('new_post'),
            {'author': self.user, 'text': post_text}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, post_text)
        cache.clear()
        response_new = self.client.get(reverse('index'))
        self.assertContains(response_new, post_text)
