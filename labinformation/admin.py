import datetime
import re
from functools import reduce
from django.db.models import Q
import tablib
from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportActionModelAdmin
from import_export.formats import base_formats
from django import forms
from labinformation.models import BioChemicalIndexes , IndexesUnusual , MetaRiskIndexes , GutRiskIndexes
from labinformation.models import ConventionalIndex
from labinformation.models import DegradationIndexes
from labinformation.models import QpcrIndexes
from labinformation.models import ScfasIndexes
from examinationsample.models import Risk
from basicdata.models import CTformula , RiskItem , RiskItemDefault
from formula import Solver
from basicdata.models import ReferenceRange
from basicdata.models import Carbon
from basicdata.models import Genus
from django.contrib import messages
from examinationsample.models import Progress , Sample , Risk
from django.db.models.query import QuerySet
from django.utils.html import format_html
from itertools import product

admin.site.empty_value_display = '-empty-'


def get_meta_risk(risk_items):
    if risk_items.count( ) == 1:
        risk_item = risk_items [0]
        meta_risk = re.split( '[；;]' , risk_item.index_name )
    else:
        meta_risk = []
    return meta_risk


def create_risk(obj , key , key_obj , low_or_high , QpcrIndexes=False):
    """
    :param QpcrIndexes:  是否pqcr对象
    :param obj:
    :param key:  偏高或偏低的指标
    :param key_obj: 指标的对象
    :param low_or_high: 偏高或偏低的字符串
    """
    if QpcrIndexes:
        MetaRiskIndexes.objects.get_or_create( sample_number = obj.sample_number ,
                                               internal_number = obj.internal_number ,
                                               carbon_source = obj.carbon_source ,
                                               genus = obj.genus ,
                                               index_name = obj.genus_zh ,
                                               is_status = low_or_high ,
                                               blood_fat = 0 , fat = 0 )
        GutRiskIndexes.objects.get_or_create( sample_number = obj.sample_number ,
                                              internal_number = obj.internal_number ,
                                              carbon_source = obj.carbon_source ,
                                              genus = obj.genus ,
                                              index_name = obj.genus_zh ,
                                              is_status = low_or_high ,
                                              infection = 0 , scherm = 0 , cancer = 0 )
    else:
        MetaRiskIndexes.objects.get_or_create( sample_number = obj.sample_number ,
                                               internal_number = obj.internal_number ,
                                               carbon_source = obj.carbon_source ,
                                               genus = obj.genus ,
                                               index_name = key_obj._meta.get_field( key ).verbose_name ,
                                               is_status = low_or_high ,
                                               blood_fat = 0 , fat = 0 )
        GutRiskIndexes.objects.get_or_create( sample_number = obj.sample_number ,
                                              internal_number = obj.internal_number ,
                                              carbon_source = obj.carbon_source ,
                                              genus = obj.genus ,
                                              index_name = key_obj._meta.get_field( key ).verbose_name ,
                                              is_status = low_or_high ,
                                              infection = 0 , scherm = 0 , cancer = 0 )


def get_status(objects , carbon_source , tax_name , field_name , obj_field):
    """
    :param tax_name:
    :param carbon_source:
    :param objects: 实例
    :param field_name: 字段名称
    :param obj_field: 字段的值
    :return:状态，参考范围
    """
    obj = ReferenceRange.objects.filter(
        index_name = objects._meta.get_field( field_name ).verbose_name , carbon_source = carbon_source ,
        tax_name = tax_name ) [0]  # TODO 挑选一个离近期最近的对象
    mi = obj.min_value
    ma = obj.max_value
    mi = float( mi )
    ma = float( ma )
    if obj_field is None:
        return None , None
    else:
        if obj_field < mi:
            obj_field_status = 2  # 偏低
        elif obj_field > ma:
            obj_field_status = 0  # 偏高
        else:
            obj_field_status = 1  # 正常
        result = obj.reference_range
    return obj_field_status , result


