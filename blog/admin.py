from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import UserToken, Category, Article, Comment


@admin.register(UserToken)
class UserTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token_preview', 'created_at')
    readonly_fields = ('token', 'created_at')
    search_fields = ('user__username',)

    def token_preview(self, obj):
        return obj.token[:20] + '...'
    token_preview.short_description = 'Токен (превью)'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'articles_count', 'created_at')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

    def articles_count(self, obj):
        return obj.articles.count()
    articles_count.short_description = 'Кол-во статей'


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'is_published', 'created_at', 'updated_at')
    list_filter = ('is_published', 'category', 'created_at')
    search_fields = ('title', 'content', 'author__username')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('is_published',)
    raw_id_fields = ('author', 'category')
    date_hierarchy = 'created_at'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'article', 'content_preview', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('author__username', 'content', 'article__title')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('author', 'article')

    def content_preview(self, obj):
        return obj.content[:50] + ('...' if len(obj.content) > 50 else '')
    content_preview.short_description = 'Текст (превью)'
