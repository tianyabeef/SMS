from django.db import models
from django.contrib.auth.models import User
from django.utils.html import format_html

class ReferenceRange(models.Model):
    sub_number = models.CharField( '指标名称' , max_length=100 )
    sub_project = models.CharField( '碳源' , max_length=40 )
    project_start_time = models.DateField( '最大值' , blank=True , null=True )
    project_start_time = models.DateField( '最小值' , blank=True , null=True )