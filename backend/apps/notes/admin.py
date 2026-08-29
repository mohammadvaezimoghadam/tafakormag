from django.contrib import admin
from .models import Topic, Post, PostReaction, PostComment, BotTask

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'post_badge', 'created_by', 'created_at', 'telegram_bot_active', 'bale_bot_active')
    search_fields = ('name', 'description', 'post_badge')
    list_filter = ('created_at', 'telegram_bot_active', 'bale_bot_active')

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'topic', 'author', 'media_type', 'created_at')
    search_fields = ('content',)
    list_filter = ('media_type', 'created_at')

@admin.register(PostReaction)
class PostReactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'user', 'emoji', 'created_at')
    list_filter = ('emoji', 'created_at')

@admin.register(PostComment)
class PostCommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'user', 'created_at')
    search_fields = ('content',)
    list_filter = ('created_at',)

@admin.register(BotTask)
class BotTaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'action', 'platform', 'chat_id', 'processed', 'created_at')
    list_filter = ('platform', 'action', 'processed', 'created_at')