class ConventionalIndexResource( resources.ModelResource ):
    class Meta:
        model = ConventionalIndex
        skip_unchanged = True
        fields = (
            'id' , 'sample_number' , 'internal_number' , 'carbon_source' , 'genus' , 'carbon_source_zh' , 'genus_zh' ,
            'occult_Tf' ,
            'occult_Hb' , 'hp' , 'calprotectin' ,
            'ph_value' ,
            'sample_type' , 'colour')
        export_order = (
            'id' , 'sample_number' , 'internal_number' , 'carbon_source' , 'genus' , 'carbon_source_zh' , 'genus_zh' ,
            'occult_Tf' ,
            'occult_Hb' , 'hp' , 'calprotectin' ,
            'ph_value' ,
            'sample_type' , 'colour')

    def get_diff_headers(self):
        return ['id' , '样本编号' , '对内编号' , '碳源' , '菌种' , '碳源中文名称' , '菌种中文名称' , '潜血双联-Tf' , '潜血双联-Hb' ,
                '幽门螺旋杆菌 抗原（HP-Ag）' ,
                '钙卫蛋白' , 'PH值' ,
                '样本类型' , '颜色']

    def get_export_headers(self):
        return ['id' , '样本编号' , '对内编号' , '碳源' , '菌种' , '碳源中文名称' , '菌种中文名称' , '潜血双联-Tf' , '潜血双联-Hb' ,
                '幽门螺旋杆菌 抗原（HP-Ag）' ,
                '钙卫蛋白' , 'PH值' ,
                '样本类型' , '颜色']

    def before_import_row(self , row , **kwargs):
        """
        Calls :meth:`import_export.fields.Field.save` if ``Field.attribute``
        and ``Field.column_name`` are found in ``data``.
        """
        sampless = Sample.objects.filter( sample_number = row ['样本编号'] )
        carbons = Carbon.objects.filter( id = row ['碳源'] )
        genuss = Genus.objects.filter( id = row ['菌种'] )
        if sampless.count( ) == 0:
            raise forms.ValidationError( '样本编号有误，请到样本接收数据中核实。' )
        if carbons.count( ) == 0:
            raise forms.ValidationError( '碳源名称有误，请到基础数据中核实。' )
        if genuss.count( ) == 0:
            raise forms.ValidationError( '菌属名称有误，请到基础数据中核实。' )
        occult_Tf_referenceRange = ReferenceRange.objects.filter( index_name = ConventionalIndex._meta.get_field(
            'occult_Tf' ).verbose_name , carbon_source = carbons [0] , tax_name = genuss [0].english_name )
        occult_Hb_referenceRange = ReferenceRange.objects.filter( index_name = ConventionalIndex._meta.get_field(
            'occult_Hb' ).verbose_name , carbon_source = carbons [0] , tax_name = genuss [0].english_name )
        hp_referenceRange = ReferenceRange.objects.filter( index_name = ConventionalIndex._meta.get_field(
            'hp' ).verbose_name )
        calprotectin_referenceRange = ReferenceRange.objects.filter( index_name = ConventionalIndex._meta.get_field(
            'calprotectin' ).verbose_name , carbon_source = carbons [0] , tax_name = genuss [0].english_name )
        ph_value_referenceRange = ReferenceRange.objects.filter( index_name = ConventionalIndex._meta.get_field(
            'ph_value' ).verbose_name , carbon_source = carbons [0] , tax_name = genuss [0].english_name )
        if occult_Tf_referenceRange.count( ) == 0:
            raise forms.ValidationError( '%s 潜血双联-Tf参考参考范围有误，请到基础数据中核实。' % (genuss [0].english_name) )
        if occult_Hb_referenceRange.count( ) == 0:
            raise forms.ValidationError( '%s 潜血双联-Hb参考参考范围有误，请到基础数据中核实。' % (genuss [0].english_name) )
        if hp_referenceRange.count( ) == 0:
            raise forms.ValidationError( '%s 幽门螺旋杆菌 抗原（HP-Ag）参考参考范围有误，请到基础数据中核实。' % (genuss [0].english_name) )
        if calprotectin_referenceRange.count( ) == 0:
            raise forms.ValidationError( '%s 钙卫蛋白参考参考范围有误，请到基础数据中核实。' % (genuss [0].english_name) )
        if ph_value_referenceRange.count( ) == 0:
            raise forms.ValidationError( '%s PH值参考参考范围有误，请到基础数据中核实。' % (genuss [0].english_name) )

    def get_or_init_instance(self , instance_loader , row):
        """
        Either fetches an already existing instance or initializes a new one.
        """
        instance = self.get_instance( instance_loader , row )
        row ['sample_number'] = row ['样本编号']
        row ['internal_number'] = row ['对内编号']
        row ['carbon_source'] = row ['碳源']
        row ['carbon_source_zh'] = row ['碳源中文名称']
        row ['genus_zh'] = row ['菌种中文名称']
        row ['genus'] = row ['菌种']
        row ['occult_Tf'] = row ['潜血双联-Tf']
        row ['occult_Hb'] = row ['潜血双联-Hb']
        row ['hp'] = row ['幽门螺旋杆菌 抗原（HP-Ag）']
        row ['calprotectin'] = row ['钙卫蛋白']
        row ['ph_value'] = row ['PH值']
        row ['sample_type'] = row ['样本类型']
        row ['colour'] = row ['颜色']
        if instance:
            return instance , False
        else:
            return self.init_instance( row ) , True

    def before_save_instance(self , instance , using_transactions , dry_run):
        """
            Override to add additional logic. Does nothing by default.
        """
        if ReferenceRange.objects.filter( index_name = ConventionalIndex._meta.get_field(
                'occult_Tf' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
            status , reference_range = get_status( ConventionalIndex , instance.carbon_source ,
                                                   instance.genus.english_name , 'occult_Tf' ,
                                                   instance.occult_Tf )
            instance.occult_Tf_reference_range = reference_range
            instance.occult_Tf_status = status
        if ReferenceRange.objects.filter( index_name = ConventionalIndex._meta.get_field(
                'occult_Tf' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
            status , reference_range = get_status( ConventionalIndex , instance.carbon_source ,
                                                   instance.genus.english_name , 'occult_Hb' ,
                                                   instance.occult_Hb )
            instance.occult_Hb_reference_range = reference_range
            instance.occult_Hb_status = status
        if ReferenceRange.objects.filter( index_name = ConventionalIndex._meta.get_field(
                'hp' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
            status , reference_range = get_status( ConventionalIndex , instance.carbon_source ,
                                                   instance.genus.english_name , 'hp' , instance.hp )
            instance.hp_reference_range = reference_range
            instance.hp_status = status
        if ReferenceRange.objects.filter( index_name = ConventionalIndex._meta.get_field(
                'calprotectin' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
            status , reference_range = get_status( ConventionalIndex , instance.carbon_source ,
                                                   instance.genus.english_name , 'calprotectin' ,
                                                   instance.calprotectin )
            instance.calprotectin_reference_range = reference_range
            instance.calprotectin_status = status
        if instance.ph_value is not None:
            if ReferenceRange.objects.filter( index_name = ConventionalIndex._meta.get_field(
                    'ph_value' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
                status , reference_range = get_status( ConventionalIndex , instance.carbon_source ,
                                                       instance.genus.english_name , 'ph_value' ,
                                                       instance.ph_value )
                instance.ph_value_reference_range = reference_range
                instance.ph_value_status = status


@admin.register( ConventionalIndex )
class ConventionalIndexAdmin( ImportExportActionModelAdmin , admin.ModelAdmin ):
    list_display = (
        'id' , 'sample_number' , 'internal_number' , 'carbon_source' , 'genus' , 'occult_Tf_status_colored' ,
        'occult_Hb_status_colored' ,
        'hp_status_colored' ,
        'calprotectin_status_colored' ,
        'ph_value_status_colored' ,
        'sample_type' , 'colour' , 'is_status')
    list_display_links = ('sample_number' ,)
    ordering = ('-id' ,)
    view_on_site = False
    list_max_show_all = 100
    list_per_page = 20
    list_filter = ('is_status' ,)
    search_fields = ('sample_number' ,)
    resource_class = ConventionalIndexResource
    # form = ConventionalIndexForm
    # list_editable =
    actions = ['make_finish' , 'export_admin_action' , 'make_risk']

    def occult_Tf_status_colored(self , obj):
        if obj.occult_Tf_status == 0:
            return format_html( '<b style="background:{};">{}</b>' , 'red' , "异常" )
        elif obj.occult_Tf_status == 2:
            return format_html( '<b style="background:{};">{}</b>' , 'blue' , obj.get_occult_Tf_status_display( ) )
        else:
            return obj.get_occult_Tf_status_display( )

    occult_Tf_status_colored.short_description = "潜血双联-Tf状态"

    def occult_Hb_status_colored(self , obj):
        if obj.occult_Hb_status == 0:
            return format_html( '<b style="background:{};">{}</b>' , 'red' , "异常" )
        elif obj.occult_Hb_status == 2:
            return format_html( '<b style="background:{};">{}</b>' , 'blue' , obj.get_occult_Hb_status_display( ) )
        else:
            return obj.get_occult_Hb_status_display( )

    occult_Hb_status_colored.short_description = "潜血双联-Hb状态"

    def hp_status_colored(self , obj):
        if obj.hp_status == 0:
            return format_html( '<b style="background:{};">{}</b>' , 'red' , "异常" )
        elif obj.hp_status == 2:
            return format_html( '<b style="background:{};">{}</b>' , 'blue' , obj.get_hp_status_display( ) )
        else:
            return obj.get_hp_status_display( )

    hp_status_colored.short_description = "幽门螺旋杆菌抗原状态"

    def calprotectin_status_colored(self , obj):
        if obj.calprotectin_status == 0:
            return format_html( '<b style="background:{};">{}</b>' , 'red' , "异常" )  # TODO 偏高改为异常
        elif obj.calprotectin_status == 2:
            return format_html( '<b style="background:{};">{}</b>' , 'blue' , obj.get_calprotectin_status_display( ) )
        else:
            return obj.get_calprotectin_status_display( )

    calprotectin_status_colored.short_description = "钙卫蛋白状态"

    def ph_value_status_colored(self , obj):
        if obj.ph_value_status == 0:
            return format_html( '<b style="background:{};">{}</b>' , 'red' , obj.get_ph_value_status_display( ) )
        elif obj.ph_value_status == 2:
            return format_html( '<b style="background:{};">{}</b>' , 'blue' , obj.get_ph_value_status_display( ) )
        else:
            return obj.get_ph_value_status_display( )

    ph_value_status_colored.short_description = "PH值状态"

    def get_readonly_fields(self , request , obj=None):
        # 根据 obj 是否为空来判断,修改数据时不能修改样本编号，
        if obj:
            self.readonly_fields = (
                'sample_number' , 'carbon_source' , 'genus' , 'occult_Tf_status' , 'occult_Tf_reference_range' ,
                'occult_Hb_status' , 'occult_Hb_reference_range' , 'hp_status' , 'hp_reference_range' ,
                'calprotectin_status' , 'calprotectin_reference_range' , 'ph_value_status' ,
                'ph_value_reference_range' , 'carbon_source_zh' , 'genus_zh' ,
                'is_status')
        else:
            self.readonly_fields = ()
        if request.user.is_superuser:
            self.readonly_fields = ()
        return self.readonly_fields

    def get_export_formats(self):
        """
        Returns available export formats.
        """
        formats = (
            base_formats.CSV ,
            base_formats.XLS ,
            base_formats.XLSX ,
            base_formats.TSV ,
        )
        return [f for f in formats if f( ).can_export( )]

    def get_import_formats(self):
        """
        Returns available export formats.
        """
        formats = (
            base_formats.CSV ,
            base_formats.XLS ,
            base_formats.XLSX ,
            base_formats.TSV ,
        )
        return [f for f in formats if f( ).can_import( )]

    def make_finish(self , request , queryset):
        i = 0  # 提交成功的数据
        n = 0  # 提交过的数量
        t = 0  # 选中状态
        for obj in queryset:
            t += 1
            if obj.is_status < 1:
                '''初始化偏高，偏低的异常状态'''
                conventional_unusual , conventional_unusual_created = IndexesUnusual.objects.get_or_create(
                    sample_number = obj.sample_number , check_type = "常规指标" )
                if conventional_unusual_created:
                    unusual_high = ""  # 偏高结果
                    unusual_low = ""  # 偏低结果
                else:
                    unusual_high = conventional_unusual.high
                    unusual_low = conventional_unusual.low
                obj_progress , created = Progress.objects.get_or_create( sample_number = obj.sample_number )
                if obj_progress.is_cgzb:
                    obj.is_status = 1  # 1是标记为完成的
                    obj.save( )
                    ''' 整理异常检测结果 '''
                    for key , status in {"occult_Tf": obj.occult_Tf_status , "occult_Hb": obj.occult_Hb_status ,
                                         "calprotectin": obj.calprotectin_status , "hp": obj.hp_status}.items( ):
                        if status == 0:
                            unusual_high = "%s,%s;" % (  # 常规指标，展示形式'''PH值;PH值;'''
                                unusual_high ,
                                ConventionalIndex._meta.get_field( key ).verbose_name)
                            '''MetaRiskIndexes   GutRiskIndexes信息新增一条'''
                            if obj.carbon_source.name == "粪便":
                                create_risk( obj , key , ConventionalIndex , "偏高" , False )
                    if obj.ph_value_status != 1:
                        if obj.ph_value_status == 0:
                            unusual_high = "%s,%s;" % (  # 常规指标，展示形式'''PH值;PH值;'''
                                unusual_high ,
                                ConventionalIndex._meta.get_field( "ph_value" ).verbose_name)
                            if obj.carbon_source.name == "粪便":
                                create_risk( obj , "ph_value" , ConventionalIndex , "偏高" )
                        else:
                            unusual_low = "%s,%s;" % (  # 常规指标，展示形式'''PH值;PH值;'''
                                unusual_low ,
                                ConventionalIndex._meta.get_field(
                                    "ph_value" ).verbose_name)
                            if obj.carbon_source.name == "粪便":
                                create_risk( obj , "ph_value" , ConventionalIndex , "偏低" )

                    ''' 把异常检测结果存到数据库中 '''
                    conventional_unusual.high = unusual_high
                    conventional_unusual.low = unusual_low
                    conventional_unusual.save( )
                    if (unusual_high == "") and (unusual_low == ""):
                        conventional_unusual.delete( )
                    i += 1
                else:
                    n += 1
            else:
                n += 1
        self.message_user( request , '选择%s条信息，完成操作%s条，不操作%s条' % (t , i , n) , level = messages.SUCCESS )

    make_finish.short_description = '1标记完成'

    def make_risk(self , request , queryset):
        '''代谢水平判读'''
        risk_items = RiskItem.objects.filter( risk_type_number = "FXDL0002" ,
                                              check_type_number = "JCDL0002" )  # 代谢水平判读; 常规指标项
        meta_risk = get_meta_risk( risk_items )
        '''肠道免疫'''
        risk_items = RiskItem.objects.filter( risk_type_number = "FXDL0003" ,
                                              check_type_number = "JCDL0002" )  # 代谢水平判读; 常规指标项
        gut_risk = get_meta_risk( risk_items )
        i = 0  # 提交成功的数据
        n = 0  # 提交过的数量
        t = 0  # 选中状态
        no_err = True  # 用户判断有误风险默认值
        for obj in queryset:
            t += 1
            if obj.is_status == 1:
                '''修改初始化偏高，偏低的异常状态的数值'''
                meta_risk_indexes = MetaRiskIndexes.objects.filter( sample_number = obj.sample_number )
                if meta_risk_indexes.count( ) > 0:
                    for meta_risk_index in meta_risk_indexes:
                        if meta_risk_index.index_name in meta_risk:
                            riskItemDefaults = RiskItemDefault.objects.filter( risk_name = "血脂" ,
                                                                               risk_type_number = "FXDL0002" ,
                                                                               index_name = meta_risk_index.index_name )
                            if riskItemDefaults.count( ) == 0:
                                self.message_user( request ,
                                                   '血脂 FXDL0002 %s 风险指标默认值没有，请先在基础数据中心添加' % meta_risk_index.index_name ,
                                                   level = messages.ERROR )
                                no_err = False
                                break
                            if meta_risk_index.is_status == "偏高":
                                meta_risk_index.blood_fat = RiskItemDefault.objects.get( risk_name = "血脂" ,
                                                                                         isk_type_number = "FXDL0002" ,
                                                                                         index_name = meta_risk_index.index_name ).high_value
                                meta_risk_index.fat = RiskItemDefault.objects.get( risk_name = "肥胖" ,
                                                                                   risk_type_number = "FXDL0002" ,
                                                                                   index_name = meta_risk_index.index_name ).high_value
                            elif meta_risk_index.is_status == "偏低":
                                meta_risk_index.blood_fat = RiskItemDefault.objects.get( risk_name = "血脂" ,
                                                                                         risk_type_number = "FXDL0002" ,
                                                                                         index_name = meta_risk_index.index_name ).low_value
                                meta_risk_index.fat = RiskItemDefault.objects.get( risk_name = "肥胖" ,
                                                                                   risk_type_number = "FXDL0002" ,
                                                                                   index_name = meta_risk_index.index_name ).low_value
                            meta_risk_index.save( )
                gut_risk_indexes = GutRiskIndexes.objects.filter( sample_number = obj.sample_number )
                if gut_risk_indexes.count( ) > 0:
                    for gut_risk_index in gut_risk_indexes:
                        if gut_risk_index.index_name in gut_risk:
                            riskItemDefaults = RiskItemDefault.objects.filter( risk_name = "肠道炎症" ,
                                                                               risk_type_number = "FXDL0003" ,
                                                                               index_name = gut_risk_index.index_name )
                            if riskItemDefaults.count( ) == 0:
                                self.message_user( request ,
                                                   '肠道炎症  FXDL0003 %s 风险指标默认值没有，请先在基础数据中心添加' % gut_risk_index.index_name ,
                                                   level = messages.ERROR )
                                no_err = False
                                break
                            if gut_risk_index.is_status == "偏高":
                                gut_risk_index.infection = RiskItemDefault.objects.get( risk_name = "肠道炎症" ,
                                                                                        risk_type_number = "FXDL0003" ,
                                                                                        index_name = gut_risk_index.index_name ).high_value
                                gut_risk_index.scherm = RiskItemDefault.objects.get( risk_name = "肠道屏障" ,
                                                                                     risk_type_number = "FXDL0003" ,
                                                                                     index_name = gut_risk_index.index_name ).high_value
                                gut_risk_index.cancer = RiskItemDefault.objects.get( risk_name = "消化道肿瘤" ,
                                                                                     risk_type_number = "FXDL0003" ,
                                                                                     index_name = gut_risk_index.index_name ).high_value
                            elif gut_risk_index.is_status == "偏低":
                                gut_risk_index.infection = RiskItemDefault.objects.get( risk_name = "肠道炎症" ,
                                                                                        risk_type_number = "FXDL0003" ,
                                                                                        index_name = gut_risk_index.index_name ).low_value
                                gut_risk_index.scherm = RiskItemDefault.objects.get( risk_name = "肠道屏障" ,
                                                                                     risk_type_number = "FXDL0003" ,
                                                                                     index_name = gut_risk_index.index_name ).low_value
                                gut_risk_index.cancer = RiskItemDefault.objects.get( risk_name = "消化道肿瘤" ,
                                                                                     risk_type_number = "FXDL0003" ,
                                                                                     index_name = gut_risk_index.index_name ).low_value
                            gut_risk_index.save( )
                i += 1
                if no_err:
                    obj_progress , created = Progress.objects.get_or_create( sample_number = obj.sample_number )
                    if obj_progress.is_cgzb:
                        obj_progress.cgzb_testing_date = datetime.date.today( )
                        obj_progress.cgzb_testing_staff = request.user.last_name + ' ' + request.user.first_name
                        obj_progress.save( )
                        obj.is_status = 2  # 2是标记为完成并判读的
                        obj.save( )
                else:
                    n += 1
            else:
                n += 1
        self.message_user( request , '选择%s条信息，完成操作%s条，不操作%s条' % (t , i , n) , level = messages.SUCCESS )

    make_risk.short_description = '2标记风险'

    def save_model(self , request , obj , form , change):
        if obj.occult_Tf is not None:
            if ReferenceRange.objects.filter( index_name = ConventionalIndex._meta.get_field(
                    'occult_Tf' ).verbose_name , carbon_source = obj.carbon_source ,
                                              tax_name = obj.genus.english_name ).count( ) != 0:  # 根据字段的名称查询参考访问
                status , reference_range = get_status( ConventionalIndex , obj.carbon_source ,
                                                       obj.genus.english_name , 'occult_Tf' , obj.occult_Tf )
                obj.occult_Tf_reference_range = reference_range
                obj.occult_Tf_status = status
            else:
                self.message_user( request , '潜血双联-Tf 检测指标没有参考范围的基础数据，请先添加基础数据中心' , level = messages.ERROR )

        if obj.occult_Hb is not None:
            if ReferenceRange.objects.filter( index_name = ConventionalIndex._meta.get_field(
                    'occult_Hb' ).verbose_name , carbon_source = obj.carbon_source ,
                                              tax_name = obj.genus.english_name ).count( ) != 0:  # 根据字段的名称查询参考访问
                status , reference_range = get_status( ConventionalIndex , obj.carbon_source ,
                                                       obj.genus.english_name , 'occult_Hb' , obj.occult_Hb )
                obj.occult_Hb_reference_range = reference_range
                obj.occult_Hb_status = status

            else:
                self.message_user( request , '潜血双联-Hb 检测指标没有参考范围的基础数据，请先添加基础数据中心' , level = messages.ERROR )

        if obj.hp is not None:
            if ReferenceRange.objects.filter( index_name = ConventionalIndex._meta.get_field(
                    'hp' ).verbose_name , carbon_source = obj.carbon_source ,
                                              tax_name = obj.genus.english_name ).count( ) != 0:  # 根据字段的名称查询参考访问
                status , reference_range = get_status( ConventionalIndex , obj.carbon_source ,
                                                       obj.genus.english_name , 'hp' , obj.hp )
                obj.hp_reference_range = reference_range
                obj.hp_status = status
            else:
                self.message_user( request , '幽门螺旋杆菌 抗原（HP-Ag）检测指标没有参考范围的基础数据，请先添加基础数据中心' , level = messages.ERROR )

        if obj.calprotectin is not None:
            if ReferenceRange.objects.filter( index_name = ConventionalIndex._meta.get_field(
                    'calprotectin' ).verbose_name , carbon_source = obj.carbon_source ,
                                              tax_name = obj.genus.english_name ).count( ) != 0:  # 根据字段的名称查询参考访问
                status , reference_range = get_status( ConventionalIndex , obj.carbon_source ,
                                                       obj.genus.english_name , 'calprotectin' ,
                                                       obj.calprotectin )
                obj.calprotectin_reference_range = reference_range
                obj.calprotectin_status = status
            else:
                self.message_user( request , '钙卫蛋白状态 检测指标没有参考范围的基础数据，请先添加基础数据中心' , level = messages.ERROR )

        if obj.ph_value is not None:
            if ReferenceRange.objects.filter( index_name = ConventionalIndex._meta.get_field(
                    'ph_value' ).verbose_name , carbon_source = obj.carbon_source ,
                                              tax_name = obj.genus.english_name ).count( ) != 0:  # 根据字段的名称查询参考访问

                status , reference_range = get_status( ConventionalIndex , obj.carbon_source ,
                                                       obj.genus.english_name , 'ph_value' , obj.ph_value )
                obj.ph_value_reference_range = reference_range
                obj.ph_value_status = status

            else:
                self.message_user( request , 'PH值 检测指标没有参考范围的基础数据，请先添加基础数据中心' , level = messages.ERROR )
        obj.save( )


class BioChemicalIndexesResource( resources.ModelResource ):
    class Meta:
        model = BioChemicalIndexes
        skip_unchanged = True
        fields = (
            'id' , 'sample_number' , 'internal_number' , 'carbon_source' , 'genus' , 'carbon_source_zh' , 'genus_zh' ,
            'fecal_nitrogen' ,
            'bile_acid')
        export_order = (
            'id' , 'sample_number' , 'internal_number' , 'carbon_source' , 'genus' , 'carbon_source_zh' , 'genus_zh' ,
            'fecal_nitrogen' ,
            'bile_acid')

    def get_diff_headers(self):
        return ['id' , '样本编号' , '对内编号' , '碳源' , '菌种' , '碳源中文名称' , '菌种中文名称' , '粪氨' , '胆汁酸']

    def get_export_headers(self):
        return ['id' , '样本编号' , '对内编号' , '碳源' , '菌种' , '碳源中文名称' , '菌种中文名称' , '粪氨' , '胆汁酸']

    def before_import_row(self , row , **kwargs):
        """
        Calls :meth:`import_export.fields.Field.save` if ``Field.attribute``
        and ``Field.column_name`` are found in ``data``.
        """
        sampless = Sample.objects.filter( sample_number = row ['样本编号'] )
        carbons = Carbon.objects.filter( id = row ['碳源'] )
        genuss = Genus.objects.filter( id = row ['菌种'] )
        if sampless.count( ) == 0:
            raise forms.ValidationError( '样本编号有误，请到样本接收数据中核实。' )
        if carbons.count( ) == 0:
            raise forms.ValidationError( '碳源名称有误，请到基础数据中核实。' )
        if genuss.count( ) == 0:
            raise forms.ValidationError( '菌属名称有误，请到基础数据中核实。' )
        fecal_nitrogen_referenceRange = ReferenceRange.objects.filter( index_name = BioChemicalIndexes._meta.get_field(
            'fecal_nitrogen' ).verbose_name , carbon_source = carbons [0] , tax_name = genuss [0].english_name )
        bile_acid_referenceRange = ReferenceRange.objects.filter( index_name = BioChemicalIndexes._meta.get_field(
            'bile_acid' ).verbose_name , carbon_source = carbons [0] , tax_name = genuss [0].english_name )
        if fecal_nitrogen_referenceRange.count( ) == 0:
            raise forms.ValidationError( '%s 粪氨参考参考范围有误，请到基础数据中核实。' % (genuss [0].english_name) )
        if bile_acid_referenceRange.count( ) == 0:
            raise forms.ValidationError( '%s 胆汁酸参考参考范围有误，请到基础数据中核实。' % (genuss [0].english_name) )

    def get_or_init_instance(self , instance_loader , row):
        """
        Either fetches an already existing instance or initializes a new one.
        """
        instance = self.get_instance( instance_loader , row )
        row ['sample_number'] = row ['样本编号']
        row ['internal_number'] = row ['对内编号']
        row ['carbon_source'] = row ['碳源']
        row ['genus'] = row ['菌种']
        row ['carbon_source_zh'] = row ['碳源中文名称']
        row ['genus_zh'] = row ['菌种中文名称']
        row ['fecal_nitrogen'] = row ['粪氨']
        row ['bile_acid'] = row ['胆汁酸']
        if instance:
            return instance , False
        else:
            return self.init_instance( row ) , True

    def before_save_instance(self , instance , using_transactions , dry_run):
        """
            Override to add additional logic. Does nothing by default.
        """
        if ReferenceRange.objects.filter( index_name = BioChemicalIndexes._meta.get_field(
                'fecal_nitrogen' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
            status , reference_range = get_status( BioChemicalIndexes , instance.carbon_source ,
                                                   instance.genus.english_name , 'fecal_nitrogen' ,
                                                   instance.fecal_nitrogen )
            instance.fecal_nitrogen_reference_range = reference_range
            instance.fecal_nitrogen_status = status
        if ReferenceRange.objects.filter( index_name = BioChemicalIndexes._meta.get_field(
                'bile_acid' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
            status , reference_range = get_status( BioChemicalIndexes , instance.carbon_source ,
                                                   instance.genus.english_name , 'bile_acid' ,
                                                   instance.bile_acid )
            instance.bile_acid_reference_range = reference_range
            instance.bile_acid_status = status


class BioChemicalIndexesForm( forms.ModelForm ):
    fecal_nitrogen = forms.DecimalField( label = "粪氨" , help_text = "单位：μmol/g wet feces" , required = True ,
                                         widget = forms.NumberInput(
                                             attrs = {'class': ' form-control' , 'placeholder': '示例：26.79'} ) ,
                                         error_messages = {'required': '单位：μmol/g wet feces'} )
    bile_acid = forms.DecimalField( label = "粪胆汁酸" , help_text = "单位：μmol/g wet feces" , required = True ,
                                    widget = forms.NumberInput(
                                        attrs = {'class': ' form-control' , 'placeholder': '示例：4.15'} ) ,
                                    error_messages = {'required': '单位：μmol/g wet feces'} )

    class Meta:
        model = BioChemicalIndexes
        exclude = ('' ,)


@admin.register( BioChemicalIndexes )
class BioChemicalIndexesAdmin( ImportExportActionModelAdmin , admin.ModelAdmin ):
    list_display = (
        'id' , 'sample_number' , 'internal_number' , 'carbon_source' , 'genus' , 'fecal_nitrogen' ,
        'fecal_nitrogen_status_colored' ,
        'bile_acid' ,
        'bile_acid_status_colored' , 'is_status')
    list_display_links = ('sample_number' ,)
    ordering = ('-id' ,)
    view_on_site = False
    list_max_show_all = 100
    list_per_page = 20
    list_filter = ('is_status' ,)
    search_fields = ('sample_number' ,)
    resource_class = BioChemicalIndexesResource
    form = BioChemicalIndexesForm
    # list_editable =
    actions = ['make_finish' , 'export_admin_action' , 'make_risk']

    def fecal_nitrogen_status_colored(self , obj):
        if obj.fecal_nitrogen_status == 0:
            return format_html( '<b style="background:{};">{}</b>' , 'red' , obj.get_fecal_nitrogen_status_display( ) )
        elif obj.fecal_nitrogen_status == 2:
            return format_html( '<b style="background:{};">{}</b>' , 'blue' , obj.get_fecal_nitrogen_status_display( ) )
        else:
            return obj.get_fecal_nitrogen_status_display( )

    fecal_nitrogen_status_colored.short_description = "粪氨状态"

    def bile_acid_status_colored(self , obj):
        if obj.bile_acid_status == 0:
            return format_html( '<b style="background:{};">{}</b>' , 'red' , obj.get_bile_acid_status_display( ) )
        elif obj.bile_acid_status == 2:
            return format_html( '<b style="background:{};">{}</b>' , 'blue' , obj.get_bile_acid_status_display( ) )
        else:
            return obj.get_bile_acid_status_display( )

    bile_acid_status_colored.short_description = "胆汁酸状态"

    def get_readonly_fields(self , request , obj=None):
        # 根据 obj 是否为空来判断,修改数据时不能修改样本编号，
        if obj:
            self.readonly_fields = (
                'sample_number' , 'carbon_source' , 'genus' , 'fecal_nitrogen_status' ,
                'fecal_nitrogen_reference_range' ,
                'bile_acid_status' , 'bile_acid_reference_range' , 'is_status' , 'carbon_source_zh' , 'genus_zh')
        else:
            self.readonly_fields = ()
        if request.user.is_superuser:
            self.readonly_fields = ()
        return self.readonly_fields

    def get_export_formats(self):
        """
        Returns available export formats.
        """
        formats = (
            base_formats.CSV ,
            base_formats.XLS ,
            base_formats.XLSX ,
            base_formats.TSV ,
        )
        return [f for f in formats if f( ).can_export( )]

    def get_import_formats(self):
        """
        Returns available export formats.
        """
        formats = (
            base_formats.CSV ,
            base_formats.XLS ,
            base_formats.XLSX ,
            base_formats.TSV ,
        )
        return [f for f in formats if f( ).can_import( )]

    def make_finish(self , request , queryset):
        i = 0  # 提交成功的数据
        n = 0  # 提交过的数量
        t = 0  # 选中状态
        for obj in queryset:
            t += 1
            if obj.is_status < 1:
                '''初始化偏高，偏低的异常状态'''
                bio_unusual , bio_unusual_created = IndexesUnusual.objects.get_or_create(
                    sample_number = obj.sample_number , check_type = "生化检测" )
                if bio_unusual_created:
                    unusual_high = ""  # 偏高结果
                    unusual_low = ""  # 偏低结果
                else:
                    unusual_high = bio_unusual.high
                    unusual_low = bio_unusual.low
                obj_progress , created = Progress.objects.get_or_create( sample_number = obj.sample_number )
                if obj_progress.is_shzb:
                    obj.is_status = 1  # 1是标记为完成的
                    obj.save( )
                    ''' 整理异常检测结果 '''
                    for key , status in {"fecal_nitrogen": obj.fecal_nitrogen_status ,
                                         "bile_acid": obj.bile_acid_status}.items( ):
                        if status != 1:
                            if status == 0:
                                unusual_high = "%s,%s;" % (  # 常规指标，展示形式'''胆汁酸;'''
                                    unusual_high ,
                                    BioChemicalIndexes._meta.get_field( key ).verbose_name)
                                if obj.carbon_source.name == "粪便":
                                    create_risk( obj , key , BioChemicalIndexes , "偏高" , False )
                            else:
                                unusual_low = "%s,%s;" % (
                                    unusual_low ,
                                    BioChemicalIndexes._meta.get_field( key ).verbose_name)
                                if obj.carbon_source.name == "粪便":
                                    create_risk( obj , key , BioChemicalIndexes , "偏低" , False )
                    ''' 把异常检测结果存到数据库中 '''
                    bio_unusual.high = unusual_high
                    bio_unusual.low = unusual_low
                    bio_unusual.save( )
                    i += 1
                else:
                    n += 1
            else:
                n += 1
        self.message_user( request , '选择%s条信息，完成操作%s条，不操作%s条' % (t , i , n) , level = messages.SUCCESS )

    make_finish.short_description = '1标记完成'

    def make_risk(self , request , queryset):
        '''代谢水平判读'''
        risk_items = RiskItem.objects.filter( risk_type_number = "FXDL0002" ,
                                              check_type_number = "JCDL0003" )  # 代谢水平判读; 生化指标项
        meta_risk = get_meta_risk( risk_items )
        i = 0  # 提交成功的数据
        n = 0  # 提交过的数量
        t = 0  # 选中状态
        no_err = True
        for obj in queryset:
            t += 1
            if obj.is_status == 1:
                '''修改初始化偏高，偏低的异常状态的数值'''
                meta_risk_indexes = MetaRiskIndexes.objects.filter( sample_number = obj.sample_number )
                if meta_risk_indexes.count( ) > 0:
                    for meta_risk_index in meta_risk_indexes:
                        if meta_risk_index.index_name in meta_risk:
                            riskItemDefaults = RiskItemDefault.objects.filter( risk_name = "血脂" ,
                                                                               risk_type_number = "FXDL0002" ,
                                                                               index_name = meta_risk_index.index_name )
                            if riskItemDefaults.count( ) == 0:
                                self.message_user( request , '风险指标默认值没有，请先在基础数据中心添加' ,
                                                   level = messages.ERROR )
                                no_err = False
                                break
                            if meta_risk_index.is_status == "偏高":

                                meta_risk_index.blood_fat = RiskItemDefault.objects.get( risk_name = "血脂" ,
                                                                                         risk_type_number = "FXDL0002" ,
                                                                                         index_name = meta_risk_index.index_name ).high_value
                                meta_risk_index.fat = RiskItemDefault.objects.get( risk_name = "肥胖" ,
                                                                                   risk_type_number = "FXDL0002" ,
                                                                                   index_name = meta_risk_index.index_name ).high_value
                            elif meta_risk_index.is_status == "偏低":
                                meta_risk_index.blood_fat = RiskItemDefault.objects.get( risk_name = "血脂" ,
                                                                                         risk_type_number = "FXDL0002" ,
                                                                                         index_name = meta_risk_index.index_name ).low_value
                                meta_risk_index.fat = RiskItemDefault.objects.get( risk_name = "肥胖" ,
                                                                                   risk_type_number = "FXDL0002" ,
                                                                                   index_name = meta_risk_index.index_name ).low_value
                            meta_risk_index.save( )
                i += 1  # 提交成功数量
                if no_err:
                    obj_progress , created = Progress.objects.get_or_create( sample_number = obj.sample_number )
                    if obj_progress.is_shzb:
                        obj_progress.shzb_testing_date = datetime.date.today( )
                        obj_progress.shzb_testing_staff = request.user.last_name + ' ' + request.user.first_name
                        obj_progress.save( )
                        obj.is_status = 2  # 2是标记为完成并判读的
                        obj.save( )
                else:
                    n += 1
            else:
                n += 1
        self.message_user( request , '选择%s条信息，完成操作%s条，不操作%s条' % (t , i , n) , level = messages.SUCCESS )

    make_risk.short_description = '2标记风险'

    def save_model(self , request , obj , form , change):
        if obj.fecal_nitrogen is not None:
            if ReferenceRange.objects.filter( index_name = BioChemicalIndexes._meta.get_field(
                    'fecal_nitrogen' ).verbose_name , carbon_source = obj.carbon_source ,
                                              tax_name = obj.genus.english_name ).count( ) != 0:  # 根据字段的名称查询参考访问
                status , reference_range = get_status( BioChemicalIndexes , obj.carbon_source ,
                                                       obj.genus.english_name , 'fecal_nitrogen' ,
                                                       obj.fecal_nitrogen )
                obj.fecal_nitrogen_reference_range = reference_range
                obj.fecal_nitrogen_status = status
            else:
                self.message_user( request , '粪氨 检测指标没有参考范围的基础数据，请先添加基础数据中心' , level = messages.ERROR )
        obj.save( )

        if obj.bile_acid is not None:
            if ReferenceRange.objects.filter( index_name = BioChemicalIndexes._meta.get_field(
                    'bile_acid' ).verbose_name , carbon_source = obj.carbon_source ,
                                              tax_name = obj.genus.english_name ).count( ) != 0:  # 根据字段的名称查询参考访问
                status , reference_range = get_status( BioChemicalIndexes , obj.carbon_source ,
                                                       obj.genus.english_name , 'bile_acid' , obj.bile_acid )
                obj.bile_acid_reference_range = reference_range
                obj.bile_acid_status = status

            else:
                self.message_user( request , '胆汁酸 检测指标没有参考范围的基础数据，请先添加基础数据中心' , level = messages.ERROR )
        obj.save( )


class QpcrIndexesResource( resources.ModelResource ):
    class Meta:
        model = QpcrIndexes
        skip_unchanged = True
        fields = (
            'id' , 'sample_number' , 'internal_number' , 'carbon_source' , 'genus' , 'carbon_source_zh' , 'genus_zh' ,
            'ct' ,
            'formula_number' ,
            'concentration')
        export_order = (
            'id' , 'sample_number' , 'internal_number' , 'carbon_source' , 'genus' , 'carbon_source_zh' , 'genus_zh' ,
            'ct' ,
            'formula_number' ,
            'concentration')

    def get_diff_headers(self):
        return ['id' , '样本编号' , '对内编号' , '碳源' , '菌种' , '碳源中文名称' , '菌种中文名称' , 'ct' , '公式编号' , '浓度']

    def get_export_headers(self):
        return ['id' , '样本编号' , '对内编号' , '碳源' , '菌种' , '碳源中文名称' , '菌种中文名称' , 'ct' , '公式编号' , '浓度']

    def export(self , queryset=None , *args , **kwargs):
        """
                Exports a resource.
                """

        self.before_export( queryset , *args , **kwargs )

        if queryset is None:
            queryset = self.get_queryset( )
        headers = self.get_export_headers( )
        data = tablib.Dataset( headers = headers )

        if isinstance( queryset , QuerySet ):
            # Iterate without the queryset cache, to avoid wasting memory when
            # exporting large datasets.
            iterable = queryset.iterator( )
        else:
            iterable = queryset
        for obj in iterable:
            cts = CTformula.objects.filter( tax_name = obj.genus_zh ).order_by( "-version_num" )
            if cts.count( ) > 0:
                obj.formula_number = cts [0].number
            data.append( self.export_resource( obj ) )

        self.after_export( queryset , data , *args , **kwargs )

        return data

    def before_import_row(self , row , **kwargs):
        """
        Calls :meth:`import_export.fields.Field.save` if ``Field.attribute``
        and ``Field.column_name`` are found in ``data``.
        """
        sampless = Sample.objects.filter( sample_number = row ['样本编号'] )
        carbons = Carbon.objects.filter( id = row ['碳源'] )
        genuss = Genus.objects.filter( id = row ['菌种'] )
        formula_content = CTformula.objects.filter( number = row ['公式编号'] )
        if sampless.count( ) == 0:
            raise forms.ValidationError( '样本编号有误，请到样本接收数据中核实。' )
        if carbons.count( ) == 0:
            raise forms.ValidationError( '碳源名称有误，请到基础数据中核实。' )
        if genuss.count( ) == 0:
            raise forms.ValidationError( '菌属名称有误，请到基础数据中核实。' )
        if formula_content.count( ) == 0:
            raise forms.ValidationError( 'CT公式的编号有误，请到基础数据中核实。' )
        concentration_referenceRanges = ReferenceRange.objects.filter( index_name = QpcrIndexes._meta.get_field(
            'concentration' ).verbose_name , carbon_source = carbons [0] , tax_name = genuss [0].english_name )
        if concentration_referenceRanges.count( ) == 0:
            raise forms.ValidationError( '%s浓度参考范围有误，请到基础数据中核实' % (genuss [0].english_name) )

    def get_or_init_instance(self , instance_loader , row):
        """
        Either fetches an already existing instance or initializes a new one.
        """
        instance = self.get_instance( instance_loader , row )
        row ['sample_number'] = row ['样本编号']
        row ['internal_number'] = row ['对内编号']
        row ['carbon_source'] = row ['碳源']
        row ['genus'] = row ['菌种']
        row ['carbon_source_zh'] = row ['碳源中文名称']
        row ['genus_zh'] = row ['菌种中文名称']
        row ['concentration'] = row ['浓度']
        row ['formula_number'] = row ['公式编号']
        if instance:
            return instance , False
        else:
            return self.init_instance( row ) , True

    def before_save_instance(self , instance , using_transactions , dry_run):
        """
            Override to add additional logic. Does nothing by default.
        """
        formula_content = CTformula.objects.filter( number = instance.formula_number ) [0].formula_content
        formula = Solver( formula_content , precision = 32 )
        if instance.ct is None:
            instance.ct = 9  # TODO 当ct未检出时，提供一个默认值
        else:
            point = {'x': instance.ct}
            '''ct值为0时，不适合ct计算公式'''
            if float( instance.ct ) == 0:
                instance.concentration = 0
            else:
                instance.concentration = float( formula( point ) )
            if ReferenceRange.objects.filter( index_name = QpcrIndexes._meta.get_field(
                    'concentration' ).verbose_name , carbon_source = instance.carbon_source ,
                                              tax_name = instance.genus.english_name ).count( ) != 0:  # 根据字段的名称查询参考范围
                status , reference_range = get_status( QpcrIndexes , instance.carbon_source ,
                                                       instance.genus.english_name , 'concentration' ,
                                                       instance.concentration )
                instance.concentration_reference_range = reference_range
                instance.concentration_status = status


class QpcrIndexesForm( forms.ModelForm ):
    formula_number = forms.CharField( label = '公式唯一编号' , help_text = '基础数据管理中查询并填入' , required = True ,
                                      widget = forms.TextInput(
                                          attrs = {'class': 'form-control' , 'placeholder': '基础数据管理中查询并填入'} ) ,
                                      error_messages = {'required': '这个字段是必填项。'} )
    ct = forms.CharField( label = 'ct 值' , help_text = '未检出ct值，请直接输入0' , required = True ,
                          widget = forms.TextInput(
                              attrs = {'class': 'form-control' , 'placeholder': '未检出ct值，请直接输入0'} ) ,
                          error_messages = {'required': '这个字段是必填项。'} )

    class Meta:
        model = QpcrIndexes
        exclude = ('' ,)

    def clean_formula_number(self):
        if CTformula.objects.filter( number = self.cleaned_data ['formula_number'] ).count( ) == 0:
            raise forms.ValidationError( '公式唯一编号有错误请核实' )
        return self.cleaned_data ['formula_number']

    def clean_ct(self):
        if float( self.cleaned_data ['ct'] ) == 0:
            self.cleaned_data ['ct'] = 9  # TODO 当ct未检出时，提供一个默认值
        return self.cleaned_data ['ct']


class GenusListFilter( admin.SimpleListFilter ):
    title = "菌种"
    parameter_name = "genus"

    def lookups(self , request , model_admin):
        l = [i.english_name for i in Genus.objects.all( )]
        l.remove( "empty" )
        h = ["FAE" , "BT" , "FN" , "LAC-BIFI" , "CS-EF-AKK" , "CS" , "LAC" , "BIFI" , "EF" , "AKK"]
        value = list( product( l , l ) )
        label = []
        for i in value:
            label.append( "%s-%s" % (i [0] , i [1]) )
        label.remove("LAC-BIFI")
        return tuple( zip( h+label , h+label ) )

    def queryset(self , request , queryset):
        genus_english_name = self.value( )
        if genus_english_name:
            if re.match( ".*-.*" , genus_english_name ):
                if re.split( "-" , genus_english_name ).__len__( ) == 3:
                    '''适用于（FN,AKK,BIFI）'''
                    return queryset.filter(
                        genus__english_name = re.split( "-" , genus_english_name ) [0] ) | queryset.filter(
                        genus__english_name = re.split( "-" , genus_english_name ) [1] ) | queryset.filter(
                        genus__english_name = re.split( "-" , genus_english_name ) [2] )
                else:
                    '''适用于（FN,AKK）'''
                    return queryset.filter(
                        genus__english_name = re.split( "-" , genus_english_name ) [0] ) | queryset.filter(
                        genus__english_name = re.split( "-" , genus_english_name ) [1] )
            else:
                return queryset.filter( genus__english_name = genus_english_name )
        return queryset


@admin.register( QpcrIndexes )
class QpcrIndexesAdmin( ImportExportActionModelAdmin , admin.ModelAdmin ):
    list_display = (
        'id' , 'sample_number' , 'internal_number' , 'carbon_source' , 'genus' , 'ct' , 'concentration' ,
        'concentration_reference_range' ,
        'concentration_status_colored' , 'formula_number' , 'is_status')
    list_display_links = ('sample_number' ,)
    ordering = ('-id' ,)
    view_on_site = False
    list_max_show_all = 100
    list_per_page = 38
    list_filter = ('is_status' , 'carbon_source' , GenusListFilter)
    search_fields = ('internal_number' ,)

    def get_search_results(self , request , queryset , search_term):
        if not (search_term.strip( ) == ""):
            search_term_split = re.split( ' +' , search_term.strip( ) )
            qlist = []
            for search_term in search_term_split:
                for field in self.search_fields:
                    qlist.append( Q( **{'{}__iregex'.format( field ): search_term} ) )
            return queryset.filter( reduce( lambda x , y: x | y , qlist ) ) , True  # 按照内部编号进行查询，顺序按照搜索顺序
        else:
            return super( ).get_search_results( request , queryset , search_term )

    resource_class = QpcrIndexesResource
    form = QpcrIndexesForm
    # list_editable =
    actions = ['make_finish' , 'export_admin_action' , 'make_risk']
    fields = (
        'sample_number' , 'carbon_source' , 'genus' , 'ct' , 'concentration' , 'concentration_reference_range' ,
        'concentration_status' ,
        'formula_number' , 'is_status')

    def concentration_status_colored(self , obj):
        if obj.concentration_status == 0:
            return format_html( '<b style="background:{};">{}</b>' , 'red' , obj.get_concentration_status_display( ) )
        elif obj.concentration_status == 2:
            return format_html( '<b style="background:{};">{}</b>' , 'blue' , obj.get_concentration_status_display( ) )
        else:
            return obj.get_concentration_status_display( )

    concentration_status_colored.short_description = "浓度状态"

    def get_readonly_fields(self , request , obj=None):
        # 根据 obj 是否为空来判断,修改数据时不能修改样本编号，
        if obj:
            self.readonly_fields = (
                'sample_number' , 'concentration' , 'concentration_reference_range' , 'concentration_status' ,
                'genus_zh' , 'carbon_source_zh')
        else:
            self.readonly_fields = (
                'concentration' , 'concentration_reference_range' , 'concentration_status' , 'genus_zh' ,
                'carbon_source_zh')
        # if request.user.is_superuser: TODO 上线后取消注释
        #     self.readonly_fields = ()
        return self.readonly_fields

    def get_export_formats(self):
        """
        Returns available export formats.
        """
        formats = (
            base_formats.CSV ,
            base_formats.XLS ,
            base_formats.XLSX ,
            base_formats.TSV ,
        )
        return [f for f in formats if f( ).can_export( )]

    def get_import_formats(self):
        """
        Returns available export formats.
        """
        formats = (
            base_formats.CSV ,
            base_formats.XLS ,
            base_formats.XLSX ,
            base_formats.TSV ,
        )
        return [f for f in formats if f( ).can_import( )]

    def make_finish(self , request , queryset):
        i = 0  # 提交成功的数据
        n = 0  # 提交过的数量
        t = 0  # 选中状态
        for obj in queryset:
            t += 1
            if obj.is_status < 1:
                '''初始化偏高，偏低的异常状态'''
                qpcr_unusual , qpcr_unusual_created = IndexesUnusual.objects.get_or_create(
                    sample_number = obj.sample_number , check_type = "qPCR检测" )
                if qpcr_unusual_created:
                    unusual_high = ""  # 偏高结果
                    unusual_low = ""  # 偏低结果
                else:
                    unusual_high = qpcr_unusual.high
                    unusual_low = qpcr_unusual.low
                obj_progress , created = Progress.objects.get_or_create( sample_number = obj.sample_number )
                if obj_progress.is_qpcr:
                    obj.is_status = 1  # 1是标记为完成的
                    obj.save( )
                    ''' 整理异常检测结果 '''
                    concentration_status = obj.concentration_status
                    if concentration_status != 1:
                        if concentration_status == 0:
                            if obj.carbon_source.name == "粪便":
                                unusual_high = "%s,%s;" % (  # qpcr展示形式：双歧杆菌；普拉梭菌
                                    unusual_high , obj.genus.china_name)
                                create_risk( obj , "concentration" , QpcrIndexes , "偏高" , True )
                            else:
                                unusual_high = "%s,%s,%s;" % (  # qpcr展示形式：果糖,双歧杆菌；木糖醇,普拉梭菌
                                    unusual_high , obj.carbon_source.name , obj.genus.china_name)
                        else:
                            if obj.carbon_source.name == "粪便":
                                unusual_low = "%s,%s;" % (  # qpcr展示形式：双歧杆菌;普拉梭菌
                                    unusual_low , obj.genus.china_name)
                                create_risk( obj , "concentration" , QpcrIndexes , "偏低" , True )
                            else:
                                unusual_low = "%s,%s,%s;" % (  # qpcr展示形式：果糖,双歧杆菌；木糖醇,普拉梭菌
                                    unusual_low , obj.carbon_source.name , obj.genus.china_name)
                    ''' 把异常检测结果存到数据库中 '''
                    qpcr_unusual.high = unusual_high
                    qpcr_unusual.low = unusual_low
                    qpcr_unusual.save( )
                    i += 1
                else:
                    n += 1
            else:
                n += 1
        self.message_user( request , '选择%s条信息，完成操作%s条，不操作%s条' % (t , i , n) , level = messages.SUCCESS )

    make_finish.short_description = '1标记完成'

    def make_risk(self , request , queryset):
        '''代谢水平判读'''
        risk_items = RiskItem.objects.filter( risk_type_number = "FXDL0002" ,
                                              check_type_number = "JCDL0004" )  # 代谢水平判读; qpcr指标项
        meta_risk = get_meta_risk( risk_items )
        '''肠道免疫'''
        risk_items = RiskItem.objects.filter( risk_type_number = "FXDL0003" ,
                                              check_type_number = "JCDL0004" )  # 代谢水平判读; qpcr指标项
        gut_risk = get_meta_risk( risk_items )
        i = 0  # 提交成功的数据
        n = 0  # 提交过的数量
        t = 0  # 选中状态
        no_err = True
        for obj in queryset:
            t += 1
            if obj.is_status == 1:
                '''修改初始化偏高，偏低的异常状态的数值'''
                meta_risk_indexes = MetaRiskIndexes.objects.filter( sample_number = obj.sample_number ,
                                                                    index_name = obj.genus_zh )
                if meta_risk_indexes.count( ) > 0:
                    for meta_risk_index in meta_risk_indexes:
                        if meta_risk_index.index_name in meta_risk:
                            riskItemDefaults = RiskItemDefault.objects.filter( risk_name = "血脂" ,
                                                                               risk_type_number = "FXDL0002" ,
                                                                               index_name = meta_risk_index.index_name )
                            if riskItemDefaults.count( ) == 0:
                                self.message_user( request , '风险指标默认值没有，请先在基础数据中心添加' ,
                                                   level = messages.ERROR )
                                no_err = False
                                break
                            if meta_risk_index.is_status == "偏高":
                                meta_risk_index.blood_fat = RiskItemDefault.objects.get( risk_name = "血脂" ,
                                                                                         risk_type_number = "FXDL0002" ,
                                                                                         index_name = meta_risk_index.index_name ).high_value
                                meta_risk_index.fat = RiskItemDefault.objects.get( risk_name = "肥胖" ,
                                                                                   risk_type_number = "FXDL0002" ,
                                                                                   index_name = meta_risk_index.index_name ).high_value
                            elif meta_risk_index.is_status == "偏低":
                                meta_risk_index.blood_fat = RiskItemDefault.objects.get( risk_name = "血脂" ,
                                                                                         risk_type_number = "FXDL0002" ,
                                                                                         index_name = meta_risk_index.index_name ).low_value
                                meta_risk_index.fat = RiskItemDefault.objects.get( risk_name = "肥胖" ,
                                                                                   risk_type_number = "FXDL0002" ,
                                                                                   index_name = meta_risk_index.index_name ).low_value
                            meta_risk_index.save( )
                gut_risk_indexes = GutRiskIndexes.objects.filter( sample_number = obj.sample_number ,
                                                                  index_name = obj.genus_zh )
                if gut_risk_indexes.count( ) > 0:
                    for gut_risk_index in gut_risk_indexes:
                        if gut_risk_index.index_name in gut_risk:
                            riskItemDefaults = RiskItemDefault.objects.filter( risk_name = "肠道炎症" ,
                                                                               risk_type_number = "FXDL0003" ,
                                                                               index_name = meta_risk_index.index_name )
                            if riskItemDefaults.count( ) == 0:
                                self.message_user( request , '风险指标默认值没有，请先在基础数据中心添加' ,
                                                   level = messages.ERROR )
                                no_err = False
                                break
                            if gut_risk_index.is_status == "偏高":
                                gut_risk_index.infection = RiskItemDefault.objects.get( risk_name = "肠道炎症" ,
                                                                                        risk_type_number = "FXDL0003" ,
                                                                                        index_name = meta_risk_index.index_name ).high_value
                                gut_risk_index.scherm = RiskItemDefault.objects.get( risk_name = "肠道屏障" ,
                                                                                     risk_type_number = "FXDL0003" ,
                                                                                     index_name = meta_risk_index.index_name ).high_value
                                gut_risk_index.cancer = RiskItemDefault.objects.get( risk_name = "消化道肿瘤" ,
                                                                                     risk_type_number = "FXDL0003" ,
                                                                                     index_name = meta_risk_index.index_name ).high_value
                            elif gut_risk_index.is_status == "偏低":
                                gut_risk_index.infection = RiskItemDefault.objects.get( risk_name = "肠道炎症" ,
                                                                                        risk_type_number = "FXDL0003" ,
                                                                                        index_name = meta_risk_index.index_name ).low_value
                                gut_risk_index.scherm = RiskItemDefault.objects.get( risk_name = "肠道屏障" ,
                                                                                     risk_type_number = "FXDL0003" ,
                                                                                     index_name = meta_risk_index.index_name ).low_value
                                gut_risk_index.cancer = RiskItemDefault.objects.get( risk_name = "消化道肿瘤" ,
                                                                                     risk_type_number = "FXDL0003" ,
                                                                                     index_name = meta_risk_index.index_name ).low_value
                            gut_risk_index.save( )
                i += 1  # 提交成功数量
                if no_err:
                    obj_progress , created = Progress.objects.get_or_create( sample_number = obj.sample_number )
                    if obj_progress.is_qpcr:
                        obj_progress.qPCR_testing_date = datetime.date.today( )
                        obj_progress.qPCR_testing_staff = request.user.last_name + ' ' + request.user.first_name
                        obj_progress.save( )
                        obj.is_status = 2  # 2是标记为完成并判读的
                        obj.save( )
                else:
                    n += 1
            else:
                n += 1
        self.message_user( request , '选择%s条信息，完成操作%s条，不操作%s条' % (t , i , n) , level = messages.SUCCESS )

    make_risk.short_description = '2标记风险'

    def get_changeform_initial_data(self , request):
        initial = super( ).get_changeform_initial_data( request )
        initial ['formula_number'] = CTformula.objects.filter( formula_group__id = 2 ).order_by( '-create_date' ) [
            0].number  # id 为2的一定为“CT浓度换算” 类别
        return initial

    def save_model(self , request , obj , form , change):
        formula_content = CTformula.objects.filter( number = obj.formula_number ) [0].formula_content
        formula = Solver( formula_content , precision = 32 )
        point = {'x': obj.ct}
        '''ct值为0时，不适合ct计算公式'''
        if float( obj.ct ) == 0:
            obj.concentration = 0
        else:
            obj.concentration = float( formula( point ) )
        if ReferenceRange.objects.filter( index_name = QpcrIndexes._meta.get_field(
                'concentration' ).verbose_name , carbon_source = obj.carbon_source ,
                                          tax_name = obj.genus.english_name ).count( ) != 0:  # 根据字段的名称查询参考访问
            status , reference_range = get_status( QpcrIndexes , obj.carbon_source ,
                                                   obj.genus.english_name , 'concentration' ,
                                                   obj.concentration )
            obj.concentration_reference_range = reference_range
            obj.concentration_status = status
        else:
            self.message_user( request , '检测指标没有参考范围的基础数据，请先添加基础数据中心' , level = messages.ERROR )
        obj.save( )


class ScfasIndexesResource( resources.ModelResource ):
    class Meta:
        model = ScfasIndexes
        skip_unchanged = True
        fields = (
            'id' , 'sample_number' , 'internal_number' , 'carbon_source' , 'genus' , 'carbon_source_zh' , 'genus_zh' ,
            'total_acid' , 'acetic_acid' , 'propionic' , 'butyric' , 'isobutyric_acid' , 'valeric' ,
            'isovaleric' ,
            'acid_first' , 'acid_second' , 'acetic_acid_ratio' , 'propionic_ratio' , 'butyric_ratio' ,
            'isobutyric_acid_ratio' , 'valeric_ratio' ,
            'isovaleric_ratio')
        export_order = (
            'id' , 'sample_number' , 'internal_number' , 'carbon_source' , 'genus' , 'carbon_source_zh' , 'genus_zh' ,
            'total_acid' , 'acetic_acid' , 'propionic' , 'butyric' , 'isobutyric_acid' , 'valeric' ,
            'isovaleric' ,
            'acid_first' , 'acid_second' , 'acetic_acid_ratio' , 'propionic_ratio' , 'butyric_ratio' ,
            'isobutyric_acid_ratio' , 'valeric_ratio' ,
            'isovaleric_ratio')

    def get_diff_headers(self):
        return ['id' , '样本编号' , '对内编号' , '碳源' , '菌种' , '碳源中文名称' , '菌种中文名称' , '总酸' , '乙酸' , '丙酸' , '丁酸' ,
                '异丁酸' , '戊酸' , '异戊酸' , '乙丙丁酸占总酸比' , '异丁戊异戊占总酸比' , '乙酸占比' , '丙酸占比' , '丁酸占比' ,
                '异丁酸占比' , '戊酸占比' , '异戊酸占比']

    def get_export_headers(self):
        return ['id' , '样本编号' , '对内编号' , '碳源' , '菌种' , '碳源中文名称' , '菌种中文名称' , '总酸' , '乙酸' , '丙酸' , '丁酸' ,
                '异丁酸' , '戊酸' , '异戊酸' , '乙丙丁酸占总酸比' , '异丁戊异戊占总酸比' , '乙酸占比' , '丙酸占比' , '丁酸占比' ,
                '异丁酸占比' , '戊酸占比' , '异戊酸占比']

    def before_import_row(self , row , **kwargs):
        """
        Calls :meth:`import_export.fields.Field.save` if ``Field.attribute``
        and ``Field.column_name`` are found in ``data``.
        """
        sampless = Sample.objects.filter( sample_number = row ['样本编号'] )
        carbons = Carbon.objects.filter( id = row ['碳源'] )
        genuss = Genus.objects.filter( id = row ['菌种'] )
        if sampless.count( ) == 0:
            raise forms.ValidationError( '样本编号有误，请到样本接收数据中核实。' )
        if carbons.count( ) == 0:
            raise forms.ValidationError( '碳源名称有误，请到基础数据中核实。' )
        if genuss.count( ) == 0:
            raise forms.ValidationError( '菌种名称有误，请到基础数据中核实。' )
        total_acid_referenceRanges = ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
            'total_acid' ).verbose_name , carbon_source = carbons [0] , tax_name = genuss [0].english_name )
        acetic_acid_referenceRanges = ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
            'acetic_acid' ).verbose_name , carbon_source = carbons [0] , tax_name = genuss [0].english_name )
        propionic_referenceRanges = ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
            'propionic' ).verbose_name , carbon_source = carbons [0] , tax_name = genuss [0].english_name )
        butyric_referenceRanges = ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
            'butyric' ).verbose_name , carbon_source = carbons [0] , tax_name = genuss [0].english_name )
        isobutyric_acid_referenceRanges = ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
            'isobutyric_acid' ).verbose_name , carbon_source = carbons [0] , tax_name = genuss [0].english_name )
        valeric_referenceRanges = ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
            'valeric' ).verbose_name , carbon_source = carbons [0] , tax_name = genuss [0].english_name )
        isovaleric_reference_ranges = ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
            'isovaleric' ).verbose_name , carbon_source = carbons [0] , tax_name = genuss [0].english_name )
        isovaleric1_reference_ranges = ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
            'isovaleric1' ).verbose_name , carbon_source = carbons [0] , tax_name = genuss [0].english_name )
        isovaleric2_reference_ranges = ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
            'isovaleric2' ).verbose_name , carbon_source = carbons [0] , tax_name = genuss [0].english_name )
        isovaleric3_reference_ranges = ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
            'isovaleric3' ).verbose_name , carbon_source = carbons [0] , tax_name = genuss [0].english_name )
        acid_first_reference_ranges = ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
            'acid_first' ).verbose_name , carbon_source = carbons [0] , tax_name = genuss [0].english_name )
        acid_second_reference_ranges = ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
            'acid_second' ).verbose_name , carbon_source = carbons [0] , tax_name = genuss [0].english_name )
        acetic_acid_ratio_referenceRanges = ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
            'acetic_acid_ratio' ).verbose_name , carbon_source = carbons [0] , tax_name = genuss [0].english_name )
        propionic_ratio_referenceRanges = ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
            'propionic_ratio' ).verbose_name , carbon_source = carbons [0] , tax_name = genuss [0].english_name )
        butyric_ratio_referenceRanges = ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
            'butyric_ratio' ).verbose_name , carbon_source = carbons [0] , tax_name = genuss [0].english_name )
        isobutyric_acid_ratio_referenceRanges = ReferenceRange.objects.filter(
            index_name = ScfasIndexes._meta.get_field(
                'isobutyric_acid_ratio' ).verbose_name , carbon_source = carbons [0] ,
            tax_name = genuss [0].english_name )
        valeric_ratio_referenceRanges = ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
            'valeric_ratio' ).verbose_name , carbon_source = carbons [0] , tax_name = genuss [0].english_name )
        isovaleric_ratio_reference_ranges = ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
            'isovaleric_ratio' ).verbose_name , carbon_source = carbons [0] , tax_name = genuss [0].english_name )

        if total_acid_referenceRanges.count( ) == 0:
            raise forms.ValidationError( '%s 总酸参考范围有误，请到基础数据中核实。' % genuss [0].english_name )
        if acetic_acid_referenceRanges.count( ) == 0:
            raise forms.ValidationError( '%s 乙酸参考范围有误，请到基础数据中核实。' % genuss [0].english_name )
        if propionic_referenceRanges.count( ) == 0:
            raise forms.ValidationError( '%s 丙酸参考范围有误，请到基础数据中核实' % genuss [0].english_name )
        if butyric_referenceRanges.count( ) == 0:
            raise forms.ValidationError( '%s 丁酸参考范围有误，请到基础数据中核实' % (genuss [0].english_name) )
        if isobutyric_acid_referenceRanges.count( ) == 0:
            raise forms.ValidationError( '%s 异丁酸参考范围有误，请到基础数据中核实' % (genuss [0].english_name) )
        if valeric_referenceRanges.count( ) == 0:
            raise forms.ValidationError( '%s 戊酸参考范围有误，请到基础数据中核实' % (genuss [0].english_name) )
        if isovaleric_reference_ranges.count( ) == 0:
            raise forms.ValidationError( '%s 异戊酸参考参考范围有误，请到基础数据中核实' % genuss [0].english_name )
        if isovaleric1_reference_ranges.count( ) == 0:
            raise forms.ValidationError( '%s 扩展酸1参考范围有误，请到基础数据中核实' % genuss [0].english_name )
        if isovaleric2_reference_ranges.count( ) == 0:
            raise forms.ValidationError( '%s 扩展酸2参考范围有误，请到基础数据中核实' % genuss [0].english_name )
        if isovaleric3_reference_ranges.count( ) == 0:
            raise forms.ValidationError( '%s 扩展酸3参考范围有误，请到基础数据中核实' % genuss [0].english_name )
        if acid_first_reference_ranges.count( ) == 0:
            raise forms.ValidationError( '%s 乙丙丁酸占总酸比参考范围有误，请到基础数据中核实' % genuss [0].english_name )
        if acid_second_reference_ranges.count( ) == 0:
            raise forms.ValidationError( '%s 异丁戊异戊占总酸比参考范围有误，请到基础数据中核实' % genuss [0].english_name )
        if acetic_acid_ratio_referenceRanges.count( ) == 0:
            raise forms.ValidationError( '%s 乙酸占比参考范围有误，请到基础数据中核实。' % genuss [0].english_name )
        if propionic_ratio_referenceRanges.count( ) == 0:
            raise forms.ValidationError( '%s 丙酸占比参考范围有误，请到基础数据中核实' % genuss [0].english_name )
        if butyric_ratio_referenceRanges.count( ) == 0:
            raise forms.ValidationError( '%s 丁酸占比参考范围有误，请到基础数据中核实' % (genuss [0].english_name) )
        if isobutyric_acid_ratio_referenceRanges.count( ) == 0:
            raise forms.ValidationError( '%s 异丁酸占比参考范围有误，请到基础数据中核实' % (genuss [0].english_name) )
        if valeric_ratio_referenceRanges.count( ) == 0:
            raise forms.ValidationError( '%s 戊酸占比参考范围有误，请到基础数据中核实' % (genuss [0].english_name) )
        if isovaleric_ratio_reference_ranges.count( ) == 0:
            raise forms.ValidationError( '%s 异戊酸占比参考参考范围有误，请到基础数据中核实' % genuss [0].english_name )

    def get_or_init_instance(self , instance_loader , row):
        """
        Either fetches an already existing instance or initializes a new one.
        """
        instance = self.get_instance( instance_loader , row )
        row ['sample_number'] = row ['样本编号']
        row ['internal_number'] = row ['对内编号']
        row ['carbon_source'] = row ['碳源']
        row ['genus'] = row ['菌种']
        row ['carbon_source_zh'] = row ['碳源中文名称']
        row ['genus_zh'] = row ['菌种中文名称']
        row ['total_acid'] = row ['总酸']
        row ['acetic_acid'] = row ['乙酸']
        row ['propionic'] = row ['丙酸']
        row ['butyric'] = row ['丁酸']
        row ['isobutyric_acid'] = row ['异丁酸']
        row ['valeric'] = row ['戊酸']
        row ['isovaleric'] = row ['异戊酸']
        row ['acid_first'] = row ['乙丙丁酸占总酸比']
        row ['acid_second'] = row ['异丁戊异戊占总酸比']
        row ['acetic_acid_ratio'] = row ['乙酸占比']
        row ['propionic_ratio'] = row ['丙酸占比']
        row ['butyric_ratio'] = row ['丁酸占比']
        row ['isobutyric_acid_ratio'] = row ['异丁酸占比']
        row ['valeric_ratio'] = row ['戊酸占比']
        row ['isovaleric_ratio'] = row ['异戊酸占比']
        if instance:
            return instance , False
        else:
            return self.init_instance( row ) , True

    def before_save_instance(self , instance , using_transactions , dry_run):
        """
            Override to add additional logic. Does nothing by default.
        """
        if (instance.acetic_acid is not None) and (instance.propionic is not None) and (
                instance.butyric is not None) and (
                instance.isobutyric_acid is not None) and (instance.valeric is not None) and (
                instance.isovaleric is not None):
            instance.total_acid = instance.acetic_acid + instance.propionic + instance.butyric + instance.isobutyric_acid + instance.valeric + \
                                  instance.isovaleric

        if (instance.acetic_acid is not None) and (instance.propionic is not None) and (instance.butyric is not None):
            instance.acid_first = (instance.acetic_acid + instance.propionic + instance.butyric) / instance.total_acid

        if (instance.isobutyric_acid is not None) and (instance.valeric is not None) and (
                instance.isovaleric is not None):
            instance.acid_second = (
                                           instance.isobutyric_acid + instance.valeric + instance.isovaleric) / instance.total_acid

        if instance.acetic_acid is not None:
            instance.acetic_acid_ratio = instance.acetic_acid / instance.total_acid

        if instance.propionic is not None:
            instance.propionic_ratio = instance.propionic / instance.total_acid

        if instance.butyric is not None:
            instance.butyric_ratio = instance.butyric / instance.total_acid

        if instance.isobutyric_acid is not None:
            instance.isobutyric_acid_ratio = instance.isobutyric_acid / instance.total_acid

        if instance.valeric is not None:
            instance.valeric_ratio = instance.valeric / instance.total_acid

        if instance.isovaleric is not None:
            instance.isovaleric_ratio = instance.isovaleric / instance.total_acid

        if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                'total_acid' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
            status , reference_range = get_status( ScfasIndexes , instance.carbon_source ,
                                                   instance.genus.english_name , 'total_acid' ,
                                                   instance.total_acid )
            instance.total_acid_reference_range = reference_range
            instance.total_acid_status = status
        if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                'acetic_acid' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
            status , reference_range = get_status( ScfasIndexes , instance.carbon_source ,
                                                   instance.genus.english_name , 'acetic_acid' ,
                                                   instance.acetic_acid )
            instance.acetic_acid_reference_range = reference_range
            instance.acetic_acid_status = status
        if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                'propionic' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
            status , reference_range = get_status( ScfasIndexes , instance.carbon_source ,
                                                   instance.genus.english_name , 'propionic' ,
                                                   instance.propionic )
            instance.propionic_reference_range = reference_range
            instance.propionic_status = status
        if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                'butyric' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
            status , reference_range = get_status( ScfasIndexes , instance.carbon_source ,
                                                   instance.genus.english_name , 'butyric' , instance.butyric )
            instance.butyric_reference_range = reference_range
            instance.butyric_status = status
        if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                'isobutyric_acid' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
            status , reference_range = get_status( ScfasIndexes , instance.carbon_source ,
                                                   instance.genus.english_name , 'isobutyric_acid' ,
                                                   instance.isobutyric_acid )
            instance.isobutyric_acid_reference_range = reference_range
            instance.isobutyric_acid_status = status
        if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                'valeric' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
            status , reference_range = get_status( ScfasIndexes , instance.carbon_source ,
                                                   instance.genus.english_name , 'valeric' , instance.valeric )
            instance.valeric_reference_range = reference_range
            instance.valeric_status = status
        if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                'isovaleric' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
            status , reference_range = get_status( ScfasIndexes , instance.carbon_source ,
                                                   instance.genus.english_name , 'isovaleric' ,
                                                   instance.isovaleric )
            instance.isovaleric_reference_range = reference_range
            instance.isovaleric_status = status
        if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                'acid_first' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
            status , reference_range = get_status( ScfasIndexes , instance.carbon_source ,
                                                   instance.genus.english_name , 'acid_first' ,
                                                   instance.acid_first )
            instance.acid_first_reference_range = reference_range
            instance.acid_first_status = status
        if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                'acid_second' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
            status , reference_range = get_status( ScfasIndexes , instance.carbon_source ,
                                                   instance.genus.english_name , 'acid_second' ,
                                                   instance.acid_second )
            instance.acid_second_reference_range = reference_range
            instance.acid_second_status = status
        if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                'acetic_acid_ratio' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
            status , reference_range = get_status( ScfasIndexes , instance.carbon_source ,
                                                   instance.genus.english_name , 'acetic_acid_ratio' ,
                                                   instance.acetic_acid_ratio )
            instance.acetic_acid_ratio_reference_range = reference_range
            instance.acetic_acid_ratio_status = status

        if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                'propionic_ratio' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
            status , reference_range = get_status( ScfasIndexes , instance.carbon_source ,
                                                   instance.genus.english_name , 'propionic_ratio' ,
                                                   instance.propionic_ratio )
            instance.propionic_ratio_reference_range = reference_range
            instance.propionic_ratio_status = status

        if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                'butyric_ratio' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
            status , reference_range = get_status( ScfasIndexes , instance.carbon_source ,
                                                   instance.genus.english_name , 'butyric_ratio' ,
                                                   instance.butyric_ratio )
            instance.butyric_ratio_reference_range = reference_range
            instance.butyric_ratio_status = status

        if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                'isobutyric_acid_ratio' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
            status , reference_range = get_status( ScfasIndexes , instance.carbon_source ,
                                                   instance.genus.english_name , 'isobutyric_acid_ratio' ,
                                                   instance.isobutyric_acid_ratio )
            instance.isobutyric_acid_ratio_reference_range = reference_range
            instance.isobutyric_acid_ratio_status = status

        if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                'valeric_ratio' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
            status , reference_range = get_status( ScfasIndexes , instance.carbon_source ,
                                                   instance.genus.english_name , 'valeric_ratio' ,
                                                   instance.valeric_ratio )
            instance.valeric_ratio_reference_range = reference_range
            instance.valeric_ratio_status = status

        if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                'isovaleric_ratio' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
            status , reference_range = get_status( ScfasIndexes , instance.carbon_source ,
                                                   instance.genus.english_name , 'isovaleric_ratio' ,
                                                   instance.isovaleric_ratio )
            instance.isovaleric_ratio_reference_range = reference_range
            instance.isovaleric_ratio_status = status


