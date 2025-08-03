from django.contrib import admin
from .models import ConversionTask

@admin.register(ConversionTask)
class ConversionTaskAdmin(admin.ModelAdmin):
    list_display = ['id', 'ppt_filename', 'status', 'created_at', 'updated_at']
    list_filter = ['status', 'created_at']
    search_fields = ['id', 'ppt_file']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('id', 'status', 'created_at', 'updated_at')
        }),
        ('文件信息', {
            'fields': ('ppt_file', 'sketch_file')
        }),
        ('错误信息', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
    )
