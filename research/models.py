from django.db import models
from django.contrib.auth.models import User
from django.utils.html import format_html

from basicdata.models import Carbon , Genus


def func_file(instance , filename):
    return 'uploads/research/{0}/{1}'.format( instance.contract_number , filename )


class Contract( models.Model ):
    STATUS_CHOICES = (
        (1 , '方案讨论中') ,
        (2 , '合同签署中') ,
        (3 , '预实验中') ,
        (4 , '项目进度20%') ,
        (5 , '项目进度40%') ,
        (6 , '项目进度60%') ,
        (7 , '项目进度80%') ,
        (8 , '报告出具中') ,
        (9 , '已完成') ,
    )
    HT_CHOICES = (
        (1 , '无') ,
        (2 , '已签字') ,
        (3 , '已盖章') ,
    )
    contract_number = models.CharField( '合同号' , max_length = 255 , unique = True )
    name = models.CharField( '合同名' , max_length = 255 , blank = True , null = True )
    partner_company = models.CharField( '合同单位' , max_length = 255 , blank = True , null = True )
    keyword = models.CharField( '项目关键词' , max_length = 255 , blank = True , null = True )
    contacts = models.CharField( '合同联系人' , max_length = 255 , blank = True , null = True )
    contacts_email = models.EmailField( verbose_name = "合同联系人邮箱" , blank = True , null = True )
    contact_phone = models.CharField( '合同联系人电话' , max_length = 30 , blank = True , null = True )
    contact_address = models.CharField( '合同联系人地址' , max_length = 255 , blank = True , null = True )
    all_amount = models.DecimalField( '合同总款额' , max_digits = 12 , decimal_places = 2 , default = 0 )
    project_amount = models.DecimalField( '项目总费用' , max_digits = 12 , decimal_places = 2 , default = 0 )
    make_out_amount = models.DecimalField( "已开票金额" , max_digits = 12 , decimal_places = 2 , default = 0 )
    amount_in = models.DecimalField( '已到账金额' , max_digits = 12 , decimal_places = 2 , default = 0 )
    amount_date = models.DateField( '最后一笔到款日' , blank = True , null = True )
    tracking_number = models.CharField( '快递单号' , max_length = 25 , null = True , blank = True )
    send_date = models.DateField( '合同寄出日' , null = True , blank = True )
    receive_date = models.DateField( '合同寄回日' , null = True , blank = True )
    ht_choices = models.IntegerField( '盖章情况' , choices = HT_CHOICES , default = 1 )
    contract_file = models.FileField( '附件' , upload_to = 'uploads/research/contract/%Y/%m' , null = True ,
                                      blank = True )
    contract_file_scanning = models.FileField( '扫描件' , upload_to = 'uploads/research/contractScanning/%Y/%m' ,
                                               null = True ,
                                               blank = True )
    is_status = models.IntegerField( '状态' , choices = STATUS_CHOICES , default = 1 )
    project_leader = models.CharField( verbose_name = "项目负责人" , max_length = 255 , blank = True , null = True )
    report_file = models.CharField( '志愿者报告路径' , max_length = 255 , null = True , blank = True )
    payment = models.FileField( '收付款截图' , upload_to = func_file , null = True , blank = True )
    create_date = models.DateField( verbose_name = '创建时间' , auto_now_add = True )
    historys = models.TextField( verbose_name = "历史填写版本" , blank = True , null = True )
    writer = models.CharField( verbose_name = "创建人" , max_length = 255 , blank = True , null = True )
    note = models.TextField( verbose_name = '合同备注' , blank = True , null = True )

    class Meta:
        verbose_name = '合同管理'
        verbose_name_plural = '合同管理'

    def file_link(self):
        if self.contract_file:
            return format_html( "<a href='%s'>下载</a>" % (self.contract_file.url) )
        else:
            return "未上传"

    file_link.short_description = "合同附件"
    file_link.allow_tags = True

    def file_link_scanning(self):
        if self.contract_file_scanning:
            return format_html( "<a href='%s'>下载</a>" % (self.contract_file_scanning.url) )
        else:
            return "未上传"

    file_link_scanning.short_description = "合同扫描件"
    file_link_scanning.allow_tags = True

    def __str__(self):
        return '【%s】-【%s】' % (self.contract_number , self.name)


class InvoiceTitle( models.Model ):
    title = models.CharField( "发票抬头" , max_length = 100 )

    class Meta:
        verbose_name = '发票抬头'
        verbose_name_plural = '发票抬头'

    def __str__(self):
        return '%s' % self.title


