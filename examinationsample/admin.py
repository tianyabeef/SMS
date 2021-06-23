import os
from django.core import serializers
from django.contrib import admin
import json
from docxtpl import DocxTemplate
from import_export import resources
from datacenter.models import DataInformation
from examinationsample.models import Checks
from examinationsample.models import Progress
from examinationsample.models import Sample
from examinationreport.models import Reports
from questionnairesurvey.models import Quenstion
from labinformation.models import ScfasIndexes
from labinformation.models import QpcrIndexes
from labinformation.models import BioChemicalIndexes
from labinformation.models import ConventionalIndex
from labinformation.models import DegradationIndexes
from import_export.admin import ImportExportActionModelAdmin , ImportExportActionModelAdmin
from django.contrib import messages
import datetime
from basicdata.models import Product , Carbon , Genus
from django import forms
import re
from basicdata.models import CheckItem
import jinja2

admin.site.empty_value_display = '-empty-'


def tran_format(value):
    if value is not None:
        if float( value ) > 1000 or (0.001 > float( value ) > 0) or float( value ) < -0.001:  # TODO 当数值多少用科学计数法比较合理
            value = "%.2e" % value
    else:
        value = 0
    return value


class ChecksForm( forms.ModelForm ):
    """
        对检查项目的数量和检测名称进行validation
    """

    class Meta:
        model = Checks
        exclude = ("" ,)

    def clean_check_name(self):
        if CheckItem.objects.filter( check_name = self.cleaned_data ["check_name"] ).count( ) == 0:
            raise forms.ValidationError( "检测模块名称在数据库中无法查询到" )
        return self.cleaned_data ["check_name"]

    def clean_check_number(self):
        if CheckItem.objects.filter( number = self.cleaned_data ["check_number"] ).count( ) == 0:
            raise forms.ValidationError( "检测模块编号在数据库中无法查询到" )
        return self.cleaned_data ["check_number"]


class ChecksInline( admin.TabularInline ):
    """
        样本收样中的检测项目申请（Inline）
    """
    form = ChecksForm  # TODO 对检查项目的数量和检测名称进行validation
    model = Checks
    extra = 1  # 额外新开一个
    fields = ('check_name' , 'is_status' , 'finish_date')
    readonly_fields = ('is_status' , 'finish_date')
    # # autocomplete_fields = ('title',)   # TODO 当数据量较多是，下拉框会变得很长，有待优化
    # raw_id_fields = ('check_name',)
    #
    #
    # def get_readonly_fields(self, request, obj=None):
    #     if obj.is_status == 2:
    #         self.readonly_fields = ['check_name', 'sample_number', 'finish_date']
    #     return self.readonly_fields


class SampleForm( forms.ModelForm ):
    set_meal = forms.CharField( label = "套餐编号" , help_text = "不能为空，。示例：TC0001" ,
                                required = True , widget = forms.TextInput( attrs =
                                                                            {'class': 'vTextField , form-control' ,
                                                                             'placeholder': '示例：TC0001'} ) ,
                                error_messages = {'required': '这个字段是必填项。'} )

    class Meta:
        model = Sample
        exclude = ("" ,)

    def clean_set_meal(self):
        if Product.objects.filter( number = self.cleaned_data ["set_meal"] ).count( ) == 0:
            raise forms.ValidationError( "套餐编号在数据库中无法查询到" )
        return self.cleaned_data ["set_meal"]


class SampleResource( resources.ModelResource ):
    class Meta:
        model = Sample
        skip_unchanged = True
        fields = (
            'id' , 'sample_number' , 'internal_number' , 'name' , 'email' , 'receive_sample' , 'receive_sample_date' ,
            'sample_source' , 'set_meal' , 'cost' , 'report_date' , 'report_template' , 'report_template_url' , 'note')
        export_order = (
            'id' , 'sample_number' , 'internal_number' , 'name' , 'email' , 'receive_sample' , 'receive_sample_date' ,
            'sample_source' , 'set_meal' , 'cost' , 'report_date' , 'report_template' , 'report_template_url' , 'note')


