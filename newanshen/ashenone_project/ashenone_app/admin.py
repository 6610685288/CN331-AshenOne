"""
Admin Site Configuration for ashenone_app
(ไฟล์นี้คือไฟล์ที่ถูกต้องและสมบูรณ์ที่สุด)
"""
from django.contrib import admin
from .models import CustomUser, LFGPost



@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
   
    list_display = ('username', 'email', 'role', 'suspended', 'is_staff')
   
    list_filter = ('role', 'suspended', 'is_staff')
  
    search_fields = ('username', 'email')
   
    list_editable = ('role', 'suspended',) 

    actions = ['suspend_users']

    def suspend_users(self, request, queryset):
        queryset.update(suspended=True)
    suspend_users.short_description = "Suspend selected users"

@admin.register(LFGPost)
class LFGPostAdmin(admin.ModelAdmin):
   
    list_display = ('boss_name', 'game_name', 'user', 'platform', 'status', 'created_at')
   
    list_filter = ('game_name', 'platform', 'status')
   
    search_fields = ('boss_name', 'user__username')
   
    list_editable = ('status',)

    actions = ['delete_selected']

    def delete_selected(self, request, queryset):
        queryset.delete()
    delete_selected.short_description = "Delete selected posts"