@admin.register( ScfasIndexes )
class ScfasIndexesAdmin( ImportExportActionModelAdmin , admin.ModelAdmin ):
    list_display = ('id' , 'sample_number' , 'internal_number' , 'carbon_source' , 'genus' ,
                    'total_acid_status_colored' , 'acetic_acid_status_colored' , 'propionic_status_colored' ,
                    'butyric_status_colored' ,
                    'isobutyric_acid_status_colored' , 'valeric_status_colored' ,
                    'isovaleric_status_colored' ,
                    'acid_first_status_colored' , 'acid_second_status_colored' , 'is_status')
    list_display_links = ('sample_number' ,)
    ordering = ('-id' ,)
    view_on_site = False
    list_max_show_all = 100
    list_per_page = 20
    list_filter = ('is_status' , 'carbon_source')
    search_fields = ('sample_number' ,)
    import_export_args = {'import_resource_class': ScfasIndexesResource , 'export_resource_class': ScfasIndexesResource}
    resource_class = ScfasIndexesResource
    # form =
    # list_editable =
    actions = ['make_finish' , 'export_admin_action' , 'make_risk']
    exclude = (
        'isovaleric1' , 'isovaleric1_status' , 'isovaleric1_reference_range' , 'isovaleric2' , 'isovaleric2_status' ,
        'isovaleric2_reference_range' , 'isovaleric3' , 'isovaleric3_status' , 'isovaleric3_reference_range' ,
        'carbon_source_zh' , 'genus_zh')

    def total_acid_status_colored(self , obj):
        if obj.total_acid_status == 0:
            return format_html( '<b style="background:{};">{}</b>' , 'red' , obj.get_total_acid_status_display( ) )
        elif obj.total_acid_status == 2:
            return format_html( '<b style="background:{};">{}</b>' , 'blue' , obj.get_total_acid_status_display( ) )
        else:
            return obj.get_total_acid_status_display( )

    total_acid_status_colored.short_description = "总酸状态"

    def acetic_acid_status_colored(self , obj):
        if obj.acetic_acid_status == 0:
            return format_html( '<b style="background:{};">{}</b>' , 'red' , obj.get_acetic_acid_status_display( ) )
        elif obj.acetic_acid_status == 2:
            return format_html( '<b style="background:{};">{}</b>' , 'blue' , obj.get_acetic_acid_status_display( ) )
        else:
            return obj.get_acetic_acid_status_display( )

    acetic_acid_status_colored.short_description = "乙酸状态"

    def propionic_status_colored(self , obj):
        if obj.propionic_status == 0:
            return format_html( '<b style="background:{};">{}</b>' , 'red' , obj.get_propionic_status_display( ) )
        elif obj.propionic_status == 2:
            return format_html( '<b style="background:{};">{}</b>' , 'blue' , obj.get_propionic_status_display( ) )
        else:
            return obj.get_propionic_status_display( )

    propionic_status_colored.short_description = "丙酸状态"

    def butyric_status_colored(self , obj):
        if obj.butyric_status == 0:
            return format_html( '<b style="background:{};">{}</b>' , 'red' , obj.get_butyric_status_display( ) )
        elif obj.butyric_status == 2:
            return format_html( '<b style="background:{};">{}</b>' , 'blue' , obj.get_butyric_status_display( ) )
        else:
            return obj.get_butyric_status_display( )

    butyric_status_colored.short_description = "丁酸状态"

    def isobutyric_acid_status_colored(self , obj):
        if obj.isobutyric_acid_status == 0:
            return format_html( '<b style="background:{};">{}</b>' , 'red' , obj.get_isobutyric_acid_status_display( ) )
        elif obj.isobutyric_acid_status == 2:
            return format_html( '<b style="background:{};">{}</b>' , 'blue' ,
                                obj.get_isobutyric_acid_status_display( ) )
        else:
            return obj.get_isobutyric_acid_status_display( )

    isobutyric_acid_status_colored.short_description = "异丁酸状态"

    def valeric_status_colored(self , obj):
        if obj.valeric_status == 0:
            return format_html( '<b style="background:{};">{}</b>' , 'red' , obj.get_valeric_status_display( ) )
        elif obj.valeric_status == 2:
            return format_html( '<b style="background:{};">{}</b>' , 'blue' , obj.get_valeric_status_display( ) )
        else:
            return obj.get_valeric_status_display( )

    valeric_status_colored.short_description = "戊酸状态"

    def isovaleric_status_colored(self , obj):
        if obj.isovaleric_status == 0:
            return format_html( '<b style="background:{};">{}</b>' , 'red' , obj.get_isovaleric_status_display( ) )
        elif obj.isovaleric_status == 2:
            return format_html( '<b style="background:{};">{}</b>' , 'blue' , obj.get_isovaleric_status_display( ) )
        else:
            return obj.get_isovaleric_status_display( )

    isovaleric_status_colored.short_description = "异戊酸状态"

    def acid_first_status_colored(self , obj):
        if obj.acid_first_status == 0:
            return format_html( '<b style="background:{};">{}</b>' , 'red' , obj.get_acid_first_status_display( ) )
        elif obj.acid_first_status == 2:
            return format_html( '<b style="background:{};">{}</b>' , 'blue' , obj.get_acid_first_status_display( ) )
        else:
            return obj.get_acid_first_status_display( )

    acid_first_status_colored.short_description = "乙丙丁酸占总酸比状态"

    def acid_second_status_colored(self , obj):
        if obj.acid_second_status == 0:
            return format_html( '<b style="background:{};">{}</b>' , 'red' , obj.get_acid_second_status_display( ) )
        elif obj.acid_second_status == 2:
            return format_html( '<b style="background:{};">{}</b>' , 'blue' , obj.get_acid_second_status_display( ) )
        else:
            return obj.get_acid_second_status_display( )

    acid_second_status_colored.short_description = "异丁戊异戊占总酸比"

    def get_readonly_fields(self , request , obj=None):
        # 根据 obj 是否为空来判断,修改数据时不能修改样本编号，
        if obj:
            self.readonly_fields = ('sample_number' , 'carbon_source' , 'genus')
        else:
            self.readonly_fields = ()
        if request.user.is_superuser:  # TODO 上线时打开
            self.readonly_fields = ()
        return self.readonly_fields

    def get_export_formats(self):
        """
        Returns available export formats.
        """
        formats = (
            base_formats.CSV ,
            base_formats.XLS ,
            base_formats.XLSX ,
            base_formats.TSV ,
        )
        return [f for f in formats if f( ).can_export( )]

    def get_import_formats(self):
        """
        Returns available export formats.
        """
        formats = (
            base_formats.CSV ,
            base_formats.XLS ,
            base_formats.XLSX ,
            base_formats.TSV ,
        )
        return [f for f in formats if f( ).can_import( )]

    def make_finish(self , request , queryset):
        i = 0  # 提交成功的数据
        n = 0  # 提交过的数量
        t = 0  # 选中状态
        for obj in queryset:
            t += 1
            if obj.is_status < 1:
                '''初始化偏高，偏低的异常状态'''
                scfas_unusual , scfas_unusual_created = IndexesUnusual.objects.get_or_create(
                    sample_number = obj.sample_number , check_type = "SCFAs指标" )
                if scfas_unusual_created:
                    unusual_high = ""  # 偏高结果
                    unusual_low = ""  # 偏低结果
                else:
                    unusual_high = scfas_unusual.high
                    unusual_low = scfas_unusual.low
                obj_progress , created = Progress.objects.get_or_create( sample_number = obj.sample_number )
                if obj_progress.is_scfa:
                    obj.is_status = 1  # 1是标记为完成的
                    obj.save( )
                    ''' 整理异常检测结果 '''
                    for key , status in {"acetic_acid": obj.acetic_acid_status ,
                                         "propionic": obj.propionic_status , "butyric": obj.butyric_status ,
                                         "isobutyric_acid": obj.isobutyric_acid_status ,
                                         "valeric": obj.valeric_status ,
                                         "isovaleric": obj.isovaleric_status}.items( ):
                        if status != 1:
                            if status == 0:
                                if obj.carbon_source.name == "粪便":  # 对风险判读做数据处理
                                    unusual_high = "%s,%s;" % (  # 异丁酸;乙酸
                                        unusual_high ,
                                        ScfasIndexes._meta.get_field( key ).verbose_name)
                                    create_risk( obj , key , ScfasIndexes , "偏高" , False )
                                else:
                                    unusual_high = "%s,%s,%s;" % (  # 木糖醇,异丁酸;果糖,乙酸
                                        unusual_high , obj.carbon_source.name ,
                                        ScfasIndexes._meta.get_field( key ).verbose_name)
                            else:
                                if obj.carbon_source.name == "粪便":
                                    unusual_low = "%s,%s;" % (  # 异丁酸;乙酸
                                        unusual_low ,
                                        ScfasIndexes._meta.get_field( key ).verbose_name)
                                    create_risk( obj , key , ScfasIndexes , "偏低" , False )
                                else:
                                    unusual_low = "%s,%s,%s;" % (  # 木糖醇,异丁酸;果糖,乙酸
                                        unusual_low , obj.carbon_source.name ,
                                        ScfasIndexes._meta.get_field( key ).verbose_name)
                    ''' 把异常检测结果存到数据库中 '''
                    scfas_unusual.high = unusual_high
                    scfas_unusual.low = unusual_low
                    scfas_unusual.save( )

                    i += 1
                else:
                    n += 1
            else:
                n += 1
        self.message_user( request , '选择%s条信息，完成操作%s条，不操作%s条' % (t , i , n) , level = messages.SUCCESS )

    make_finish.short_description = '1标记完成'

    def make_risk(self , request , queryset):
        '''代谢水平判读'''
        risk_items = RiskItem.objects.filter( risk_type_number = "FXDL0002" ,
                                              check_type_number = "JCDL0005" )  # 代谢水平判读; SCFAs指标项
        meta_risk = get_meta_risk( risk_items )
        i = 0  # 提交成功的数据
        n = 0  # 提交过的数量
        t = 0  # 选中状态
        no_err = True
        for obj in queryset:
            t += 1
            if obj.is_status == 1:
                '''修改初始化偏高，偏低的异常状态的数值'''
                meta_risk_indexes = MetaRiskIndexes.objects.filter( sample_number = obj.sample_number )
                if meta_risk_indexes.count( ) > 0:
                    for meta_risk_index in meta_risk_indexes:
                        if meta_risk_index.index_name in meta_risk:
                            riskItemDefaults = RiskItemDefault.objects.filter( risk_name = "血脂" ,
                                                                               risk_type_number = "FXDL0002" ,
                                                                               index_name = meta_risk_index.index_name )
                            if riskItemDefaults.count( ) == 0:
                                self.message_user( request , '风险指标默认值没有，请先在基础数据中心添加' ,
                                                   level = messages.ERROR )
                                no_err = False
                                break
                            if meta_risk_index.is_status == "偏高":
                                meta_risk_index.blood_fat = RiskItemDefault.objects.get( risk_name = "血脂" ,
                                                                                         risk_type_number = "FXDL0002" ,
                                                                                         index_name = meta_risk_index.index_name ).high_value
                                meta_risk_index.fat = RiskItemDefault.objects.get( risk_name = "肥胖" ,
                                                                                   risk_type_number = "FXDL0002" ,
                                                                                   index_name = meta_risk_index.index_name ).high_value
                            elif meta_risk_index.is_status == "偏低":
                                meta_risk_index.blood_fat = RiskItemDefault.objects.get( risk_name = "血脂" ,
                                                                                         risk_type_number = "FXDL0002" ,
                                                                                         index_name = meta_risk_index.index_name ).low_value
                                meta_risk_index.fat = RiskItemDefault.objects.get( risk_name = "肥胖" ,
                                                                                   risk_type_number = "FXDL0002" ,
                                                                                   index_name = meta_risk_index.index_name ).low_value
                            meta_risk_index.save( )
                i += 1
                if no_err:
                    obj_progress , created = Progress.objects.get_or_create( sample_number = obj.sample_number )
                    if obj_progress.is_scfa:
                        obj_progress.SCFAs_testing_date = datetime.date.today( )
                        obj_progress.SCFAs_testing_staff = request.user.last_name + ' ' + request.user.first_name
                        obj_progress.save( )
                        obj.is_status = 2  # 2是标记为完成并判读的
                        obj.save( )
                else:
                    n += 1
            else:
                n += 1
        self.message_user( request , '选择%s条信息，完成操作%s条，不操作%s条' % (t , i , n) , level = messages.SUCCESS )

    make_risk.short_description = '2标记风险'

    def save_model(self , request , obj , form , change):

        if obj.acetic_acid is not None:
            if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                    'acetic_acid' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问

                status , reference_range = get_status( ScfasIndexes , obj.carbon_source ,
                                                       obj.genus.english_name , 'acetic_acid' ,
                                                       obj.acetic_acid )
                obj.acetic_acid_reference_range = reference_range
                obj.acetic_acid_status = status
            else:
                self.message_user( request , '乙酸 检测指标没有参考范围的基础数据，请先添加基础数据中心' , level = messages.ERROR )
        if obj.propionic is not None:
            if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                    'propionic' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
                status , reference_range = get_status( ScfasIndexes , obj.carbon_source ,
                                                       obj.genus.english_name , 'propionic' , obj.propionic )
                obj.propionic_reference_range = reference_range
                obj.propionic_status = status
            else:
                self.message_user( request , '丙酸 检测指标没有参考范围的基础数据，请先添加基础数据中心' , level = messages.ERROR )
        if obj.butyric is not None:
            if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                    'butyric' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
                status , reference_range = get_status( ScfasIndexes , obj.carbon_source ,
                                                       obj.genus.english_name , 'butyric' , obj.butyric )
                obj.butyric_reference_range = reference_range
                obj.butyric_status = status
            else:
                self.message_user( request , '丁酸 检测指标没有参考范围的基础数据，请先添加基础数据中心' , level = messages.ERROR )
        if obj.isobutyric_acid is not None:
            if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                    'isobutyric_acid' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
                status , reference_range = get_status( ScfasIndexes , obj.carbon_source ,
                                                       obj.genus.english_name , 'isobutyric_acid' ,
                                                       obj.isobutyric_acid )
                obj.isobutyric_acid_reference_range = reference_range
                obj.isobutyric_acid_status = status
            else:
                self.message_user( request , '异丁酸 检测指标没有参考范围的基础数据，请先添加基础数据中心' , level = messages.ERROR )
        if obj.valeric is not None:
            if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                    'valeric' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
                status , reference_range = get_status( ScfasIndexes , obj.carbon_source ,
                                                       obj.genus.english_name , 'valeric' , obj.valeric )
                obj.valeric_reference_range = reference_range
                obj.valeric_status = status
            else:
                self.message_user( request , '戊酸 检测指标没有参考范围的基础数据，请先添加基础数据中心' , level = messages.ERROR )
        if obj.isovaleric is not None:
            if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                    'isovaleric' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
                status , reference_range = get_status( ScfasIndexes , obj.carbon_source ,
                                                       obj.genus.english_name , 'isovaleric' , obj.isovaleric )
                obj.isovaleric_reference_range = reference_range
                obj.isovaleric_status = status
            else:
                self.message_user( request , '异戊酸 检测指标没有参考范围的基础数据，请先添加基础数据中心' , level = messages.ERROR )

        if (obj.acetic_acid is not None) and (obj.propionic is not None) and (obj.butyric is not None) and (
                obj.isobutyric_acid is not None) and (obj.valeric is not None) and (obj.isovaleric is not None):
            obj.total_acid = obj.acetic_acid + obj.propionic + obj.butyric + obj.isobutyric_acid + obj.valeric + \
                             obj.isovaleric
            '''保存信息的时候，对糖代谢能力，便秘腹泻做判读'''
            if obj.carbon_source.name == "粪便":
                digestive_diarrhea = (1 + 2.97002415119877 / float(
                    obj.acetic_acid / obj.propionic ) + 4.60469584970147 / float(
                    obj.acetic_acid / obj.butyric )) / (39.8959183583737 / float(
                    obj.acetic_acid / obj.isobutyric_acid ) + 33.5702967741936 / float(
                    obj.acetic_acid / obj.valeric ) + 27.6137713653937 / float(
                    obj.acetic_acid / obj.isovaleric ))
                metaboilic = obj.butyric / obj.acetic_acid
                risk , stat = Risk.objects.get_or_create( sample_number = obj.sample_number ,
                                                          internal_number = obj.internal_number )
                risk.digestive_diarrhea = digestive_diarrhea
                risk.metaboilic = metaboilic
                risk.save( )
        if (obj.acetic_acid is not None) and (obj.propionic is not None) and (obj.butyric is not None):
            obj.acid_first = (obj.acetic_acid + obj.propionic + obj.butyric) / obj.total_acid

        if (obj.isobutyric_acid is not None) and (obj.valeric is not None) and (obj.isovaleric is not None):
            obj.acid_second = (obj.isobutyric_acid + obj.valeric + obj.isovaleric) / obj.total_acid

        if obj.acetic_acid is not None:
            obj.acetic_acid_ratio = obj.acetic_acid / obj.total_acid

        if obj.propionic is not None:
            obj.propionic_ratio = obj.propionic / obj.total_acid

        if obj.butyric is not None:
            obj.butyric_ratio = obj.butyric / obj.total_acid

        if obj.isobutyric_acid is not None:
            obj.isobutyric_acid_ratio = obj.isobutyric_acid / obj.total_acid

        if obj.valeric is not None:
            obj.valeric_ratio = obj.valeric / obj.total_acid

        if obj.isovaleric is not None:
            obj.isovaleric_ratio = obj.isovaleric / obj.total_acid

        if obj.acetic_acid_ratio is not None:
            if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                    'acetic_acid_ratio' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
                status , reference_range = get_status( ScfasIndexes , obj.carbon_source ,
                                                       obj.genus.english_name , 'acetic_acid_ratio' ,
                                                       obj.acetic_acid_ratio )
                obj.acetic_acid_ratio_reference_range = reference_range
                obj.acetic_acid_ratio_status = status

            else:
                self.message_user( request , '乙酸占比 检测指标没有参考范围的基础数据，请先添加基础数据中心' , level = messages.ERROR )

        if obj.propionic_ratio is not None:
            if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                    'propionic_ratio' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
                status , reference_range = get_status( ScfasIndexes , obj.carbon_source ,
                                                       obj.genus.english_name , 'propionic_ratio' ,
                                                       obj.propionic_ratio )
                obj.propionic_ratio_reference_range = reference_range
                obj.propionic_ratio_status = status

            else:
                self.message_user( request , '丙酸占比 检测指标没有参考范围的基础数据，请先添加基础数据中心' , level = messages.ERROR )
        if obj.butyric_ratio is not None:
            if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                    'butyric_ratio' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
                status , reference_range = get_status( ScfasIndexes , obj.carbon_source ,
                                                       obj.genus.english_name , 'butyric_ratio' , obj.butyric_ratio )
                obj.butyric_ratio_reference_range = reference_range
                obj.butyric_ratio_status = status

            else:
                self.message_user( request , '丁酸占比 检测指标没有参考范围的基础数据，请先添加基础数据中心' , level = messages.ERROR )

        if obj.isobutyric_acid_ratio is not None:
            if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                    'isobutyric_acid_ratio' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
                status , reference_range = get_status( ScfasIndexes , obj.carbon_source ,
                                                       obj.genus.english_name , 'isobutyric_acid_ratio' ,
                                                       obj.isobutyric_acid_ratio )
                obj.isobutyric_acid_ratio_reference_range = reference_range
                obj.isobutyric_acid_ratio_status = status

            else:
                self.message_user( request , '异丁酸占比 检测指标没有参考范围的基础数据，请先添加基础数据中心' , level = messages.ERROR )

        if obj.valeric_ratio is not None:
            if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                    'valeric_ratio' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
                status , reference_range = get_status( ScfasIndexes , obj.carbon_source ,
                                                       obj.genus.english_name , 'valeric_ratio' ,
                                                       obj.valeric_ratio )
                obj.valeric_ratio_reference_range = reference_range
                obj.valeric_ratio_status = status

            else:
                self.message_user( request , '戊酸占比 检测指标没有参考范围的基础数据，请先添加基础数据中心' , level = messages.ERROR )

        if obj.isovaleric_ratio is not None:
            if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                    'isovaleric_ratio' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
                status , reference_range = get_status( ScfasIndexes , obj.carbon_source ,
                                                       obj.genus.english_name , 'isovaleric_ratio' ,
                                                       obj.isovaleric_ratio )
                obj.isovaleric_ratio_reference_range = reference_range
                obj.isovaleric_ratio_status = status

            else:
                self.message_user( request , '异戊酸占比 检测指标没有参考范围的基础数据，请先添加基础数据中心' , level = messages.ERROR )

        if obj.acid_first is not None:
            if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                    'acid_first' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
                status , reference_range = get_status( ScfasIndexes , obj.carbon_source ,
                                                       obj.genus.english_name , 'acid_first' , obj.acid_first )
                obj.acid_first_reference_range = reference_range
                obj.acid_first_status = status

            else:
                self.message_user( request , '乙丙丁酸占总酸比 检测指标没有参考范围的基础数据，请先添加基础数据中心' , level = messages.ERROR )

        if obj.acid_second is not None:
            if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                    'acid_second' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
                status , reference_range = get_status( ScfasIndexes , obj.carbon_source ,
                                                       obj.genus.english_name , 'acid_second' ,
                                                       obj.acid_second )
                obj.acid_second_reference_range = reference_range
                obj.acid_second_status = status
            else:
                self.message_user( request , '异丁戊异戊占总酸比 检测指标没有参考范围的基础数据，请先添加基础数据中心' , level = messages.ERROR )

        if obj.total_acid is not None:
            if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                    'total_acid' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
                status , reference_range = get_status( ScfasIndexes , obj.carbon_source ,
                                                       obj.genus.english_name , 'total_acid' , obj.total_acid )
                obj.total_acid_reference_range = reference_range
                obj.total_acid_status = status
            else:
                self.message_user( request , '总酸 检测指标没有参考范围的基础数据，请先添加基础数据中心' , level = messages.ERROR )
        obj.save( )


