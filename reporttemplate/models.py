from django.db import models
from django.contrib.auth.models import User
from django.utils.html import format_html

class Template(models.Model):
    sub_number = models.CharField( '产品名称' , max_length=100 )
    sub_project = models.CharField( '版本' , max_length=40 )
    project_start_time = models.DateField( '上传时间' , blank=True , null=True )
    sub_project_t = models.CharField( '使用次数' , max_length=40 )

    class Meta:
        unique_together = ('sub_number',)
        verbose_name = '产品名称'
        verbose_name_plural = verbose_name

    def __str__(self):
            return '%s' % self.sub_number