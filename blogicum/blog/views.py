from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count
from django.http import Http404, HttpResponseNotFound, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import ProfileForm, PostForm, CommentForm
from .models import Category, Post, Comment
from .constants import PAGE_LIMIT

User = get_user_model()


def post_base_query():
    """Base post query set: currently available posts with comment count"""
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
    """Deny a request from anyone but author"""

    def test_func(self):
        """If requesting user is author of content he requests - return True"""
        object = self.get_object()
        return object.author == self.request.user


class HomePageView(ListView):
    """Display home page with paginated posts"""

    model = Post
    template_name = 'blog/index.html'
    paginate_by = PAGE_LIMIT

    def get_queryset(self):
        """Get eligible for show posts"""
        return post_base_query()


class CategoryListView(ListView):
    """Display posts in chosen category"""

    model = Post
    template_name = 'blog/category.html'
    paginate_by = PAGE_LIMIT

    def get_queryset(self):
        """Get queryset. If category is not published redirect to 404"""
        if not Category.objects.get(
                slug=self.kwargs['category_slug']
        ).is_published:
            raise Http404
        queryset = post_base_query(
        ).filter(
            category__slug=self.kwargs['category_slug']
        )
        return queryset


class ProfileListView(ListView):
    """Display posts in chosen profile and profile information"""

    template_name = 'blog/profile.html'
    paginate_by = PAGE_LIMIT

    def get_queryset(self):
        """Get all posts if requesting user is owner of the profile
        or eligible for show posts otherwise
        """
        user = get_object_or_404(User, username=self.kwargs['slug'])
        if self.request.user.username == user.get_username():
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
        """Add profile data to context"""
        context = super(ProfileListView, self).get_context_data(**kwargs)
        context['profile'] = User.objects.get(username=self.kwargs['slug'])
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Edit user profile"""

    form_class = ProfileForm
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        """Get profile of requesting user"""
        return self.request.user

    def get_success_url(self):
        """On success redirect to updated profile"""
        return reverse_lazy(
            'blog:profile',
            kwargs={'slug': self.request.user.username}
        )


class PostDetailView(UserPassesTestMixin, DetailView):
    """Display post details and comments"""

    model = Post
    template_name = 'blog/detail.html'

    def get_context_data(self, **kwargs):
        """Get post details, comments and comment form"""
        self.object = self.get_object()
        context = super().get_context_data(**kwargs)
        context["form"] = CommentForm()
        context["comments"] = self.object.comments.select_related('author')
        return context

    def test_func(self):
        """Test if post is eligible for show or author is requesting user"""
        post = self.get_object()
        if post in post_base_query():
            return True
        return post.author == self.request.user

    def handle_no_permission(self):
        """Instead of 500 redirect to 404"""
        return HttpResponseNotFound()


class PostCreateView(LoginRequiredMixin, CreateView):
    """Create a new post"""

    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        """Validate form data"""
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        """On success redirect to profile page"""
        user = self.request.user
        return reverse_lazy('blog:profile', kwargs={'slug': user.username})


class PostUpdateView(OnlyAuthorMixin, UpdateView):
    """Edit an existing post"""

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def handle_no_permission(self):
        """When requested not by owner redirect back to post"""
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        """On success redirect to edited post"""
        post = self.get_object()
        return reverse_lazy('blog:post_detail', kwargs={'pk': post.pk})


class PostDeleteView(OnlyAuthorMixin, DeleteView):
    """Delete an existing post"""

    model = Post
    template_name = 'blog/create.html'

    def handle_no_permission(self):
        """Instead of error page redirects to home page"""
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        """On success redirects back to home page"""
        return reverse_lazy('blog:index')


class CommentCreateView(LoginRequiredMixin, CreateView):
    """Create a new comment on a post"""

    post_obj = None
    model = Comment
    form_class = CommentForm

    def dispatch(self, request, *args, **kwargs):
        """Check if parent post exists"""
        self.post_obj = get_object_or_404(Post, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Validate form data"""
        form.instance.author = self.request.user
        form.instance.post = self.post_obj
        return super().form_valid(form)

    def get_success_url(self):
        """On success redirect to parent post"""
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'pk': self.post_obj.pk}
        )


class CommentUpdateView(OnlyAuthorMixin, UpdateView):
    """Edit comment on a post"""

    form_class = CommentForm
    template_name = 'blog/comment.html'

    def get_object(self, queryset=None):
        comment = get_object_or_404(Comment, pk=self.kwargs['pk'])
        return comment

    def get_success_url(self):
        """On success redirect to parent post"""
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'pk': self.kwargs['post_id']}
        )


class CommentDeleteView(OnlyAuthorMixin, DeleteView):
    """Delete comment on a post"""

    model = Comment
    template_name = 'blog/comment.html'

    def get_object(self, queryset=None):
        """Get chosen comment or 404"""
        comment = get_object_or_404(Comment, pk=self.kwargs['pk'])
        return comment

    def get_success_url(self):
        """On success redirect to parent post"""
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'pk': self.kwargs['post_id']}
        )