class DegradationIndexesResource( resources.ModelResource ):
    class Meta:
        model = DegradationIndexes
        skip_unchanged = True
        fields = (
            'id' , 'sample_number' , 'internal_number' , 'carbon_source' , 'genus' , 'carbon_source_zh' , 'genus_zh' ,
            'degradation' ,
            'gas')
        export_order = (
            'id' , 'sample_number' , 'internal_number' , 'carbon_source' , 'genus' , 'carbon_source_zh' , 'genus_zh' ,
            'degradation' ,
            'gas')

    def get_export_headers(self):
        return ['id' , '样本编号' , '对内编号' , '碳源' , '菌种' , '碳源中文名称' , '菌种中文名称' , '降解率' , '产气']

    def get_diff_headers(self):
        return ['id' , '样本编号' , '对内编号' , '碳源' , '菌种' , '碳源中文名称' , '菌种中文名称' , '降解率' , '产气']

    def before_import_row(self , row , **kwargs):
        """
        Calls :meth:`import_export.fields.Field.save` if ``Field.attribute``
        and ``Field.column_name`` are found in ``data``.
        """
        sampless = Sample.objects.filter( sample_number = row ['样本编号'] )
        carbons = Carbon.objects.filter( id = row ['碳源'] )
        genuss = Genus.objects.filter( id = row ['菌种'] )
        if sampless.count( ) == 0:
            raise forms.ValidationError( '样本编号有误，请到样本接收数据中核实。' )
        if carbons.count( ) == 0:
            raise forms.ValidationError( '碳源名称有误，请到基础数据中核实。' )
        if genuss.count( ) == 0:
            raise forms.ValidationError( '菌种名称有误，请到基础数据中核实' )
        degradation_referenceRanges = ReferenceRange.objects.filter( index_name = DegradationIndexes._meta.get_field(
            'degradation' ).verbose_name , carbon_source = carbons [0] , tax_name = genuss [0].english_name )
        gas_referenceRanges = ReferenceRange.objects.filter( index_name = DegradationIndexes._meta.get_field(
            'gas' ).verbose_name , carbon_source = carbons [0] , tax_name = genuss [0].english_name )
        if degradation_referenceRanges.count( ) == 0:
            raise forms.ValidationError( '%s 降解率有误，请到基础数据中核实。' % genuss [0].english_name )
        if gas_referenceRanges.count( ) == 0:
            raise forms.ValidationError( '%s 产气量有误，请到基础数据中核实。' % genuss [0].english_name )

    def get_or_init_instance(self , instance_loader , row):
        """
        Either fetches an already existing instance or initializes a new one.
        """
        instance = self.get_instance( instance_loader , row )
        row ['sample_number'] = row ['样本编号']
        row ['internal_number'] = row ['对内编号']
        row ['carbon_source'] = row ['碳源']
        row ['genus'] = row ['菌种']
        row ['carbon_source_zh'] = row ['碳源中文名称']
        row ['genus_zh'] = row ['菌种中文名称']
        row ['degradation'] = row ['降解率']
        row ['gas'] = row ['产气']
        if instance:
            return instance , False
        else:
            return self.init_instance( row ) , True

    def before_save_instance(self , instance , using_transactions , dry_run):
        """
            Override to add additional logic. Does nothing by default.
        """

        if ReferenceRange.objects.filter( index_name = DegradationIndexes._meta.get_field(
                'degradation' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
            status , reference_range = get_status( DegradationIndexes , instance.carbon_source ,
                                                   instance.genus.english_name , 'degradation' ,
                                                   instance.degradation )
            instance.degradation_reference_range = reference_range
            instance.degradation_status = status
        if ReferenceRange.objects.filter( index_name = DegradationIndexes._meta.get_field(
                'gas' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
            status , reference_range = get_status( DegradationIndexes , instance.carbon_source ,
                                                   instance.genus.english_name , 'gas' , instance.gas )
            instance.gas_reference_range = reference_range
            instance.gas_status = status


@admin.register( DegradationIndexes )
class DegradationIndexesAdmin( ImportExportActionModelAdmin , admin.ModelAdmin ):
    list_display = ('id' , 'sample_number' , 'internal_number' , 'carbon_source' , 'genus' ,
                    'degradation_status_colored' , 'gas_status_colored' , 'is_status')
    list_display_links = ('sample_number' ,)
    ordering = ('-id' ,)
    view_on_site = False
    list_max_show_all = 100
    list_per_page = 20
    list_filter = ('is_status' ,)
    search_fields = ('sample_number' ,)
    resource_class = DegradationIndexesResource
    # form =
    # list_editable =
    actions = ['make_finish' , 'export_admin_action']

    def degradation_status_colored(self , obj):
        if obj.degradation_status == 0:
            return format_html( '<b style="background:{};">{}</b>' , 'red' , obj.get_degradation_status_display( ) )
        elif obj.degradation_status == 2:
            return format_html( '<b style="background:{};">{}</b>' , 'blue' , obj.get_degradation_status_display( ) )
        else:
            return obj.get_degradation_status_display( )

    degradation_status_colored.short_description = "降解率状态"

    def gas_status_colored(self , obj):
        if obj.gas_status == 0:
            return format_html( '<b style="background:{};">{}</b>' , 'red' , obj.get_gas_status_display( ) )
        elif obj.gas_status == 2:
            return format_html( '<b style="background:{};">{}</b>' , 'blue' , obj.get_gas_status_display( ) )
        else:
            return obj.get_gas_status_display( )

    gas_status_colored.short_description = "产气量状态"

    def get_readonly_fields(self , request , obj=None):
        # 根据 obj 是否为空来判断,修改数据时不能修改样本编号，
        if obj:
            self.readonly_fields = ('sample_number' , 'carbon_source' , 'genus')
        else:
            self.readonly_fields = ()
        if request.user.is_superuser:  # TODO 上线时打开
            self.readonly_fields = ()
        return self.readonly_fields

    def get_export_formats(self):
        """
        Returns available export formats.
        """
        formats = (
            base_formats.CSV ,
            base_formats.XLS ,
            base_formats.XLSX ,
            base_formats.TSV ,
        )
        return [f for f in formats if f( ).can_export( )]

    def get_import_formats(self):
        """
        Returns available export formats.
        """
        formats = (
            base_formats.CSV ,
            base_formats.XLS ,
            base_formats.XLSX ,
            base_formats.TSV ,
        )
        return [f for f in formats if f( ).can_import( )]

    def make_finish(self , request , queryset):
        i = 0  # 提交成功的数据
        n = 0  # 提交过的数量
        t = 0  # 选中状态
        for obj in queryset:
            t += 1
            if obj.is_status < 1:
                '''初始化偏高，偏低的异常状态'''
                degradation_unusual , degradation_unusual_created = IndexesUnusual.objects.get_or_create(
                    sample_number = obj.sample_number , check_type = "气压与降解率" )
                if degradation_unusual_created:
                    unusual_high = ""  # 偏高结果
                    unusual_low = ""  # 偏低结果
                else:
                    unusual_high = degradation_unusual.high
                    unusual_low = degradation_unusual.low
                obj_progress , created = Progress.objects.get_or_create( sample_number = obj.sample_number )
                if obj_progress.is_qyjj:
                    obj_progress.degradation_testing_date = datetime.date.today( )
                    obj_progress.degradation_testing_staff = request.user.last_name + ' ' + request.user.first_name
                    obj_progress.save( )
                    obj.is_status = 1  # 1是标记为完成的
                    obj.save( )
                    ''' 整理异常检测结果 '''
                    for key , status in {"degradation": obj.degradation_status , "gas": obj.gas_status}.items( ):
                        if status != 1:
                            if status == 0:
                                unusual_high = "%s,%s,%s,%s;" % (
                                    unusual_high , obj.carbon_source.name , obj.genus.china_name ,
                                    DegradationIndexes._meta.get_field( key ).verbose_name)
                                # if obj.carbon_source.name == "粪便":   # TODO 未来需要是再取消注释
                                #     create_risk( obj , key , DegradationIndexes , "偏高", False)
                            else:
                                unusual_low = "%s,%s,%s,%s;" % (
                                    unusual_low , obj.carbon_source.name , obj.genus.china_name ,
                                    DegradationIndexes._meta.get_field( key ).verbose_name)
                                # if obj.carbon_source.name == "粪便":  # TODO 未来需要是再取消注释
                                #     create_risk( obj , key , DegradationIndexes , "偏低",False )
                    ''' 把异常检测结果存到数据库中 '''
                    degradation_unusual.high = unusual_high
                    degradation_unusual.low = unusual_low
                    degradation_unusual.save( )

                    i += 1
                else:
                    n += 1
            else:
                n += 1
        self.message_user( request , '选择%s条信息，完成操作%s条，不操作%s条' % (t , i , n) , level = messages.SUCCESS )

    make_finish.short_description = '1标记完成'

    def save_model(self , request , obj , form , change):
        if obj.degradation is not None:
            if ReferenceRange.objects.filter( index_name = DegradationIndexes._meta.get_field(
                    'degradation' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
                status , reference_range = get_status( DegradationIndexes , obj.carbon_source ,
                                                       obj.genus.english_name , 'degradation' ,
                                                       obj.degradation )
                obj.degradation_reference_range = reference_range
                obj.degradation_status = status
            else:
                self.message_user( request , '降解率 检测指标没有参考范围的基础数据，请先添加基础数据中心' , level = messages.ERROR )

        if obj.gas is not None:
            if ReferenceRange.objects.filter( index_name = DegradationIndexes._meta.get_field(
                    'gas' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
                status , reference_range = get_status( DegradationIndexes , obj.carbon_source ,
                                                       obj.genus.english_name , 'gas' , obj.gas )
                obj.gas_reference_range = reference_range
                obj.gas_status = status
            else:
                self.message_user( request , '产气量 检测指标没有参考范围的基础数据，请先添加基础数据中心' , level = messages.ERROR )
        obj.save( )


@admin.register( IndexesUnusual )
class IndexesUnusualAdmin( ImportExportActionModelAdmin , admin.ModelAdmin ):
    list_display = ('sample_number' , 'internal_number' , 'check_type')
    list_display_links = ('sample_number' ,)
    ordering = ('-id' ,)
    view_on_site = False
    list_max_show_all = 100
    list_per_page = 20
    list_filter = ('check_type' ,)
    search_fields = ('sample_number' ,)
    # resource_class = DegradationIndexesResource
    # form =
    # list_editable =
    # actions = ['make_finish' , 'export_admin_action']


@admin.register( MetaRiskIndexes )
class MetaRiskIndexesAdmin( ImportExportActionModelAdmin , admin.ModelAdmin ):
    list_display = (
        'id' , 'sample_number' , 'internal_number' , 'carbon_source' , 'genus' , 'index_name' , 'is_status' ,
        'blood_fat' ,
        'fat')
    list_display_links = ('sample_number' ,)
    ordering = ('-id' ,)
    view_on_site = False
    list_max_show_all = 100
    list_per_page = 20
    list_filter = ('genus' , 'index_name')
    search_fields = ('sample_number' ,)


@admin.register( GutRiskIndexes )
class GutRiskIndexesAdmin( ImportExportActionModelAdmin , admin.ModelAdmin ):
    list_display = ('id' ,
                    'sample_number' , 'internal_number' , 'carbon_source' , 'genus' , 'index_name' , 'is_status' ,
                    'infection' , 'scherm' , 'cancer')
    list_display_links = ('sample_number' ,)
    ordering = ('-id' ,)
    view_on_site = False
    list_max_show_all = 100
    list_per_page = 20
    list_filter = ('genus' , 'index_name')
    search_fields = ('sample_number' ,)