@admin.register( Sample )
class SampleAdmin( ImportExportActionModelAdmin , admin.ModelAdmin ):
    list_display = (
        "sample_number" , 'internal_number' , 'receive_sample_date' , 'receive_sample' , 'is_wjxx' , 'report_date' ,
        'is_status')
    list_display_links = ('sample_number' ,)
    ordering = ("-sample_number" ,)
    view_on_site = False
    list_max_show_all = 100
    list_per_page = 20
    list_filter = ("sample_source" , 'is_status')
    search_fields = ('sample_number' ,)
    resource_class = SampleResource
    form = SampleForm
    # list_editable = ('internal_number' ,)
    # actions=
    inlines = [ChecksInline , ]
    date_hierarchy = 'report_date'  # 按照时间搜素
    actions = ['make_test' , 'export_admin_action']
    fieldsets = (
        ('基本信息' , {
            'fields': (("sample_number" , 'internal_number' ,) ,
                       ('name' , 'email') ,
                       ('receive_sample' ,) ,
                       ('sample_source' ,) ,
                       ('set_meal' , 'product_name') ,)
        }) ,

        ('金额' , {
            'fields': (
                ('cost' ,) , ('report_template' , 'report_template_url' ,) , ('note' , 'is_status') , ('historys' ,))
        })
    )

    def product_name(self , obj):
        product = Product.objects.filter( number = obj.set_meal )
        return product [0].name if product else ""

    product_name.short_description = "套餐名称"

    def is_wjxx(self , obj):
        check_wjxx = Checks.objects.filter( sample_number = obj )
        return check_wjxx [0].finish_date if check_wjxx else ""

    is_wjxx.short_description = "问卷完成时间"

    # '''自定义actions'''
    # def get_actions(self , request):
    #     actions = super( ).get_actions( request )
    #     return actions

    def get_readonly_fields(self , request , obj=None):
        # 根据 obj 是否为空来判断,修改数据时不能修改样本接收人，
        if obj:
            self.readonly_fields = (
                "sample_number" , 'internal_number' , 'historys' , 'receive_sample' , 'product_name' ,
                'report_template_url' , 'is_status')
        else:
            self.readonly_fields = ('historys' , 'product_name' , 'report_template_url' , 'is_status')
        # if request.user.is_superuser: TODO 正式上线时放开注释
        #     self.readonly_fields = ( 'product_name',)
        return self.readonly_fields

    def make_test(self , request , queryset):
        i = 0  # 提交成功的数据
        n = 0  # 提交过的数量
        t = 0  # 选中状态
        for obj in queryset:
            t += 1
            if obj.is_status < 1:
                obj.is_status = 1
                checks_list = Checks.objects.filter( sample_number_id = obj.id )
                obj_progress , created = Progress.objects.get_or_create( sample_number = obj.sample_number ,
                                                                         internal_number = obj.internal_number )
                obj_progress.receive_sample_date = obj.receive_sample_date  # 为避免报错，先找到数据，在赋值。
                obj_progress.workforce_date = datetime.date.today( )

                i += 1
                for checks in checks_list:
                    check_item = CheckItem.objects.get( number = checks.check_number )
                    cs = re.split( '[；;]' , check_item.carbon_source )
                    for cs_temp in cs:
                        cs_temp_id = Carbon.objects.get( cid = cs_temp )
                        gs_temp_id = Genus.objects.get( english_name = check_item.genus )
                        if check_item.type.number == "JCDL0001":  # 问卷调查
                            Quenstion.objects.get_or_create( sample_number = obj.sample_number ,
                                                             carbon_source = cs_temp_id , genus = gs_temp_id ,
                                                             carbon_source_zh = cs_temp_id.name ,
                                                             genus_zh = gs_temp_id.china_name )
                            obj_progress.is_wjxx = True
                        if check_item.type.number == "JCDL0002":  # 常规指标项
                            ConventionalIndex.objects.get_or_create( sample_number = obj.sample_number ,
                                                                     carbon_source = cs_temp_id , genus = gs_temp_id ,
                                                                     carbon_source_zh = cs_temp_id.name ,
                                                                     genus_zh = gs_temp_id.china_name )
                            obj_progress.is_cgzb = True
                        if check_item.type.number == "JCDL0003":  # 生化指标项
                            BioChemicalIndexes.objects.get_or_create( sample_number = obj.sample_number ,
                                                                      carbon_source = cs_temp_id , genus = gs_temp_id ,
                                                                      carbon_source_zh = cs_temp_id.name ,
                                                                      genus_zh = gs_temp_id.china_name )
                            obj_progress.is_shzb = True
                        if check_item.type.number == "JCDL0004":  # qPCR检测项
                            QpcrIndexes.objects.get_or_create( sample_number = obj.sample_number ,
                                                               carbon_source = cs_temp_id , genus = gs_temp_id ,
                                                               carbon_source_zh = cs_temp_id.name ,
                                                               genus_zh = gs_temp_id.china_name )
                            obj_progress.is_qpcr = True
                        if check_item.type.number == "JCDL0005":  # SCFAs检测项
                            ScfasIndexes.objects.get_or_create( sample_number = obj.sample_number ,
                                                                carbon_source = cs_temp_id , genus = gs_temp_id ,
                                                                carbon_source_zh = cs_temp_id.name ,
                                                                genus_zh = gs_temp_id.china_name )
                            obj_progress.is_scfa = True
                        if check_item.type.number == "JCDL0006":  # 气压和降解率检测项
                            DegradationIndexes.objects.get_or_create( sample_number = obj.sample_number ,
                                                                      carbon_source = cs_temp_id , genus = gs_temp_id ,
                                                                      carbon_source_zh = cs_temp_id.name ,
                                                                      genus_zh = gs_temp_id.china_name )
                            obj_progress.is_qyjj = True
                obj.save( )
                obj_progress.save( )
            else:
                n += 1
        self.message_user( request , "选择%s条信息，完成操作%s条，不操作%s条" % (t , i , n) , level = messages.SUCCESS )

    make_test.short_description = "1检测排班"

    def get_changeform_initial_data(self , request):
        initial = super( ).get_changeform_initial_data( request )
        initial ['receive_sample'] = request.user.last_name + ' ' + request.user.first_name
        return initial

    def save_model(self , request , obj , form , change):
        if obj.report_template is not None:
            obj.report_template_url = str( obj.report_template.file_template )
        if obj.historys is None:
            obj.historys = "编号:" + obj.sample_number + ";对内编号:" + obj.internal_number + ";姓名:" + obj.name + ";时间:" \
                           + datetime.date.today( ).__str__( )
        else:
            obj.historys = obj.historys + "\n" + "编号:" + obj.sample_number + ";对内编号:" \
                           + obj.internal_number + ";姓名:" + obj.name + ";时间:" + datetime.date.today( ).__str__( )
        obj.receive_sample = "%s %s" % (request.user.last_name , request.user.first_name)  # 系统自动添加创建人
        obj.save( )
        # 保存样本收样的同时，保存了样本检测表，再样本检测项的表格中没有数据，则表明时第一次创建
        if Checks.objects.filter( id = obj.id ).count( ) == 0:
            products = Product.objects.filter( number = obj.set_meal )
            if products.count( ) == 1:
                numbers = re.split( '[；;]' , products [0].check_content )
                for number in numbers:
                    check_item = CheckItem.objects.filter( number = number )
                    Checks.objects.get_or_create( check_number = check_item [0].number ,
                                                  check_name = check_item [0].check_name ,
                                                  sample_number_id = obj.id )
                # 对样本第一次收样时，在样本进度表中保存收样时间
                obj_progress , created = Progress.objects.get_or_create( sample_number = obj.sample_number ,
                                                                         internal_number = obj.internal_number )
                obj_progress.receive_sample_date = obj.receive_sample_date  # 为避免报错，先找到数据，在赋值。
                obj_progress.save( )
            else:
                raise forms.ValidationError( "套餐编号不是唯一，请核实基础数据" )


