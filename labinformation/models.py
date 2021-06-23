from django.db import models
from examinationsample.models import Sample
from basicdata.models import Carbon
from basicdata.models import Genus


class ConventionalIndex( models.Model ):
    STATUS_CHOICES = (
        (0 , '偏高') ,
        (1 , '正常') ,
        (2 , '偏低') ,
    )
    TEST_CHOICES = (
        (0 , '待检测') ,
        (2 , '完成') ,
    )
    RESULT_CHOICES = (
        (0 , '阴性') ,
        (1 , '阳性') ,
    )
    sample_number = models.CharField( verbose_name = '样本编号' , max_length = 255 )
    carbon_source = models.ForeignKey( Carbon , verbose_name = '碳源' , on_delete = models.CASCADE , null = True )
    genus = models.ForeignKey( Genus , verbose_name = '菌种' , on_delete = models.CASCADE , null = True )
    carbon_source_zh = models.CharField( verbose_name = '碳源中文名称' , max_length = 255 , null = True , blank = True )
    genus_zh = models.CharField( verbose_name = '菌种中文名称' , max_length = 255 , null = True , blank = True )
    occult_Tf = models.IntegerField( verbose_name = '潜血双联-Tf' , choices = RESULT_CHOICES , default = 0 , null = True ,
                                     blank = True )
    occult_Tf_status = models.IntegerField( verbose_name = '潜血双联-Tf状态' , choices = STATUS_CHOICES , null = True ,
                                            blank = True )
    occult_Tf_reference_range = models.CharField( verbose_name = '参考值' , max_length = 255 , null = True , blank = True )
    occult_Hb = models.IntegerField( verbose_name = '潜血双联-Hb' , choices = RESULT_CHOICES , default = 0 , null = True ,
                                     blank = True )
    occult_Hb_status = models.IntegerField( verbose_name = '潜血双联-Hb状态' , choices = STATUS_CHOICES , null = True ,
                                            blank = True )
    occult_Hb_reference_range = models.CharField( verbose_name = '参考值' , max_length = 255 , null = True , blank = True )
    hp = models.IntegerField( verbose_name = '幽门螺旋杆菌抗原' , choices = RESULT_CHOICES , default = 0 , null = True ,
                              blank = True )
    hp_status = models.IntegerField( verbose_name = '幽门螺旋杆菌抗原状态' , choices = STATUS_CHOICES , null = True ,
                                     blank = True )
    hp_reference_range = models.CharField( verbose_name = '参考值' , max_length = 255 , null = True , blank = True )
    calprotectin = models.IntegerField( verbose_name = '钙卫蛋白' , choices = RESULT_CHOICES , default = 0 , null = True ,
                                        blank = True )
    calprotectin_status = models.IntegerField( verbose_name = '钙卫蛋白状态' , choices = STATUS_CHOICES , null = True ,
                                               blank = True )
    calprotectin_reference_range = models.CharField( verbose_name = '参考值' , max_length = 255 , null = True ,
                                                     blank = True )
    ph_value = models.DecimalField( verbose_name = 'PH值' , max_digits = 12 , decimal_places = 4 , null = True ,
                                    blank = True )
    ph_value_status = models.IntegerField( verbose_name = 'PH值状态' , choices = STATUS_CHOICES , null = True ,
                                           blank = True )
    ph_value_reference_range = models.CharField( verbose_name = '参考值' , max_length = 255 , null = True , blank = True )
    sample_type = models.CharField( verbose_name = '样本类型' , max_length = 255 , null = True , blank = True )
    colour = models.CharField( verbose_name = '颜色' , max_length = 255 , null = True , blank = True )
    is_status = models.IntegerField( verbose_name = '状态' , choices = TEST_CHOICES , default = 0 , null = True ,
                                     blank = True )

    class Meta:
        verbose_name = '常规指标'
        verbose_name_plural = verbose_name
        unique_together = ('sample_number' , 'carbon_source' , 'genus')

    def __str__(self):
        return '%s' % self.sample_number


