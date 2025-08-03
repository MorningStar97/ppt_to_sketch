from django.db import models
from django.core.validators import FileExtensionValidator
import uuid
import os

class ConversionTask(models.Model):
    STATUS_CHOICES = [
        ('pending', '等待中'),
        ('processing', '处理中'),
        ('completed', '已完成'),
        ('failed', '失败'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ppt_file = models.FileField(
        upload_to='uploads/ppt/',
        validators=[FileExtensionValidator(allowed_extensions=['ppt', 'pptx'])],
        verbose_name='PPT文件'
    )
    sketch_file = models.FileField(
        upload_to='outputs/sketch/',
        blank=True,
        null=True,
        verbose_name='Sketch文件'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='状态'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    error_message = models.TextField(blank=True, null=True, verbose_name='错误信息')
    
    class Meta:
        verbose_name = '转换任务'
        verbose_name_plural = '转换任务'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"转换任务 {self.id} - {self.get_status_display()}"
    
    @property
    def ppt_filename(self):
        if self.ppt_file:
            return os.path.basename(self.ppt_file.name)
        return ""
    
    @property
    def sketch_filename(self):
        if self.sketch_file:
            return os.path.basename(self.sketch_file.name)
        return ""
