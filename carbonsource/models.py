from django.db import models
from django.contrib.auth.models import User
from django.utils.html import format_html

class Carbon(models.Model):
    sub_number = models.CharField( 'id' , max_length=100 )
    sub_project = models.CharField( '名称' , max_length=40 )
    project_start_time = models.DateField( '成分配比' , blank=True , null=True )