class Invoice( models.Model ):
    STATUS_CHOICES = (
        (1 , '开票中') ,
        (2 , '完成') ,
    )
    INVOICE_TYPE_CHOICES = (
        ('CC' , '普票') ,
        ('SC' , '专票') ,
    )
    contract = models.ForeignKey( Contract , verbose_name = '合同' , on_delete = models.CASCADE )
    title = models.ForeignKey( InvoiceTitle , verbose_name = '发票抬头' , on_delete = models.CASCADE )
    invoice_code = models.CharField( '发票号码' , max_length = 12 , default = "" , blank = True )
    amount = models.DecimalField( '发票金额' , max_digits = 12 , decimal_places = 2 , default = 0 )
    type = models.CharField( '发票类型' , max_length = 3 , choices = INVOICE_TYPE_CHOICES , default = 'CC' )
    tax_amount = models.DecimalField( '开票税率' , max_digits = 12 , decimal_places = 2 , default = 0 )
    content = models.TextField( '发票内容' , null = True , blank = True )
    date = models.DateField( '开票日期' , null = True , blank = True )
    note = models.TextField( '备注' , null = True , blank = True )
    invoice_file = models.FileField( '电子发票' , upload_to = 'uploads/research/Invoice/%Y/%m' , null = True ,
                                     blank = True )
    tracking_number = models.CharField( '快递单号' , max_length = 15 , null = True , blank = True )
    send_date = models.DateField( '寄出日期' , null = True , blank = True )
    income_date = models.DateField( '到账日期' , null = True , blank = True )
    income = models.DecimalField( '到账金额' , null = True , max_digits = 12 , decimal_places = 2 , default = 0 )
    is_status = models.IntegerField( '状态' , choices = STATUS_CHOICES , default = 1 )
    create_date = models.DateField( verbose_name = '创建时间' , auto_now_add = True )
    historys = models.TextField( verbose_name = "历史填写版本" , blank = True , null = True )
    writer = models.CharField( verbose_name = "创建人" , max_length = 255 , blank = True , null = True )
    fp = models.BooleanField( '是发票' , default = True )  # 在save_formset函数中区分发票或账目

    class Meta:
        verbose_name = '发票管理'
        verbose_name_plural = '发票管理'

    def file_link(self):
        if self.invoice_file:
            return format_html( "<a href='%s'>下载</a>" % (self.invoice_file.url ,) )
        else:
            return "未上传"

    file_link.short_description = "电子发票"
    file_link.allow_tags = True

    def __str__(self):
        return '【%s】-【%s】' % (self.title , self.invoice_code)

    @property
    def income_set(self):
        if Bill.objects.filter( invoice = self.id ):
            return [float( i.income ) for i in Bill.objects.filter( invoice = self.id )]
        return ""

    @property
    def income_date_set(self):
        if Bill.objects.filter( invoice = self.id ):
            return [format( i.date , "%Y-%m-%d" ) for i in Bill.objects.filter( invoice = self.id )]
        return ""


class Bill( models.Model ):
    invoice = models.ForeignKey( Invoice , verbose_name = '发票' , on_delete = models.CASCADE )
    income = models.DecimalField( '到账金额' , max_digits = 12 , decimal_places = 2 , default = 0 )
    date = models.DateField( '到账日期' , null = True , blank = True )

    class Meta:
        verbose_name = '进账管理'
        verbose_name_plural = '进帐管理'

    def __str__(self):
        return '%f' % self.income


class Accounting( models.Model ):
    contract = models.ForeignKey( Contract , verbose_name = '合同' , on_delete = models.CASCADE )
    name = models.CharField( '账目名称' , max_length = 255 , blank = True , null = True )
    amount = models.DecimalField( '账目金额' , max_digits = 12 , decimal_places = 2 , default = 0 )
    date = models.DateField( verbose_name = '创建时间' , null = True , blank = True )
    note = models.TextField( '备注' , null = True , blank = True )
    fp = models.BooleanField( '是发票' , default = False )  # 在save_formset函数中区分发票或账目

    class Meta:
        verbose_name = '账目管理'
        verbose_name_plural = '账目管理'

    def __str__(self):
        return '%s' % self.name


