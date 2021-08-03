from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.core.validators import MinValueValidator , MaxValueValidator


class FormulaGroup( models.Model ):
    name = models.CharField( verbose_name = "公式类别" , max_length = 255 )
    number = models.CharField( verbose_name = "公式类别编号" , max_length = 255 )

    class Meta:
        verbose_name = '计算公式类别'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '%s' % self.name


class CTformula( models.Model ):
    number = models.CharField( verbose_name = "公式唯一编号" , max_length = 255 , unique = True )
    formula_group = models.ForeignKey( FormulaGroup , verbose_name = '公式类别' , on_delete = models.CASCADE )
    formula_name = models.CharField( verbose_name = '公式名称' , max_length = 255 , blank = True , null = True )
    formula_content = models.CharField( verbose_name = '计算公式' , max_length = 255 )
    tax_name = models.CharField( verbose_name = '菌种名称' , max_length = 255 )
    version_num = models.IntegerField( verbose_name = '版本号' , default = 1 ,
                                       validators = [MinValueValidator( 0 ) , MaxValueValidator( 2000 )] )
    example_data = models.FloatField( verbose_name = "输入示例" )
    result_data = models.FloatField( verbose_name = "输出结果" )
    create_date = models.DateField( verbose_name = '创建时间' , auto_now_add = True )
    historys = models.TextField( verbose_name = "历史填写版本" , blank = True , null = True )
    writer = models.CharField( verbose_name = "创建人" , max_length = 255 , blank = True , null = True )
    note = models.TextField( verbose_name = '备注' , max_length = 255 , blank = True , null = True )

    class Meta:
        verbose_name = '计算公式'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '%s' % self.number


# Create your models here.
class Genus( models.Model ):
    taxid = models.IntegerField( verbose_name = 'taxid' , unique = True )
    china_name = models.CharField( verbose_name = '中文名称' , max_length = 255 )
    english_name = models.CharField( verbose_name = '英文名称' , max_length = 255 , unique = True )
    create_date = models.DateField( verbose_name = '创建时间' , auto_now = True )
    historys = models.TextField( verbose_name = "历史填写日期" , blank = True , null = True )
    writer = models.CharField( verbose_name = "创建人" , max_length = 255 , blank = True , null = True )
    note = models.TextField( verbose_name = '备注' , max_length = 255 , blank = True , null = True )

    class Meta:
        verbose_name = '菌种信息'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '%s' % self.english_name


# Create your models here.
class Agent( models.Model ):
    number = models.CharField( verbose_name = '渠道编号' , max_length = 255 , unique = True )
    name = models.CharField( verbose_name = '渠道名称' , max_length = 255 , null = True , blank = True )
    responsible_user = models.ForeignKey( User , verbose_name = '负责人姓名' , on_delete = models.CASCADE )
    phone = PhoneNumberField( verbose_name = '联系电话' , null = True , blank = True , help_text = 'Contact phone number' )
    email = models.EmailField( verbose_name = '邮箱' )
    area = models.CharField( verbose_name = '负责区域' , max_length = 255 , default = '' , null = True , blank = True )
    create_date = models.DateField( verbose_name = '创建时间' , auto_now = True )
    historys = models.TextField( verbose_name = "历史填写日期" , blank = True , null = True )
    writer = models.CharField( verbose_name = "创建人" , max_length = 255 , blank = True , null = True )
    note = models.TextField( verbose_name = '备注' , max_length = 255 , blank = True , null = True )

    class Meta:
        verbose_name = '渠道信息'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '%s' % self.name


class Product( models.Model ):
    number = models.CharField( verbose_name = '套餐编号' , max_length = 255 , unique = True )
    name = models.CharField( verbose_name = '套餐名称' , max_length = 255 , unique = True )
    price = models.DecimalField( verbose_name = '套餐价格' , max_digits = 8 , decimal_places = 2 , null = True ,
                                 blank = True )
    check_content = models.CharField( verbose_name = '检测模块' , max_length = 255 )
    create_date = models.DateField( verbose_name = '创建时间' , auto_now = True )
    days = models.IntegerField( verbose_name = '周期天数' , default = 1 ,
                                validators = [MinValueValidator( 0 ) , MaxValueValidator( 200 )] )
    historys = models.TextField( verbose_name = "历史填写日期" , blank = True , null = True )
    writer = models.CharField( verbose_name = "创建人" , max_length = 255 , blank = True , null = True )
    note = models.TextField( verbose_name = '备注' , max_length = 255 , blank = True , null = True )

    class Meta:
        verbose_name = '套餐信息'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '%s' % self.number