# Create your models here.
class BioChemicalIndexes( models.Model ):
    STATUS_CHOICES = (
        (0 , '偏高') ,
        (1 , '正常') ,
        (2 , '偏低') ,
    )
    TEST_CHOICES = (
        (0 , '待检测') ,
        (2 , '完成') ,
    )
    sample_number = models.CharField( verbose_name = '样本编号' , max_length = 255 )
    carbon_source = models.ForeignKey( Carbon , verbose_name = '碳源' , on_delete = models.CASCADE , null = True )
    genus = models.ForeignKey( Genus , verbose_name = '菌种' , on_delete = models.CASCADE , null = True )
    carbon_source_zh = models.CharField( verbose_name = '碳源中文名称' , max_length = 255 , null = True , blank = True )
    genus_zh = models.CharField( verbose_name = '菌种中文名称' , max_length = 255 , null = True , blank = True )
    fecal_nitrogen = models.DecimalField( verbose_name = '粪氨' , max_digits = 12 , decimal_places = 4 , null = True ,
                                          blank = True )
    fecal_nitrogen_status = models.IntegerField( verbose_name = '粪氨状态' , choices = STATUS_CHOICES , null = True ,
                                                 blank = True )
    fecal_nitrogen_reference_range = models.CharField( verbose_name = '参考值' , max_length = 255 , null = True ,
                                                       blank = True )
    bile_acid = models.DecimalField( verbose_name = '胆汁酸' , max_digits = 12 , decimal_places = 4 , null = True ,
                                     blank = True )
    bile_acid_status = models.IntegerField( verbose_name = '胆汁酸状态' , choices = STATUS_CHOICES , null = True ,
                                            blank = True )
    bile_acid_reference_range = models.CharField( verbose_name = '参考值' , max_length = 255 , null = True , blank = True )
    is_status = models.IntegerField( verbose_name = '状态' , choices = TEST_CHOICES , default = 0 , null = True ,
                                     blank = True )

    class Meta:
        verbose_name = '生化指标'
        verbose_name_plural = verbose_name
        unique_together = ('sample_number' , 'carbon_source' , 'genus')

    def __str__(self):
        return '%s' % self.sample_number


# Create your models here.
class QpcrIndexes( models.Model ):
    sample_number = models.CharField( verbose_name = '样本编号' , max_length = 255 )
    carbon_source = models.ForeignKey( Carbon , verbose_name = '碳源' , on_delete = models.CASCADE , null = True )
    genus = models.ForeignKey( Genus , verbose_name = '菌种' , on_delete = models.CASCADE , null = True )
    carbon_source_zh = models.CharField( verbose_name = '碳源中文名称' , max_length = 255 , null = True , blank = True )
    genus_zh = models.CharField( verbose_name = '菌种中文名称' , max_length = 255 , null = True , blank = True )

    STATUS_CHOICES = (
        (0 , '偏高') ,
        (1 , '正常') ,
        (2 , '偏低') ,
    )
    TEST_CHOICES = (
        (0 , '待检测') ,
        (2 , '完成') ,
    )
    ct = models.DecimalField( verbose_name = 'CT' , max_digits = 12 , decimal_places = 4 , null = True ,
                              blank = True )
    concentration = models.FloatField( verbose_name = 'Qpcr浓度' , null = True , blank = True )
    concentration_reference_range = models.CharField( verbose_name = '参考值' , max_length = 255 , null = True ,
                                                      blank = True )
    concentration_status = models.IntegerField( verbose_name = '浓度状态' , choices = STATUS_CHOICES , null = True ,
                                                blank = True )
    formula_number = models.CharField( verbose_name = "公式唯一编号" , max_length = 255 )
    is_status = models.IntegerField( verbose_name = '状态' , choices = TEST_CHOICES , default = 0 , null = True ,
                                     blank = True )

    class Meta:
        verbose_name = 'qPCR指标'
        verbose_name_plural = verbose_name
        unique_together = ('sample_number' , 'carbon_source' , 'genus')

    def __str__(self):
        return '%s' % self.sample_number


