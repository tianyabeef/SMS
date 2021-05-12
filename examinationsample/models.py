from django.db import models
from django.contrib.auth.models import User
from django.utils.html import format_html
from reporttemplate.models import Template
class SubProject(models.Model):

    sub_number = models.CharField('样本ID', max_length=100)
    sub_project = models.CharField('性别', max_length=40)
    project_start_time = models.DateField('年龄', blank=True, null=True)
    sub_project_t = models.CharField( '姓名' , max_length=40 )
    time_ext_start = models.DateField( "收样日期" , null=True  )
    # 流程时间节点
    time_ext_start = models.DateField( "报告日期" , null=True , )
    start_up_amount = models.DecimalField('身高', max_digits=12, decimal_places=2, null=True, blank=True)
    settlement_amount = models.DecimalField('体重', max_digits=12, decimal_places=2, null=True, blank=True)
    settlement_amounti = models.DecimalField( 'BMI值' , max_digits=12 , decimal_places=2 , null=True , blank=True )
    sub_project_note = models.TextField('主诉', blank=True)
    sub_project_notet = models.TextField( '过敏源' , blank=True )
    sub_project_notett = models.TextField( '既往病史' , blank=True )
    sub_project_notettt = models.TextField( '饮食习惯' , blank=True )
    sub_project_noteta = models.TextField( '近两周益生菌补充' , blank=True )
    sub_project_notetb = models.TextField( '近两周益生元补充' , blank=True )
    sub_project_notetc = models.TextField( '近1个月抗生素食用' , blank=True )
    sub_project_notetd = models.TextField( '近1个月排便情况' , blank=True )
    sub_project_notetf = models.TextField( '近1个月排气情况' , blank=True )
    sub_project_notetg = models.TextField( '近1个月胃肠道症状' , blank=True )
    sub_project_notetg = models.TextField( '渠道来源' , blank=True )
    wsub_project_notetg = models.TextField( 'word报告' , blank=True )
    sub_project_notetgg = models.TextField( 'excel报告' , blank=True )
    templatenotetgg = models.ForeignKey( Template,verbose_name='报告模板',on_delete=models.CASCADE)
    sub_project_notetggg = models.TextField( 'SCFAs检测人' , blank=True )
    time_ext_startgg = models.DateField( "SCFAs检测时间" , null=True )
    sub_project_notetggt = models.TextField( 'qPCR检测人' , blank=True )
    time_ext_startggf = models.DateField( "qPCR检测时间" , null=True )




    class Meta:
        unique_together = ('sub_number',)
        verbose_name = '样本信息'
        verbose_name_plural = verbose_name

    def __str__(self):
            return '%s' % self.sub_number

    def file_link(self):
        if self.file_to_start:
            return format_html(
            "<a href='{0}'>下载</a>" .format(self.file_to_start.url))

        else:
            return "未上传"

    file_link.allow_tags = True
    file_link.short_description = "已上传信息"