class Carbon( models.Model ):
    cid = models.CharField( verbose_name = '碳源编号' , max_length = 255 , unique = True )
    name = models.CharField( verbose_name = '名称' , max_length = 255 , unique = True )  # qpcr数据导入是根据中文名称进行创建对象
    english_name = models.CharField( verbose_name = '英文名称' , max_length = 255 , unique = True )  # 在渲染word报告时使用
    ratio = models.CharField( verbose_name = '碳源配比' , max_length = 255 )
    create_date = models.DateField( verbose_name = '创建时间' , auto_now_add = True )
    historys = models.TextField( verbose_name = "历史填写日期" , blank = True , null = True )
    writer = models.CharField( verbose_name = "创建人" , max_length = 255 , blank = True , null = True )
    note = models.TextField( verbose_name = '备注' , max_length = 255 , blank = True , null = True )

    class Meta:
        verbose_name = '碳源信息'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '%s' % self.name


# 最大值0，最小值0  为阴性；  最大值1，最小值1  为阳性
class ReferenceRange( models.Model ):
    L_CHOICES = (
        (0 , '数值') ,
        (1 , '科学记数法') ,
        (2 , '百分数') ,
        (3 , '阴阳') ,
    )
    index_name = models.CharField( verbose_name = '指标名称' , max_length = 255 )  # 实验结果就是通过这个字段进行匹配查询的
    carbon_source = models.ForeignKey( Carbon , verbose_name = '碳源' , on_delete = models.CASCADE )
    tax_name = models.CharField( verbose_name = '菌种名称' , max_length = 255 )
    version_num = models.IntegerField( verbose_name = '版本号' , default = 1 ,
                                       validators = [MinValueValidator( 0 ) , MaxValueValidator( 2000 )] )
    reference_range = models.CharField( verbose_name = '参考值' , max_length = 255 , null = True ,
                                        blank = True )
    layout = models.IntegerField( verbose_name = '报告显示形式' , choices = L_CHOICES , default = 0 , null = True ,
                                  blank = True )
    point = models.IntegerField( verbose_name = '小数点位数' , default = 2 , null = True , blank = True ,
                                 validators = [MinValueValidator( 0 ) , MaxValueValidator( 100 )] )
    max_value = models.FloatField( verbose_name = '最大值' , null = True , blank = True )
    min_value = models.FloatField( verbose_name = '最小值' , null = True , blank = True )
    create_date = models.DateField( verbose_name = '创建时间' , auto_now_add = True )
    historys = models.TextField( verbose_name = "历史填写版本" , blank = True , null = True )
    writer = models.CharField( verbose_name = "创建人" , max_length = 255 , blank = True , null = True )
    note = models.TextField( verbose_name = '备注' , max_length = 255 , blank = True , null = True )

    class Meta:
        verbose_name = '参考范围'
        verbose_name_plural = verbose_name
        unique_together = ('index_name' , 'carbon_source' , 'tax_name' , 'version_num')

    def __str__(self):
        return '%s' % self.index_name