class DegradationIndexes( models.Model ):
    STATUS_CHOICES = (
        (0 , '偏高') ,
        (1 , '正常') ,
        (2 , '偏低') ,
    )
    TEST_CHOICES = (
        (0 , '待检测') ,
        (2 , '完成') ,
    )
    sample_number = models.CharField( verbose_name = '样本编号' , max_length = 255 )
    carbon_source = models.ForeignKey( Carbon , verbose_name = '碳源' , on_delete = models.CASCADE , null = True )
    genus = models.ForeignKey( Genus , verbose_name = '菌种' , on_delete = models.CASCADE , null = True )
    carbon_source_zh = models.CharField( verbose_name = '碳源中文名称' , max_length = 255 , null = True , blank = True )
    genus_zh = models.CharField( verbose_name = '菌种中文名称' , max_length = 255 , null = True , blank = True )
    degradation = models.DecimalField( verbose_name = '降解率' , max_digits = 12 , decimal_places = 4 , null = True ,
                                       blank = True )
    degradation_status = models.IntegerField( verbose_name = '降解率状态' , choices = STATUS_CHOICES , null = True ,
                                              blank = True )
    degradation_reference_range = models.CharField( verbose_name = '参考值' , max_length = 255 , null = True ,
                                                    blank = True )
    gas = models.DecimalField( verbose_name = '产气量' , max_digits = 12 , decimal_places = 4 , null = True ,
                               blank = True )
    gas_status = models.IntegerField( verbose_name = '产气量状态' , choices = STATUS_CHOICES , null = True , blank = True )
    gas_reference_range = models.CharField( verbose_name = '参考值' , max_length = 255 , null = True ,
                                            blank = True )
    is_status = models.IntegerField( verbose_name = '状态' , choices = TEST_CHOICES , default = 0 , null = True ,
                                     blank = True )

    class Meta:
        verbose_name = '气压与降解率'
        verbose_name_plural = verbose_name
        unique_together = ('sample_number' , 'carbon_source' , 'genus')

    def __str__(self):
        return '%s' % self.sample_number


