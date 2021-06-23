from django.db import models
from django.contrib.auth.models import User

from basicdata.models import Template
from basicdata.models import Agent
from basicdata.models import Product
from basicdata.models import CheckItem


class Sample( models.Model ):
    SEX_CHOICES = (
        (0 , '女性') ,
        (1 , '男性') ,
    )
    STATUS_CHOICES = (
        (0 , '完成样本收样') ,
        (1 , '开始检测') ,
    )
    sample_number = models.CharField( verbose_name = '样本编号' , max_length = 255 , unique = True )
    internal_number = models.CharField( verbose_name = '对内编号' , max_length = 255 , unique = True )
    name = models.CharField( verbose_name = '姓名' , max_length = 255 )
    email = models.EmailField( verbose_name = '邮箱' )
    receive_sample = models.CharField( verbose_name = '收样人' , max_length = 255 )
    receive_sample_date = models.DateField( verbose_name = '收样日期' , auto_now_add = True , blank = True , null = True )
    sample_source = models.ForeignKey( Agent , verbose_name = '渠道来源' , on_delete = models.CASCADE )
    set_meal = models.CharField( verbose_name = '套餐编号' , max_length = 255 )
    cost = models.DecimalField( verbose_name = '费用' , max_digits = 8 , decimal_places = 2 , null = True , blank = True )
    report_date = models.DateField( verbose_name = '预计报告日期' , auto_now = True , blank = True , null = True )
    report_template = models.ForeignKey( Template , verbose_name = '报告模板' , on_delete = models.CASCADE )
    report_template_url = models.CharField( verbose_name = '报告模板地址' , max_length = 255 )  # 选择模板是自动填写
    note = models.TextField( verbose_name = '备注' , max_length = 255 , null = True , blank = True )
    historys = models.TextField( verbose_name = '历史填写日期' , blank = True , null = True )
    is_status = models.IntegerField( verbose_name = '状态' , choices = STATUS_CHOICES , default = 0 , null = True ,
                                     blank = True )

    class Meta:
        verbose_name = '样本接收'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '%s' % self.sample_number


class Checks( models.Model ):
    STATUS_CHOICES = (
        (0 , '未完成') ,
        (1 , '完成') ,
    )

    check_name = models.CharField( verbose_name = '检测模块名称' , max_length = 255 )
    check_number = models.CharField( verbose_name = '检测模块编号' , max_length = 255 )
    sample_number = models.ForeignKey( Sample , verbose_name = '样本编号' , on_delete = models.CASCADE )
    is_status = models.IntegerField( verbose_name = '状态' , choices = STATUS_CHOICES , default = 0 , null = True ,
                                     blank = True )
    finish_date = models.DateField( verbose_name = '完成时间' , null = True , blank = True )
    writer = models.CharField( verbose_name = '检测人' , max_length = 255 , blank = True , null = True )

    class Meta:
        verbose_name = '检测项'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '%s' % self.check_name


class Progress( models.Model ):
    STATUS_CHOICES = (
        (0 , '检测中') ,
        (1 , '出报告中') ,
        (2 , '完成') ,
    )
    sample_number = models.CharField( verbose_name = '样本编号' , max_length = 255 , unique = True )
    internal_number = models.CharField( verbose_name = '对内编号' , max_length = 255 , unique = True )
    receive_sample_date = models.DateField( verbose_name = '收样日期' , null = True , blank = True )
    workforce_date = models.DateField( verbose_name = '排班日期' , null = True , blank = True )
    wjxx_testing_staff = models.CharField( verbose_name = '问卷填写人' , max_length = 255 , null = True ,
                                           blank = True )  # 记录姓名
    wjxx_testing_date = models.DateField( verbose_name = '问卷填写时间' , null = True , blank = True )
    cgzb_testing_staff = models.CharField( verbose_name = '常规指标检测人' , max_length = 255 , null = True ,
                                           blank = True )  # 记录姓名
    cgzb_testing_date = models.DateField( verbose_name = '常规指标检测时间' , null = True , blank = True )
    shzb_testing_staff = models.CharField( verbose_name = '生化指标检测人' , max_length = 255 , null = True ,
                                           blank = True )  # 记录姓名
    shzb_testing_date = models.DateField( verbose_name = '生化指标检测时间' , null = True , blank = True )
    SCFAs_testing_staff = models.CharField( verbose_name = 'SCFAs检测人' , max_length = 255 , null = True , blank = True )
    SCFAs_testing_date = models.DateField( verbose_name = 'SCFAs检测时间' , null = True , blank = True )
    qPCR_testing_staff = models.CharField( verbose_name = 'qPCR检测人' , max_length = 255 , null = True , blank = True )
    qPCR_testing_date = models.DateField( verbose_name = 'qPCR检测时间' , null = True , blank = True )
    degradation_testing_staff = models.CharField( verbose_name = '降解率产气量检测人' , max_length = 255 , null = True ,
                                                  blank = True )
    degradation_testing_date = models.DateField( verbose_name = '降解率产气量检测时间' , null = True , blank = True )
    report_testing_staff = models.CharField( verbose_name = '报告出具人' , max_length = 255 , null = True ,
                                             blank = True )
    report_testing_date = models.DateField( verbose_name = '报告时间' , null = True , blank = True )
    kuoz1_testing_staff = models.CharField( verbose_name = '扩展1检测人' , max_length = 255 , null = True , blank = True )
    kuoz1_testing_date = models.DateField( verbose_name = '扩展1检测时间' , null = True , blank = True )
    kuoz2_testing_staff = models.CharField( verbose_name = '扩展2检测人' , max_length = 255 , null = True , blank = True )
    kuoz2_testing_date = models.DateField( verbose_name = '扩展2检测时间' , null = True , blank = True )
    is_status = models.IntegerField( verbose_name = '状态' , choices = STATUS_CHOICES , default = 0 , null = True ,
                                     blank = True )
    is_wjxx = models.BooleanField( '问卷信息' , default = False )
    is_shzb = models.BooleanField( '生化指标' , default = False )
    is_cgzb = models.BooleanField( '常规指标' , default = False )
    is_qyjj = models.BooleanField( '气压与降解率' , default = False )
    is_qpcr = models.BooleanField( 'qPCR' , default = False )
    is_scfa = models.BooleanField( 'SCFAs' , default = False )
    is_kuoz1 = models.BooleanField( '扩展检测1' , default = False )
    is_kuoz2 = models.BooleanField( '扩展检测2' , default = False )

    class Meta:
        verbose_name = '样本进度'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '%s' % self.sample_number