class RiskReferenceRange( models.Model ):
    index_name = models.CharField( verbose_name = '风险名称' , max_length = 255 )  # 实验结果就是通过这个字段进行匹配查询的
    carbon_source = models.ForeignKey( Carbon , verbose_name = '碳源' , on_delete = models.CASCADE )
    version_num = models.IntegerField( verbose_name = '版本号' , default = 1 ,
                                       validators = [MinValueValidator( 0 ) , MaxValueValidator( 2000 )] )
    reference_range1 = models.CharField( verbose_name = '低风险参考值' , max_length = 255 , null = True ,
                                         blank = True )
    reference_range2 = models.CharField( verbose_name = '注意参考值' , max_length = 255 , null = True ,
                                         blank = True )
    reference_range3 = models.CharField( verbose_name = '中风险参考值' , max_length = 255 , null = True ,
                                         blank = True )
    reference_range4 = models.CharField( verbose_name = '高风险参考值' , max_length = 255 , null = True ,
                                         blank = True )
    create_date = models.DateField( verbose_name = '创建时间' , auto_now_add = True )
    historys = models.TextField( verbose_name = "历史填写版本" , blank = True , null = True )
    writer = models.CharField( verbose_name = "创建人" , max_length = 255 , blank = True , null = True )
    note = models.TextField( verbose_name = '备注' , max_length = 255 , blank = True , null = True )

    class Meta:
        verbose_name = '风险参考范围'
        verbose_name_plural = verbose_name
        unique_together = ('index_name' , 'version_num')

    def __str__(self):
        return '%s' % self.index_name


class RiskItem( models.Model ):
    risk_type = models.CharField( verbose_name = '风险大类名称' , max_length = 255 )
    check_type = models.CharField( verbose_name = '检测大类名称' , max_length = 255 )
    risk_type_number = models.CharField( verbose_name = '风险大类' , max_length = 255 )
    check_type_number = models.CharField( verbose_name = '检测大类' , max_length = 255 )
    index_name = models.CharField( verbose_name = '指标名称' , max_length = 255 )
    create_date = models.DateField( verbose_name = '创建时间' , auto_now_add = True )
    historys = models.TextField( verbose_name = "历史填写版本" , blank = True , null = True )
    writer = models.CharField( verbose_name = "创建人" , max_length = 255 , blank = True , null = True )
    note = models.TextField( verbose_name = '备注' , max_length = 255 , blank = True , null = True )

    class Meta:
        verbose_name = '风险模块'
        verbose_name_plural = verbose_name
        unique_together = ('risk_type' , 'check_type')

    def __str__(self):
        return '%s' % self.index_name


class RiskItemDefault( models.Model ):
    risk_type = models.CharField( verbose_name = '风险大类名称' , max_length = 255 )
    risk_type_number = models.CharField( verbose_name = '风险大类' , max_length = 255 )
    index_name = models.CharField( verbose_name = '指标名称' , max_length = 255 )
    risk_name = models.CharField( verbose_name = '风险名称' , max_length = 255 )
    low_value = models.FloatField( verbose_name = "偏低默认值" )
    high_value = models.FloatField( verbose_name = "偏高默认值" )
    create_date = models.DateField( verbose_name = '创建时间' , auto_now_add = True )
    historys = models.TextField( verbose_name = "历史填写版本" , blank = True , null = True )
    writer = models.CharField( verbose_name = "创建人" , max_length = 255 , blank = True , null = True )
    note = models.TextField( verbose_name = '备注' , max_length = 255 , blank = True , null = True )

    class Meta:
        verbose_name = '风险指标默认值'
        verbose_name_plural = verbose_name
        unique_together = ('risk_type_number' , 'index_name' , 'risk_name')

    def __str__(self):
        return '%s' % self.index_name


class Template( models.Model ):
    product_name = models.CharField( verbose_name = '模板名称' , max_length = 100 , unique = True )
    version_num = models.IntegerField( verbose_name = '版本号' , default = 1 ,
                                       validators = [MinValueValidator( 0 ) , MaxValueValidator( 2000 )] )
    upload_time = models.DateField( verbose_name = '上传时间' , blank = True , null = True , auto_now = True )
    use_count = models.IntegerField( verbose_name = '使用次数' , default = 0 )
    file_template = models.FileField( verbose_name = '模板报告' , upload_to = "uploads/template/%Y/%m" , null = True ,
                                      blank = True )
    create_date = models.DateField( verbose_name = '创建时间' , auto_now_add = True )
    historys = models.TextField( verbose_name = "历史填写日期" , blank = True , null = True )
    writer = models.CharField( verbose_name = "创建人" , max_length = 255 , blank = True , null = True )
    note = models.TextField( verbose_name = '备注' , max_length = 255 , blank = True , null = True )

    class Meta:
        verbose_name = '报告模板'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '%s' % self.product_name

    def file_link(self):
        if self.file_template:
            return format_html(
                "<a href='{0}'>下载</a>".format( self.file_template.url ) )

        else:
            return "未上传"


