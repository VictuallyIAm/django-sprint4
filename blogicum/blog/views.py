from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count
from django.http import HttpResponseRedirect, HttpResponseForbidden, HttpResponseNotFound, Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy
from django.utils import timezone

from pages.views import csrf_failure
from .forms import ProfileForm, PostForm, CommentForm
from .models import Category, Post, Comment
from .constants import PAGE_LIMIT
from django.views.generic import DetailView, ListView, UpdateView, CreateView, DeleteView


User = get_user_model()


def post_base_query():
    return Post.objects.select_related(
        'location',
        'author',
        'category',
    ).filter(
        pub_date__lte=timezone.now(),
        is_published=True,
        category__is_published=True
    ).annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date')


class OnlyAuthorMixin(UserPassesTestMixin):

    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user


class HomePageView(ListView):
    model = Post
    template_name = 'blog/index.html'
    paginate_by = PAGE_LIMIT

    def get_queryset(self):
        return post_base_query()


class CategoryListView(ListView):
    model = Post
    template_name = 'blog/category.html'
    paginate_by = PAGE_LIMIT

    def get_queryset(self):
        if not Category.objects.get(slug=self.kwargs['category_slug']).is_published:
            raise Http404
        queryset = post_base_query(
        ).filter(
            category__slug=self.kwargs['category_slug']
        )
        return queryset


class ProfileListView(ListView):
    template_name = 'blog/profile.html'
    paginate_by = PAGE_LIMIT

    def get_queryset(self):
        if self.request.user.username == self.kwargs['slug']:
            queryset = Post.objects.select_related(
                'location',
                'author',
                'category',
            ).filter(
                author__username=self.kwargs['slug'],
            ).annotate(
                comment_count=Count('comments')
            ).order_by('-pub_date')
        else:
            queryset = post_base_query(
            ).filter(
                author__username=self.kwargs['slug']
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        username = self.kwargs['slug']
        user = User.objects.filter(username=username).first()
        if user is None:
            raise Http404
        print(f"is self anon? {self}")
        context['profile'] = user

        return context


class PostDetailView(UserPassesTestMixin, DetailView):
    model = Post
    template_name = 'blog/detail.html'

    def get_context_data(self, **kwargs):
        self.object = self.get_object()
        context = super().get_context_data(**kwargs)
        context["form"] = CommentForm()
        context["comments"] = self.object.comments.select_related('author')
        return context

    def test_func(self):
        post = self.get_object()
        if post in post_base_query():
            return True
        return post.author == self.request.user

    def handle_no_permission(self):
        return HttpResponseNotFound()


class PostCreateView(LoginRequiredMixin, CreateView):
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        user = self.request.user
        return reverse_lazy('blog:profile', kwargs={'slug': user.username})


class PostUpdateView(OnlyAuthorMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def handle_no_permission(self):
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        post = self.get_object()
        return reverse_lazy('blog:post_detail', kwargs={'pk': post.pk})


class PostDeleteView(OnlyAuthorMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'

    def handle_no_permission(self):
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy('blog:index')


class ProfileUpdateView(UpdateView):
    form_class = ProfileForm
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        return self.request.user


class CommentCreateView(LoginRequiredMixin, CreateView):
    post_obj = None
    model = Comment
    form_class = CommentForm

    # Переопределяем dispatch()
    def dispatch(self, request, *args, **kwargs):
        self.post_obj = get_object_or_404(Post, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    # Переопределяем form_valid()
    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.post_obj
        return super().form_valid(form)

    # Переопределяем get_success_url()
    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={'pk': self.post_obj.pk})


class CommentUpdateView(OnlyAuthorMixin, UpdateView):
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def get_object(self, queryset=None):
        comment = get_object_or_404(Comment, pk=self.kwargs['pk'])
        return comment

    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={'pk': self.kwargs['post_id']})


class CommentDeleteView(OnlyAuthorMixin, DeleteView):
    model = Comment
    template_name = 'blog/comment.html'

    def get_object(self, queryset=None):
        comment = get_object_or_404(Comment, pk=self.kwargs['pk'])
        return comment

    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={'pk': self.kwargs['post_id']})
