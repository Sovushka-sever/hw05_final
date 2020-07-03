from django.contrib.auth import get_user_model
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from .forms import PostForm, CommentForm
from .models import Post, Group, Follow
from django.core.paginator import Paginator


User = get_user_model()


@cache_page(20)
def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'index.html', {'page': page, 'paginator': paginator, 'post': post_list})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.filter(group=group)
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'group.html',
        {'group': group, 'post': posts, 'page': page, 'paginator': paginator}
    )


@login_required
def new_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            user_post = form.save(commit=False)
            user_post.author = request.user
            user_post.save()
            return redirect('index')
    form = PostForm()
    return render(request, 'new_post.html', {'is_edit': False, 'form': form})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    following = False
    if request.user.is_authenticated and Follow.objects.filter(user=request.user, author=author).count() > 0:
        following = True
    return render(
        request,
        'profile.html',
        {'page': page, 'post': post_list, 'author': author, 'paginator': paginator, 'following': following}
    )


def post_view(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    author = get_object_or_404(User, username=username)
    post_list = post.author.posts.all()
    form = CommentForm()
    comment_list = post.comments.all()
    return render(request, 'post.html', {'author': author, 'post': post, 'posts': post_list, 'comments': comment_list, 'form': form})


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    if post.author != request.user:
        return redirect('post', username=username, post_id=post_id)
    form = PostForm(request.POST or None, files=request.FILES or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect('post', username=username, post_id=post_id)
    return render(request, 'new_post.html', {'is_edit': True, 'post': post, 'form': form})


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    comments = post.comments.all()
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            new_comment = form.save(commit=False)
            new_comment.post = post
            new_comment.author = request.user
            new_comment.save()
            return redirect('post', username=username, post_id=post_id)
    form = CommentForm()
    return render(request, 'comments.html', {'form': form, 'post': post, 'comments': comments})


@login_required
def follow_index(request):
    post = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, "follow.html", {'post': post, 'paginator': paginator, 'page': page})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    subscribe_count = Follow.objects.filter(author=author, user=request.user).count()
    if request.user != author and subscribe_count == 0:
        follow_object = Follow.objects.create(author=author, user=request.user)
        author.following.add(follow_object)
    return redirect('profile', username=author.username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.filter(author=author, user=request.user).delete()
    return redirect('profile', username=author.username)


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)