class Stuff( models.Model ):
    STATUS_CHOICES = (
        (1 , '上传中') ,
        (2 , '完成') ,
    )
    contract_number = models.CharField( '合同号' , max_length = 255 , unique = True )
    payment = models.FileField( '方案' , upload_to = func_file , null = True , blank = True )
    carbon_source_content = models.CharField( verbose_name = '检测碳源' , max_length = 255 , null = True , blank = True )
    sample_content = models.TextField( verbose_name = '检测样本' , null = True , blank = True )
    report_file = models.CharField( '结题报告路径' , max_length = 255 , null = True , blank = True )
    tlc = models.FileField( 'TLC图片' , upload_to = func_file , null = True , blank = True )
    ax = models.FileField( 'A项图片' , upload_to = func_file , null = True , blank = True )
    ltjl = models.FileField( '聊天记录截图' , upload_to = func_file , null = True , blank = True )
    ngs = models.CharField( '测序路径' , max_length = 255 , null = True , blank = True )
    unconventional = models.FileField( '非常规检测项目' , upload_to = func_file , null = True , blank = True )
    nconventional_other = models.FileField( '非常规其他项目' , upload_to = func_file , null = True , blank = True )
    method = models.FileField( '检测方法' , upload_to = func_file , null = True , blank = True )
    is_status = models.IntegerField( '状态' , choices = STATUS_CHOICES , default = 1 )
    create_date = models.DateField( verbose_name = '创建时间' , auto_now_add = True )
    historys = models.TextField( verbose_name = "历史填写版本" , blank = True , null = True )
    writer = models.CharField( verbose_name = "创建人" , max_length = 255 , blank = True , null = True )

    class Meta:
        verbose_name = '资料管理'
        verbose_name_plural = '资料管理'

    def __str__(self):
        return '%s' % self.contract_number