class ProgressResource( resources.ModelResource ):
    class Meta:
        model = Progress
        skip_unchanged = True
        fields = ('id' , 'name')
        export_order = ('id' , 'name')


@admin.register( Progress )
class ProgressAdmin( ImportExportActionModelAdmin , admin.ModelAdmin ):
    list_display = (
        'id' , 'sample_number' , 'internal_number' , 'wjxx_testing_date' ,
        'cgzb_testing_date' , 'shzb_testing_date' , 'SCFAs_testing_date' ,
        'qPCR_testing_date' , 'degradation_testing_date' ,
        'report_testing_date' , 'is_status')
    list_display_links = ('sample_number' ,)
    ordering = ("-sample_number" ,)
    view_on_site = False
    list_max_show_all = 100
    list_per_page = 20
    list_filter = ("is_status" ,)
    search_fields = ('sample_number' ,)
    resource_class = ProgressResource
    # form =
    # list_editable =
    actions = ['make_published' , 'export_admin_action']
    exclude = ("kuoz1_testing_staff" , 'kuoz1_testing_date' , 'kuoz2_testing_staff' , 'kuoz2_testing_date')

    @staticmethod
    def pos_value_display(value):
        pos_nag = {
            0: "阴性（-）" ,
            1: "阳性（+）"}
        if type( value ) is str:
            pos_nag_str = {
                "0": "阴性（-）" ,
                "1": "阳性（+）"}
            value = pos_nag_str.get( value )
        else:
            value = pos_nag.get( value )
        return value

    @staticmethod
    def sex_value_display(value):
        SEX_CHOICES = {
            0: '女性' ,
            1: '男性' ,
        }
        value = SEX_CHOICES.get( value )
        return value

    @staticmethod
    def percent_value_display(value):
        if value is not None:
            value = format( float( value ) , '.2%' )
        else:
            value = "0%"
        return value

    @staticmethod
    def side_value_display(value):
        STATUS_CHOICES = {
            0: '↑' ,
            1: '' ,
            2: '↓' ,
        }
        if value is not None:
            value = STATUS_CHOICES.get( value )
        else:
            value = "缺失"
        return value

    def make_published(self , request , queryset):
        i = 0  # 提交成功的数据
        n = 0  # 提交过的数量
        t = 0  # 选中状态
        for obj in queryset:
            t += 1
            if obj.is_status < 1:
                # obj.is_status = 1
                obj_progress , created = Reports.objects.get_or_create( sample_number = obj.sample_number )
                sample = Sample.objects.filter( sample_number = obj.sample_number ) [0]
                filename , suffix = os.path.splitext( sample.report_template_url )
                obj_progress.word_report = filename + obj.sample_number + suffix  # 为避免报错，先找到数据，在赋值。
                i += 1
                obj.save( )
                obj_progress.save( )
                # 生成word报告
                doc = DocxTemplate( 'media/' + str(
                    Sample.objects.get( sample_number = obj.sample_number ).report_template_url ) )  # TODO 关闭新增样本进度表

                checks_list = Checks.objects.filter(
                    sample_number__sample_number = obj.sample_number )  # TODO 假设不存在样本收样后，检查项为空的情况
                data = {}
                for checks in checks_list:
                    check_item = CheckItem.objects.get( number = checks.check_number )
                    cs = re.split( '[；;]' , check_item.carbon_source )
                    for carbon_source_temp in cs:
                        cs_temp_id = Carbon.objects.get( cid = carbon_source_temp )
                        gs_temp_id = Genus.objects.get( english_name = check_item.genus )
                        key_tmp = checks.check_number + carbon_source_temp + check_item.genus
                        if key_tmp not in data.keys( ):
                            '''如果需要初始化可以添加一下三个参数
                                'sample_number': obj.sample_number ,
                                'carbon_source': cs_temp_id ,
                                'genus': gs_temp_id
                            '''
                            data [key_tmp] = {}
                        if check_item.type.number == "JCDL0001":  # 问卷调查
                            quenstion = Quenstion.objects.filter( sample_number = obj.sample_number ,
                                                                  carbon_source = cs_temp_id ,
                                                                  genus = gs_temp_id )
                            tmp = serializers.serialize( 'json' , queryset = quenstion )
                            quenstion_data = json.loads( tmp ) [0] ['fields']
                            for i in ["is_status" , "sample_number" , "carbon_source" , "genus" , "genus_zh" ,
                                      "carbon_source_zh"]:
                                del quenstion_data [i]
                            data [key_tmp].update( quenstion_data )

                        if check_item.type.number == "JCDL0002":  # 常规指标项
                            conventional = ConventionalIndex.objects.filter( sample_number = obj.sample_number ,
                                                                             carbon_source = cs_temp_id ,
                                                                             genus = gs_temp_id )
                            tmp = serializers.serialize( 'json' , queryset = conventional )
                            conventional_data = json.loads( tmp ) [0] ['fields']
                            for i in ["is_status" , "sample_number" , "carbon_source" , "genus" , "genus_zh" ,
                                      "carbon_source_zh"]:
                                del conventional_data [i]
                            data [key_tmp].update( conventional_data )
                        if check_item.type.number == "JCDL0003":  # 生化指标项
                            bio = BioChemicalIndexes.objects.filter( sample_number = obj.sample_number ,
                                                                     carbon_source = cs_temp_id ,
                                                                     genus = gs_temp_id )
                            tmp = serializers.serialize( 'json' , queryset = bio )
                            bio_data = json.loads( tmp ) [0] ['fields']
                            for i in ["is_status" , "sample_number" , "carbon_source" , "genus" , "genus_zh" ,
                                      "carbon_source_zh"]:
                                del bio_data [i]
                            data [key_tmp].update( bio_data )
                        if check_item.type.number == "JCDL0004":  # qPCR检测项
                            qpcr = QpcrIndexes.objects.filter( sample_number = obj.sample_number ,
                                                               carbon_source = cs_temp_id ,
                                                               genus = gs_temp_id )
                            tmp = serializers.serialize( 'json' , queryset = qpcr )
                            qpcr_data = json.loads( tmp ) [0] ['fields']
                            for i in ["is_status" , "sample_number" , "carbon_source" , "genus" , "genus_zh" ,
                                      "carbon_source_zh","formula_number"]:
                                del qpcr_data [i]
                            data [key_tmp].update( qpcr_data )
                        if check_item.type.number == "JCDL0005":  # SCFAs检测项
                            scfas = ScfasIndexes.objects.filter( sample_number = obj.sample_number ,
                                                                 carbon_source = cs_temp_id ,
                                                                 genus = gs_temp_id )
                            tmp = serializers.serialize( 'json' , queryset = scfas )
                            scfas_data = json.loads( tmp ) [0] ['fields']
                            for i in ["is_status" , "sample_number" , "carbon_source" , "genus" , "genus_zh" ,
                                      "carbon_source_zh"]:
                                del scfas_data [i]
                            data [key_tmp].update( scfas_data )
                        if check_item.type.number == "JCDL0006":  # 气压和降解率检测项
                            degradation = DegradationIndexes.objects.filter( sample_number = obj.sample_number ,
                                                                             carbon_source = cs_temp_id ,
                                                                             genus = gs_temp_id )
                            tmp = serializers.serialize( 'json' , queryset = degradation )
                            degradation_data = json.loads( tmp ) [0] ['fields']
                            for i in ["is_status" , "sample_number" , "carbon_source" , "genus" , "genus_zh" ,
                                      "carbon_source_zh"]:
                                del degradation_data [i]
                            data [key_tmp].update( degradation_data )
                # forms.ValidationError( data )
                for tmp in data.values( ):
                    DataInformation( **tmp ).save( )
                # quenstion = Quenstion.objects.filter(sample_number = obj.sample_number)
                # conventional_index = ConventionalIndex.objects.filter(sample_number = obj.sample_number)
                # bio_chemical_indexes = BioChemicalIndexes.objects.filter(sample_number = obj.sample_number)
                # qpcr_indexes = QpcrIndexes.objects.filter(sample_number = obj.sample_number,carbon_source = obj,genus = obj)
                # degradation_indexes = DegradationIndexes.objects.filter(sample_number = obj.sample_number,carbon_source = obj)
                # context = {'company_name': str( checks.count( ) ) + "202年↑↑↑↑10月"}
                data [key_tmp].update( {'receive_sample_date': str( datetime.date.today( ) )} )
                data [key_tmp].update( {'report_testing_date': str( datetime.date.today( ) )} )
                jinja_env = jinja2.Environment( )
                jinja_env.filters ["tran"] = tran_format
                jinja_env.filters ["pos"] = self.pos_value_display
                jinja_env.filters ["sex"] = self.sex_value_display
                jinja_env.filters ['percent'] = self.percent_value_display
                jinja_env.filters ['side'] = self.side_value_display
                doc.render( data , jinja_env )
                doc.save( 'media/' + str( filename + obj.sample_number + suffix ) )
            else:
                n += 1
        self.message_user( request , "选择%s条信息，完成操作%s条，不操作%s条" % (t , i , n) , level = messages.SUCCESS )

    make_published.short_description = "1出具报告"


@admin.register( Checks )
class ChecksAdmin( ImportExportActionModelAdmin , admin.ModelAdmin ):
    list_display = ('id' , 'check_name' , 'check_number' , 'sample_number' , 'is_status' , 'finish_date' , 'writer')
    list_display_links = ('check_name' ,)
    ordering = ("-sample_number" ,)
    view_on_site = False
    list_max_show_all = 100
    list_per_page = 20
    list_filter = ("is_status" ,)
    search_fields = ('sample_number' ,)
    # resource_class =
    form = ChecksForm

    # list_editable =
    # actions =

    def get_readonly_fields(self , request , obj=None):
        # 根据 obj 是否为空来判断,修改数据时不能修改样本接收人，
        if obj:
            self.readonly_fields = ('check_name' , 'sample_number' , 'check_number')
        else:
            self.readonly_fields = ()
        return self.readonly_fields

    def get_changeform_initial_data(self , request):
        initial = super( ).get_changeform_initial_data( request )
        initial ['writer'] = request.user.last_name + ' ' + request.user.first_name
        return initial

    def save_model(self , request , obj , form , change):
        obj.writer = "%s %s" % (request.user.last_name , request.user.first_name)  # 系统自动添加创建人
        obj.save( )
