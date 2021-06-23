from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from basicdata.models import Carbon , Genus


class DataInformation( models.Model ):
    STATUS_CHOICES = (
        (0 , '偏高') ,
        (1 , '正常') ,
        (2 , '偏低') ,
    )
    SEX_CHOICES = (
        (0 , '女性') ,
        (1 , '男性') ,
    )
    RESULT_CHOICES = (
        (0 , '阴性') ,
        (1 , '阳性') ,
    )
    sample_number = models.CharField( verbose_name = '样本编号' , max_length = 255 )  # 需要样本录入后才能有问卷信息
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

    # 常规指标
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

    # bio指标
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
    bile_acid_reference_range = models.CharField( verbose_name = '参考值' , max_length = 255 , null = True ,
                                                  blank = True )
    # Qpcr

    carbon_source = models.CharField( verbose_name = '碳源' , max_length = 255 , null = True ,
                                      blank = True )
    genus = models.CharField( verbose_name = '菌种' , max_length = 255 , null = True ,
                              blank = True )
    carbon_source_zh = models.CharField( verbose_name = '碳源中文名称' , max_length = 255 , null = True , blank = True )
    genus_zh = models.CharField( verbose_name = '菌种中文名称' , max_length = 255 , null = True , blank = True )



    ct = models.DecimalField( verbose_name = 'CT' , max_digits = 12 , decimal_places = 4 , null = True ,
                              blank = True )
    concentration = models.FloatField( verbose_name = 'Qpcr浓度' , null = True , blank = True ) # TODO 数据库中的类型有问题
    concentration_reference_range = models.CharField( verbose_name = '参考值' , max_length = 255 , null = True ,
                                                      blank = True )
    concentration_status = models.IntegerField( verbose_name = '浓度状态' , choices = STATUS_CHOICES , null = True ,
                                                blank = True )

    # 降解率

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
    # 短链脂肪酸

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

    class Meta:
        verbose_name = '全信息'
        verbose_name_plural = verbose_name
        # unique_together = ('sample_number' , 'carbon_source' , 'genus')

    def __str__(self):
        return '%s' % self.sample_number



class Book( models.Model ):
    title = models.CharField( max_length = 32 )
    CHOICES = (
        (1 , 'Python') ,
        (2 , 'Linux') ,
        (3 , 'Go')
    )
    category = models.IntegerField( choices = CHOICES )
    pub_time = models.DateField( )
    publisher = models.ForeignKey( to = 'Publisher' , on_delete = models.CASCADE )
    authors = models.ManyToManyField( to = 'Author' )


class Publisher( models.Model ):
    title = models.CharField( max_length = 32 )


class Author( models.Model ):
    name = models.CharField( max_length = 32 )
