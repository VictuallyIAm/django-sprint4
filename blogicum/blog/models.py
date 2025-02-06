from django.db import models
from django.contrib.auth import get_user_model

from .constants import (
    MAX_CHARACTER_LENGTH as MAX_LENGTH,
    MAX_STR_METHOD as MAX_STR
)

User = get_user_model()


class PublishedCreatedModel(models.Model):
    """Abstract model. Adds flag 'is_published'
    and time of creation to tables.
    """

    is_published = models.BooleanField(
        'Опубликовано',
        default=True,
        help_text='Снимите галочку, чтобы скрыть публикацию.'
    )
    created_at = models.DateTimeField('Добавлено', auto_now_add=True)

    class Meta:
        abstract = True


class Category(PublishedCreatedModel):
    """Model for a table 'Category', contains:
    title, description, slug.
    """

    title = models.CharField(
        verbose_name='Заголовок',
        max_length=MAX_LENGTH
    )
    description = models.TextField(verbose_name='Описание')
    slug = models.SlugField(
        verbose_name='Идентификатор',
        unique=True,
        help_text=(
            'Идентификатор страницы для URL; '
            'разрешены символы латиницы, цифры, дефис и подчёркивание.'
        )
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'
        ordering = ('slug',)

    def __str__(self):
        return self.title[:MAX_STR]


class Location(PublishedCreatedModel):
    """Model for a table 'Location', contains:
    name
    """

    name = models.CharField(
        verbose_name='Название места',
        max_length=MAX_LENGTH)

    class Meta:
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'

    def __str__(self):
        return self.name[:MAX_STR]


class Post(PublishedCreatedModel):
    """Model for a table 'Post', contains:
    title, text, pub_date,
    FK: author, location, category
    """

    title = models.CharField(verbose_name='Заголовок', max_length=MAX_LENGTH)
    text = models.TextField(verbose_name='Текст')
    image = models.ImageField('Фото', upload_to='post_images', blank=True)
    pub_date = models.DateTimeField(
        verbose_name='Дата и время публикации',
        help_text=(
            'Если установить дату и время в будущем — '
            'можно делать отложенные публикации.'
        )
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор публикации'
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posts',
        verbose_name='Местоположение'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        related_name='posts',
        verbose_name='Категория'
    )

    class Meta:
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'
        ordering = ('pub_date',)

    def __str__(self):
        return self.title[:MAX_STR]


class Comment(models.Model):

    created_at = models.DateTimeField('Добавлено', auto_now_add=True)
    text = models.TextField('Текст комментария', max_length=MAX_LENGTH)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор комментария',
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Пост комментария'
    )

    class Meta:
        ordering = ('created_at',)