# Create your models here.
class ScfasIndexes( models.Model ):
    STATUS_CHOICES = (
        (0 , '偏高') ,
        (1 , '正常') ,
        (2 , '偏低') ,
    )
    TEST_CHOICES = (
        (0 , '待检测') ,
        (2 , '完成') ,
    )
    sample_number = models.CharField( verbose_name = '样本编号' , max_length = 255 )
    carbon_source = models.ForeignKey( Carbon , verbose_name = '碳源' , on_delete = models.CASCADE , null = True )
    genus = models.ForeignKey( Genus , verbose_name = '菌种' , on_delete = models.CASCADE , null = True )
    carbon_source_zh = models.CharField( verbose_name = '碳源中文名称' , max_length = 255 , null = True , blank = True )
    genus_zh = models.CharField( verbose_name = '菌种中文名称' , max_length = 255 , null = True , blank = True )
    total_acid = models.DecimalField( verbose_name = '总酸' , max_digits = 12 , decimal_places = 4 , null = True ,
                                      blank = True )
    total_acid_status = models.IntegerField( verbose_name = '总酸状态' , choices = STATUS_CHOICES , null = True ,
                                             blank = True )
    total_acid_reference_range = models.CharField( verbose_name = '参考值' , max_length = 255 , null = True ,
                                                   blank = True )

    acetic_acid = models.DecimalField( verbose_name = '乙酸' , max_digits = 12 , decimal_places = 4 , null = True ,
                                       blank = True )
    acetic_acid_status = models.IntegerField( verbose_name = '乙酸状态' , choices = STATUS_CHOICES , null = True ,
                                              blank = True )
    acetic_acid_reference_range = models.CharField( verbose_name = '参考值' , max_length = 255 , null = True ,
                                                    blank = True )
    propionic = models.DecimalField( verbose_name = '丙酸' , max_digits = 12 , decimal_places = 4 , null = True ,
                                     blank = True )
    propionic_status = models.IntegerField( verbose_name = '丙酸状态' , choices = STATUS_CHOICES , null = True ,
                                            blank = True )
    propionic_reference_range = models.CharField( verbose_name = '参考值' , max_length = 255 , null = True ,
                                                  blank = True )
    butyric = models.DecimalField( verbose_name = '丁酸' , max_digits = 12 , decimal_places = 4 , null = True ,
                                   blank = True )
    butyric_status = models.IntegerField( verbose_name = '丁酸状态' , choices = STATUS_CHOICES , null = True ,
                                          blank = True )
    butyric_reference_range = models.CharField( verbose_name = '参考值' , max_length = 255 , null = True ,
                                                blank = True )
    isobutyric_acid = models.DecimalField( verbose_name = '异丁酸' , max_digits = 12 , decimal_places = 4 , null = True ,
                                           blank = True )
    isobutyric_acid_status = models.IntegerField( verbose_name = '异丁酸状态' , choices = STATUS_CHOICES , null = True ,
                                                  blank = True )
    isobutyric_acid_reference_range = models.CharField( verbose_name = '参考值' , max_length = 255 , null = True ,
                                                        blank = True )
    valeric = models.DecimalField( verbose_name = '戊酸' , max_digits = 12 , decimal_places = 4 , null = True ,
                                   blank = True )
    valeric_status = models.IntegerField( verbose_name = '戊酸状态' , choices = STATUS_CHOICES , null = True ,
                                          blank = True )
    valeric_reference_range = models.CharField( verbose_name = '参考值' , max_length = 255 , null = True ,
                                                blank = True )
    isovaleric = models.DecimalField( verbose_name = '异戊酸' , max_digits = 12 , decimal_places = 4 , null = True ,
                                      blank = True )
    isovaleric_status = models.IntegerField( verbose_name = '异戊酸状态' , choices = STATUS_CHOICES , null = True ,
                                             blank = True )
    isovaleric_reference_range = models.CharField( verbose_name = '参考值' , max_length = 255 , null = True ,
                                                   blank = True )
    isovaleric1 = models.DecimalField( verbose_name = '扩展酸1' , max_digits = 12 , decimal_places = 4 , null = True ,
                                       blank = True )
    isovaleric1_status = models.IntegerField( verbose_name = '扩展酸1状态' , choices = STATUS_CHOICES , null = True ,
                                              blank = True )
    isovaleric1_reference_range = models.CharField( verbose_name = '参考值' , max_length = 255 , null = True ,
                                                    blank = True )
    isovaleric2 = models.DecimalField( verbose_name = '扩展酸2' , max_digits = 12 , decimal_places = 4 , null = True ,
                                       blank = True )
    isovaleric2_status = models.IntegerField( verbose_name = '扩展酸2状态' , choices = STATUS_CHOICES , null = True ,
                                              blank = True )
    isovaleric2_reference_range = models.CharField( verbose_name = '参考值' , max_length = 255 , null = True ,
                                                    blank = True )
    isovaleric3 = models.DecimalField( verbose_name = '扩展酸3' , max_digits = 12 , decimal_places = 4 , null = True ,
                                       blank = True )
    isovaleric3_status = models.IntegerField( verbose_name = '扩展酸3状态' , choices = STATUS_CHOICES , null = True ,
                                              blank = True )
    isovaleric3_reference_range = models.CharField( verbose_name = '参考值' , max_length = 255 , null = True ,
                                                    blank = True )
    acid_first = models.DecimalField( verbose_name = '乙丙丁酸占总酸比' , max_digits = 12 , decimal_places = 4 , null = True ,
                                      blank = True )
    acid_first_status = models.IntegerField( verbose_name = '乙丙丁酸占总酸比状态' , choices = STATUS_CHOICES , null = True ,
                                             blank = True )
    acid_first_reference_range = models.CharField( verbose_name = '参考值' , max_length = 255 , null = True ,
                                                   blank = True )
    acid_second = models.DecimalField( verbose_name = '异丁戊异戊占总酸比' , max_digits = 12 , decimal_places = 4 , null = True ,
                                       blank = True )
    acid_second_status = models.IntegerField( verbose_name = '异丁戊异戊占总酸比状态' , choices = STATUS_CHOICES , null = True ,
                                              blank = True )
    acid_second_reference_range = models.CharField( verbose_name = '参考值' , max_length = 255 , null = True ,
                                                    blank = True )
    is_status = models.IntegerField( verbose_name = '状态' , choices = TEST_CHOICES , default = 0 , null = True ,
                                     blank = True )

    class Meta:
        verbose_name = 'SCFAs指标'
        verbose_name_plural = verbose_name
        unique_together = ('sample_number' , 'carbon_source' , 'genus')

    def __str__(self):
        return '%s' % self.sample_number
