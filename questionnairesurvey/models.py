from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from basicdata.models import Carbon , Genus
from examinationsample.models import Sample


class Quenstion( models.Model ):
    SEX_CHOICES = (
        (0 , '女性') ,
        (1 , '男性') ,
    )
    TEST_CHOICES = (
        (0 , '待录入') ,
        (2 , '完成') ,
    )
    sample_number = models.CharField( verbose_name = '样本编号' , max_length = 255 )  # 需要样本录入后才能有问卷信息
    carbon_source = models.ForeignKey( Carbon , verbose_name = '碳源' , on_delete = models.CASCADE , null = True )
    genus = models.ForeignKey( Genus , verbose_name = '菌种' , on_delete = models.CASCADE , null = True )
    carbon_source_zh = models.CharField(verbose_name = '碳源中文名称' , max_length = 255, null = True , blank = True)
    genus_zh = models.CharField( verbose_name = '菌种中文名称' , max_length = 255, null = True , blank = True )
    name = models.CharField( verbose_name = '姓名' , max_length = 255 )
    gender = models.IntegerField( verbose_name = '性别' , choices = SEX_CHOICES , null = True , blank = True )
    age = models.IntegerField( verbose_name = '年龄' , blank = True , null = True )
    age_sgement = models.CharField( verbose_name = '年龄分段' , max_length = 255 )  # 因指标参考范围会因此因素造成影响，必填项，
    province = models.CharField( verbose_name = '地域' , max_length = 255 )  # 因指标参考范围会因此因素造成影响，必填项，
    height = models.DecimalField( verbose_name = '身高' , max_digits = 5 , decimal_places = 2 , null = True ,
                                  blank = True )
    weight = models.DecimalField( verbose_name = '体重' , max_digits = 5 , decimal_places = 2 , null = True ,
                                  blank = True )
    waistline = models.DecimalField( verbose_name = '腰围' , max_digits = 5 , decimal_places = 2 , null = True ,
                                     blank = True )
    bmi_value = models.DecimalField( verbose_name = 'BMI值' , max_digits = 6 , decimal_places = 2 , null = True ,
                                     blank = True )
    phone = PhoneNumberField( verbose_name = '电话' , null = True , blank = True , help_text = 'Contact phone number' )
    email = models.EmailField( verbose_name = "邮箱" )
    complaint = models.CharField( verbose_name = '主诉' , max_length = 255 , null = True , blank = True )
    condition = models.CharField( verbose_name = '近1个月排便情况' , max_length = 255 , null = True , blank = True )
    exhaust = models.CharField( verbose_name = '近1个月排气情况' , max_length = 255 , null = True , blank = True )
    smoke = models.CharField( verbose_name = '吸烟饮酒' , max_length = 255 , null = True , blank = True )
    antibiotic_consumption = models.CharField( verbose_name = '近1个月抗生素食用' , max_length = 255 , null = True ,
                                               blank = True )
    probiotic_supplements = models.CharField( verbose_name = '近两周益生菌补充' , max_length = 255 , null = True ,
                                              blank = True )
    prebiotics_supplement = models.CharField( verbose_name = '近两周益生元补充' , max_length = 255 , null = True ,
                                              blank = True )
    dietary_habit = models.CharField( verbose_name = '饮食习惯' , max_length = 255 , null = True , blank = True )
    allergen = models.CharField( verbose_name = '过敏源' , max_length = 255 , null = True , blank = True )
    anamnesis = models.CharField( verbose_name = '既往病史' , max_length = 255 , null = True , blank = True )
    triglyceride = models.CharField( verbose_name = '甘油三酯' , max_length = 255 , null = True , blank = True )
    cholesterol = models.CharField( verbose_name = '总胆固醇' , max_length = 255 , null = True , blank = True )
    hdl = models.CharField( verbose_name = 'HDL-C' , max_length = 255 , null = True , blank = True )
    blood_glucose = models.CharField( verbose_name = '餐后血糖' , max_length = 255 , null = True , blank = True )
    blood_pressure = models.CharField( verbose_name = '血压' , max_length = 255 , null = True , blank = True )
    trioxypurine = models.CharField( verbose_name = '尿酸' , max_length = 255 , null = True , blank = True )
    is_status = models.IntegerField( verbose_name = '状态' , choices = TEST_CHOICES , default = 0 , null = True ,
                                     blank = True )  # 完成状态就在样本进度表中更新状态

    class Meta:
        verbose_name = '问卷调查信息'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '%s' % self.sample_number