class ExperimentalData( models.Model ):
    TEST_CHOICES = (
        (0 , '待检测') ,
        (1 , '完成') ,
    )
    SEX_CHOICES = (
        (0 , '女性') ,
        (1 , '男性') ,
    )
    contract_number = models.CharField( verbose_name = '合同号' , max_length = 255 )
    sample_number = models.CharField( verbose_name = '样本编号' , max_length = 255 )
    internal_number = models.CharField( verbose_name = '对内编号' , max_length = 255 )
    carbon_source = models.ForeignKey( Carbon , verbose_name = '碳源' , on_delete = models.CASCADE , null = True )
    group = models.CharField( verbose_name = '组别' , max_length = 255 )
    intervention = models.CharField( verbose_name = '干预前后' , max_length = 255 )
    carbon_source_zh = models.CharField( verbose_name = '碳源中文名称' , max_length = 255 , null = True , blank = True )
    # 临床信息
    recordNo = models.CharField( verbose_name = '病历号' , max_length = 255 , blank = True , null = True )
    name = models.CharField( verbose_name = '姓名' , max_length = 255 , blank = True , null = True)
    gender = models.IntegerField( verbose_name = '性别' , choices = SEX_CHOICES , null = True , blank = True )
    age = models.IntegerField( verbose_name = '年龄' , blank = True , null = True )
    age_sgement = models.CharField( verbose_name = '年龄分段' , max_length = 255 , blank = True , null = True)  # 因指标参考范围会因此因素造成影响，必填项，
    province = models.CharField( verbose_name = '地域' , max_length = 255 , blank = True , null = True)  # 因指标参考范围会因此因素造成影响，必填项，
    height = models.DecimalField( verbose_name = '身高' , max_digits = 5 , decimal_places = 2 , null = True ,
                                  blank = True )
    weight = models.DecimalField( verbose_name = '体重' , max_digits = 5 , decimal_places = 2 , null = True ,
                                  blank = True )
    fbj = models.CharField( verbose_name = '空腹血糖' , max_length = 255 , null = True , blank = True )
    blood_pressure = models.CharField( verbose_name = '血压' , max_length = 255 , null = True , blank = True )
    trioxypurine = models.CharField( verbose_name = '尿酸' , max_length = 255 , null = True , blank = True )
    triglyceride = models.CharField( verbose_name = '血脂' , max_length = 255 , null = True , blank = True )
    anamnesis = models.CharField( verbose_name = '确诊疾病' , max_length = 255 , null = True , blank = True )
    staging = models.CharField( verbose_name = '疾病分期' , max_length = 255 , blank = True , null = True )
    therapies = models.CharField( verbose_name = '治疗方法' , max_length = 255 , blank = True , null = True )

    ###短链脂肪酸
    total_acid = models.DecimalField( verbose_name = '总酸' , max_digits = 12 , decimal_places = 4 , null = True ,
                                      blank = True )
    acetic_acid = models.DecimalField( verbose_name = '乙酸' , max_digits = 12 , decimal_places = 4 , null = True ,
                                       blank = True )
    propionic = models.DecimalField( verbose_name = '丙酸' , max_digits = 12 , decimal_places = 4 , null = True ,
                                     blank = True )
    butyric = models.DecimalField( verbose_name = '丁酸' , max_digits = 12 , decimal_places = 4 , null = True ,
                                   blank = True )
    isobutyric_acid = models.DecimalField( verbose_name = '异丁酸' , max_digits = 12 , decimal_places = 4 , null = True ,
                                           blank = True )
    valeric = models.DecimalField( verbose_name = '戊酸' , max_digits = 12 , decimal_places = 4 , null = True ,
                                   blank = True )
    isovaleric = models.DecimalField( verbose_name = '异戊酸' , max_digits = 12 , decimal_places = 4 , null = True ,
                                      blank = True )
    acetic_acid_ratio = models.DecimalField( verbose_name = '乙酸占比' , max_digits = 12 , decimal_places = 4 ,
                                             null = True ,
                                             blank = True )
    propionic_ratio = models.DecimalField( verbose_name = '丙酸占比' , max_digits = 12 , decimal_places = 4 , null = True ,
                                           blank = True )
    butyric_ratio = models.DecimalField( verbose_name = '丁酸占比' , max_digits = 12 , decimal_places = 4 , null = True ,
                                         blank = True )
    isobutyric_acid_ratio = models.DecimalField( verbose_name = '异丁酸占比' , max_digits = 12 , decimal_places = 4 ,
                                                 null = True ,
                                                 blank = True )
    valeric_ratio = models.DecimalField( verbose_name = '戊酸占比' , max_digits = 12 , decimal_places = 4 , null = True ,
                                         blank = True )
    isovaleric_ratio = models.DecimalField( verbose_name = '异戊酸占比' , max_digits = 12 , decimal_places = 4 ,
                                            null = True ,
                                            blank = True )
    # 产气量

    gas = models.DecimalField( verbose_name = '产气量' , max_digits = 12 , decimal_places = 4 , null = True ,
                               blank = True )
    co2 = models.DecimalField( verbose_name = 'CO2' , max_digits = 12 , decimal_places = 4 , null = True ,
                               blank = True )
    ch4 = models.DecimalField( verbose_name = 'CH4' , max_digits = 12 , decimal_places = 4 , null = True ,
                               blank = True )
    h2 = models.DecimalField( verbose_name = 'H2' , max_digits = 12 , decimal_places = 4 , null = True ,
                              blank = True )
    h2s = models.DecimalField( verbose_name = 'H2S' , max_digits = 12 , decimal_places = 4 , null = True ,
                               blank = True )

    # 降解率
    degradation = models.DecimalField( verbose_name = '降解率' , max_digits = 12 , decimal_places = 4 , null = True ,
                                       blank = True )
    # qpcr
    BIFI = models.FloatField( verbose_name = '双歧杆菌' , null = True , blank = True )
    LAC = models.FloatField( verbose_name = '乳酸菌' , null = True , blank = True )
    CS = models.FloatField( verbose_name = '共生梭菌' , null = True , blank = True )
    FN = models.FloatField( verbose_name = '具核梭杆菌' , null = True , blank = True )
    EF = models.FloatField( verbose_name = '粪肠球菌' , null = True , blank = True )
    BT = models.FloatField( verbose_name = '多形拟杆菌' , null = True , blank = True )
    AKK = models.FloatField( verbose_name = '阿克曼氏菌' , null = True , blank = True )
    FAE = models.FloatField( verbose_name = '普拉梭菌' , null = True , blank = True )
    is_status = models.IntegerField( verbose_name = '状态' , choices = TEST_CHOICES , default = 0 , null = True ,
                                     blank = True )

    class Meta:
        verbose_name = '实验数据'
        verbose_name_plural = verbose_name
        unique_together = ('contract_number' , 'sample_number' , 'carbon_source' , 'group' , 'intervention')

    def __str__(self):
        return '%s' % self.sample_number


class Material( models.Model ):
    carbon_source = models.CharField( verbose_name = '碳源编号' , max_length = 255 )
    carbon_source_zh = models.CharField( verbose_name = '碳源中文名称' , max_length = 255 , null = True , blank = True )
    name = models.CharField( verbose_name = '名称' , max_length = 255 )
    brand = models.CharField( verbose_name = '品牌' , max_length = 255 , null = True ,
                              blank = True )
    artNo = models.CharField( verbose_name = '货号' , max_length = 255 , null = True ,
                              blank = True )
    batch = models.CharField( verbose_name = '批次号' , max_length = 255 , null = True ,
                              blank = True )
    create_date = models.DateField( verbose_name = '创建时间' , auto_now_add = True )
    historys = models.TextField( verbose_name = "历史填写版本" , blank = True , null = True )
    writer = models.CharField( verbose_name = "创建人" , max_length = 255 , blank = True , null = True )
    note = models.TextField( verbose_name = '备注' , max_length = 255 , blank = True , null = True )

    class Meta:
        verbose_name = '原料管理'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '%s' % self.name