class CheckType( models.Model ):
    number = models.CharField( verbose_name = '检测大类编号' , max_length = 255 , unique = True )
    name = models.CharField( verbose_name = '检测大类名称' , max_length = 255 , unique = True )
    create_date = models.DateField( verbose_name = '创建时间' , auto_now = True )
    historys = models.TextField( verbose_name = "历史填写日期" , blank = True , null = True )
    writer = models.CharField( verbose_name = "创建人" , max_length = 255 , blank = True , null = True )
    note = models.TextField( verbose_name = '备注' , max_length = 255 , blank = True , null = True )

    class Meta:
        verbose_name = '检测大类'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '%s' % self.name


class CheckItem( models.Model ):
    number = models.CharField( verbose_name = '检测模块编号' , max_length = 255 , unique = True )
    check_name = models.CharField( verbose_name = '检测模块名称' , max_length = 255 , unique = True )
    type = models.ForeignKey( CheckType , verbose_name = '检测大类' , on_delete = models.CASCADE )
    carbon_source = models.CharField( verbose_name = '碳源' , max_length = 255 )
    genus = models.CharField( verbose_name = '菌种' , max_length = 255 )
    create_date = models.DateField( verbose_name = '创建时间' , auto_now = True )
    historys = models.TextField( verbose_name = "历史填写日期" , blank = True , null = True )
    writer = models.CharField( verbose_name = "创建人" , max_length = 255 , blank = True , null = True )
    note = models.TextField( verbose_name = '备注' , max_length = 255 , blank = True , null = True )

    class Meta:
        verbose_name = '检测模块'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '%s' % self.check_name


class Age( models.Model ):
    name = models.CharField( verbose_name = '年龄分段' , max_length = 255 , unique = True )
    age_range = models.CharField( verbose_name = "年龄范围" , max_length = 255 , blank = True , null = True )
    create_date = models.DateField( verbose_name = '创建时间' , auto_now = True )
    historys = models.TextField( verbose_name = "历史填写日期" , blank = True , null = True )
    writer = models.CharField( verbose_name = "创建人" , max_length = 255 , blank = True , null = True )
    note = models.TextField( verbose_name = '备注' , max_length = 255 , blank = True , null = True )

    class Meta:
        verbose_name = '年龄段'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '%s' % self.name


class Province( models.Model ):
    name = models.CharField( verbose_name = '地域' , max_length = 255 , unique = True )
    create_date = models.DateField( verbose_name = '创建时间' , auto_now = True )
    historys = models.TextField( verbose_name = "历史填写日期" , blank = True , null = True )
    writer = models.CharField( verbose_name = "创建人" , max_length = 255 , blank = True , null = True )
    note = models.TextField( verbose_name = '备注' , max_length = 255 , blank = True , null = True )

    class Meta:
        verbose_name = '地域'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '%s' % self.name


# Qpcr 检出限
class DetectionLimit( models.Model ):
    carbon_source = models.ForeignKey( Carbon , verbose_name = '碳源' , on_delete = models.CASCADE )
    tax_name = models.CharField( verbose_name = '菌种英文名称' , max_length = 255 , unique = True )
    min_layout = models.CharField( verbose_name = '最小值未检出显示形式' , max_length = 255 , null = True , blank = True )
    min_value = models.FloatField( verbose_name = '最小值' , null = True , blank = True )
    max_layout = models.CharField( verbose_name = '最大值未检出显示形式' , max_length = 255 , null = True , blank = True )
    max_value = models.FloatField( verbose_name = '最大值' , null = True , blank = True )
    create_date = models.DateField( verbose_name = '创建时间' , auto_now_add = True )
    historys = models.TextField( verbose_name = "历史填写版本" , blank = True , null = True )
    writer = models.CharField( verbose_name = "创建人" , max_length = 255 , blank = True , null = True )
    note = models.TextField( verbose_name = '备注' , max_length = 255 , blank = True , null = True )

    class Meta:
        verbose_name = 'qpcr检出限'
        verbose_name_plural = verbose_name
        unique_together = ('carbon_source' , 'tax_name')

    def __str__(self):
        return '%s' % self.tax_name
