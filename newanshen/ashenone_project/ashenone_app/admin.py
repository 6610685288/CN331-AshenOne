from django.contrib import admin
from .models import CustomUser, LFGPost, GuideContent, Offer, ChatMessage

@admin.action(description='Suspend selected users')
def suspend_users(modeladmin, request, queryset):
    queryset.update(suspended=True)
    modeladmin.message_user(request, f"{queryset.count()} users have been suspended successfully.", level='success')

@admin.action(description='Set status to In Progress')
def set_in_progress(modeladmin, request, queryset):
    queryset.update(status='In Progress')
    modeladmin.message_user(request, f"{queryset.count()} posts set to In Progress.", level='success')

@admin.action(description='Set status to Completed')
def set_completed(modeladmin, request, queryset):
    queryset.update(status='Completed')
    modeladmin.message_user(request, f"{queryset.count()} posts set to Completed.", level='success')

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'suspended', 'is_staff', 'date_joined')
    list_editable = ('role', 'suspended',) 
    list_filter = ('role', 'suspended', 'is_staff')
    search_fields = ('username', 'email')
    actions = [suspend_users]
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Profile', {'fields': ('role', 'suspended', 'date_joined')}),
    )

@admin.register(LFGPost)
class LFGPostAdmin(admin.ModelAdmin):
    list_display = ('boss_name', 'game_name', 'user', 'platform', 'status', 'created_at')
    list_editable = ('status',)
    list_filter = ('game_name', 'platform', 'status')
    search_fields = ('boss_name', 'user__username', 'description')
    actions = [set_in_progress, set_completed, 'delete_selected']
    
@admin.register(GuideContent)
class GuideContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'game_name', 'category', 'updated_at', 'slug')
    list_filter = ('game_name', 'category')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'content_body')

@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ('post', 'offered_by', 'accepted', 'created_at')
    list_filter = ('accepted', 'created_at')
    search_fields = ('post__boss_name', 'offered_by__username')
    
@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'post', 'content', 'timestamp')
    list_filter = ('post', 'sender')
    search_fields = ('sender__username', 'content')