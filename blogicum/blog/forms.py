from datetime import datetime

from django import forms
from django.contrib.auth import get_user_model

from .models import Post, Comment

User = get_user_model()


class ProfileForm(forms.ModelForm):
    """Form for profile, model - standard User model"""

    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'username',
            'email',
        )


class PostForm(forms.ModelForm):
    """Form for Post"""

    class Meta:
        model = Post
        fields = (
            'title',
            'text',
            'category',
            'location',
            'pub_date',
            'image',
        )
        widgets = {
            'pub_date': forms.DateInput(
                attrs={'type': 'date',
                       'value': datetime.now().strftime("%Y-%m-%d")
                       }
            ),
        }


class CommentForm(forms.ModelForm):
    """Form for Comment"""

    class Meta:
        model = Comment
        fields = (
            'text',
        )
