import datetime
from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportActionModelAdmin
from import_export.formats import base_formats
from django import forms
from labinformation.models import BioChemicalIndexes
from labinformation.models import ConventionalIndex
from labinformation.models import DegradationIndexes
from labinformation.models import QpcrIndexes
from labinformation.models import ScfasIndexes
from basicdata.models import CTformula
from formula import Solver
from basicdata.models import ReferenceRange
from basicdata.models import Carbon
from basicdata.models import Genus
from django.contrib import messages
from examinationsample.models import Progress , Sample
from examinationsample.admin import tran_format
admin.site.empty_value_display = '-empty-'


def get_referenceRange(objects , carbon_source , tax_name , field_name , obj_field):
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
        tax_name = tax_name ) [0]
    mi = obj.min_value
    ma = obj.max_value
    mi = float( mi )
    ma = float( ma )
    if obj_field < mi:
        obj_field_status = 2  # 偏低
    elif obj_field > ma:
        obj_field_status = 0  # 偏高
    else:
        obj_field_status = 1  # 正常
    result = str( tran_format( mi ) ) + '~' + str( tran_format( ma ) )

    if (mi == 1) and (ma == 1):
        result = "1"
    if (mi == 0) and (ma == 0):
        result = "0"
    print( result )
    return obj_field_status , result


class ConventionalIndexResource( resources.ModelResource ):
    class Meta:
        model = ConventionalIndex
        skip_unchanged = True
        fields = (
            'id' , 'sample_number' , 'carbon_source' , 'genus' , 'carbon_source_zh' , 'genus_zh' , 'occult_Tf' ,
            'occult_Hb' , 'hp' , 'calprotectin' ,
            'ph_value' ,
            'sample_type' , 'colour')
        export_order = (
            'id' , 'sample_number' , 'carbon_source' , 'genus' , 'carbon_source_zh' , 'genus_zh' , 'occult_Tf' ,
            'occult_Hb' , 'hp' , 'calprotectin' ,
            'ph_value' ,
            'sample_type' , 'colour')

    def get_diff_headers(self):
        return ['id' , '样本编号' , '碳源' , '菌种' , '碳源中文名称' , '菌种中文名称' , '潜血双联-Tf' , '潜血双联-Hb' , '幽门螺旋杆菌 抗原（HP-Ag）' ,
                '钙卫蛋白' , 'PH值' ,
                '样本类型' , '颜色' , '松软程度' , '布里斯托']

    def get_export_headers(self):
        return ['id' , '样本编号' , '碳源' , '菌种' , '碳源中文名称' , '菌种中文名称' , '潜血双联-Tf' , '潜血双联-Hb' , '幽门螺旋杆菌 抗原（HP-Ag）' ,
                '钙卫蛋白' , 'PH值' ,
                '样本类型' , '颜色' , '松软程度' , '布里斯托']

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
            status , reference_range = get_referenceRange( ConventionalIndex , instance.carbon_source ,
                                                           instance.genus.english_name , 'occult_Tf' ,
                                                           instance.occult_Tf )
            instance.occult_Tf_reference_range = reference_range
            instance.occult_Tf_status = status
        if ReferenceRange.objects.filter( index_name = ConventionalIndex._meta.get_field(
                'occult_Tf' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
            status , reference_range = get_referenceRange( ConventionalIndex , instance.carbon_source ,
                                                           instance.genus.english_name , 'occult_Hb' ,
                                                           instance.occult_Hb )
            instance.occult_Hb_reference_range = reference_range
            instance.occult_Hb_status = status
        if ReferenceRange.objects.filter( index_name = ConventionalIndex._meta.get_field(
                'hp' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
            status , reference_range = get_referenceRange( ConventionalIndex , instance.carbon_source ,
                                                           instance.genus.english_name , 'hp' , instance.hp )
            instance.hp_reference_range = reference_range
            instance.hp_status = status
        if ReferenceRange.objects.filter( index_name = ConventionalIndex._meta.get_field(
                'calprotectin' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
            status , reference_range = get_referenceRange( ConventionalIndex , instance.carbon_source ,
                                                           instance.genus.english_name , 'calprotectin' ,
                                                           instance.calprotectin )
            instance.calprotectin_reference_range = reference_range
            instance.calprotectin_status = status
        if ReferenceRange.objects.filter( index_name = ConventionalIndex._meta.get_field(
                'ph_value' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
            status , reference_range = get_referenceRange( ConventionalIndex , instance.carbon_source ,
                                                           instance.genus.english_name , 'ph_value' ,
                                                           instance.ph_value )
            instance.ph_value_reference_range = reference_range
            instance.ph_value_status = status


@admin.register( ConventionalIndex )
class ConventionalIndexAdmin( ImportExportActionModelAdmin , admin.ModelAdmin ):
    list_display = (
        'id' , 'sample_number' , 'carbon_source' , 'genus' , 'occult_Tf' , 'occult_Hb' , 'hp' , 'calprotectin' ,
        'ph_value' ,
        'sample_type' , 'colour' , 'is_status')
    list_display_links = ('sample_number' ,)
    ordering = ('-sample_number' ,)
    view_on_site = False
    list_max_show_all = 100
    list_per_page = 20
    list_filter = ('is_status' ,)
    search_fields = ('sample_number' ,)
    resource_class = ConventionalIndexResource
    # form = ConventionalIndexForm
    # list_editable =
    actions = ['make_finish' , 'export_admin_action']

    def get_readonly_fields(self , request , obj=None):
        # 根据 obj 是否为空来判断,修改数据时不能修改样本编号，
        if obj:
            self.readonly_fields = (
                'sample_number' , 'carbon_source' , 'genus' , 'occult_Tf_status' , 'occult_Tf_reference_range' ,
                'occult_Hb_status' , 'occult_Hb_reference_range' , 'hp_status' , 'hp_reference_range' ,
                'calprotectin_status' , 'calprotectin_reference_range' , 'ph_value_status' ,
                'ph_value_reference_range' ,
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
                obj_progress , created = Progress.objects.get_or_create( sample_number = obj.sample_number )
                if obj_progress.is_cgzb:
                    obj_progress.cgzb_testing_date = datetime.date.today( )
                    obj_progress.cgzb_testing_staff = request.user.last_name + ' ' + request.user.first_name
                    obj_progress.save( )
                    obj.is_status = 2  # 2是标记为完成的
                    obj.save( )
                    i += 1
                else:
                    n += 1
            else:
                n += 1
        self.message_user( request , '选择%s条信息，完成操作%s条，不操作%s条' % (t , i , n) , level = messages.SUCCESS )

    make_finish.short_description = '1标记完成'

    def save_model(self , request , obj , form , change):
        if obj.occult_Tf is not None:
            if ReferenceRange.objects.filter( index_name = ConventionalIndex._meta.get_field(
                    'occult_Tf' ).verbose_name , carbon_source = obj.carbon_source ,
                                              tax_name = obj.genus.english_name ).count( ) != 0:  # 根据字段的名称查询参考访问
                status , reference_range = get_referenceRange( ConventionalIndex , obj.carbon_source ,
                                                               obj.genus.english_name , 'occult_Tf' , obj.occult_Tf )
                obj.occult_Tf_reference_range = reference_range
                obj.occult_Tf_status = status
            else:
                self.message_user( request , '潜血双联-Tf 检测指标没有参考范围的基础数据，请先添加基础数据中心' , level = messages.ERROR )

        if obj.occult_Hb is not None:
            if ReferenceRange.objects.filter( index_name = ConventionalIndex._meta.get_field(
                    'occult_Hb' ).verbose_name , carbon_source = obj.carbon_source ,
                                              tax_name = obj.genus.english_name ).count( ) != 0:  # 根据字段的名称查询参考访问
                status , reference_range = get_referenceRange( ConventionalIndex , obj.carbon_source ,
                                                               obj.genus.english_name , 'occult_Hb' , obj.occult_Hb )
                obj.occult_Hb_reference_range = reference_range
                obj.occult_Hb_status = status

            else:
                self.message_user( request , '潜血双联-Hb 检测指标没有参考范围的基础数据，请先添加基础数据中心' , level = messages.ERROR )

        if obj.hp is not None:
            if ReferenceRange.objects.filter( index_name = ConventionalIndex._meta.get_field(
                    'hp' ).verbose_name , carbon_source = obj.carbon_source ,
                                              tax_name = obj.genus.english_name ).count( ) != 0:  # 根据字段的名称查询参考访问
                status , reference_range = get_referenceRange( ConventionalIndex , obj.carbon_source ,
                                                               obj.genus.english_name , 'hp' , obj.hp )
                obj.hp_reference_range = reference_range
                obj.hp_status = status
            else:
                self.message_user( request , '幽门螺旋杆菌 抗原（HP-Ag）检测指标没有参考范围的基础数据，请先添加基础数据中心' , level = messages.ERROR )

        if obj.calprotectin is not None:
            if ReferenceRange.objects.filter( index_name = ConventionalIndex._meta.get_field(
                    'calprotectin' ).verbose_name , carbon_source = obj.carbon_source ,
                                              tax_name = obj.genus.english_name ).count( ) != 0:  # 根据字段的名称查询参考访问
                status , reference_range = get_referenceRange( ConventionalIndex , obj.carbon_source ,
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

                status , reference_range = get_referenceRange( ConventionalIndex , obj.carbon_source ,
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
            'id' , 'sample_number' , 'carbon_source' , 'genus' , 'carbon_source_zh' , 'genus_zh' , 'fecal_nitrogen' ,
            'bile_acid')
        export_order = (
            'id' , 'sample_number' , 'carbon_source' , 'genus' , 'carbon_source_zh' , 'genus_zh' , 'fecal_nitrogen' ,
            'bile_acid')

    def get_diff_headers(self):
        return ['id' , '样本编号' , '碳源' , '菌种' , '碳源中文名称' , '菌种中文名称' , '粪氨' , '胆汁酸']

    def get_export_headers(self):
        return ['id' , '样本编号' , '碳源' , '菌种' , '碳源中文名称' , '菌种中文名称' , '粪氨' , '胆汁酸']

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
                'occult_Tf' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
            status , reference_range = get_referenceRange( BioChemicalIndexes , instance.carbon_source ,
                                                           instance.genus.english_name , 'fecal_nitrogen' ,
                                                           instance.fecal_nitrogen )
            instance.fecal_nitrogen_reference_range = reference_range
            instance.fecal_nitrogen_status = status
        if ReferenceRange.objects.filter( index_name = BioChemicalIndexes._meta.get_field(
                'bile_acid' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
            status , reference_range = get_referenceRange( BioChemicalIndexes , instance.carbon_source ,
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
    list_display = ('id' , 'sample_number' , 'carbon_source' , 'genus' , 'fecal_nitrogen' , 'bile_acid' , 'is_status')
    list_display_links = ('sample_number' ,)
    ordering = ('-sample_number' ,)
    view_on_site = False
    list_max_show_all = 100
    list_per_page = 20
    list_filter = ('is_status' ,)
    search_fields = ('sample_number' ,)
    resource_class = BioChemicalIndexesResource
    form = BioChemicalIndexesForm
    # list_editable =
    actions = ['make_finish' , 'export_admin_action']

    def get_readonly_fields(self , request , obj=None):
        # 根据 obj 是否为空来判断,修改数据时不能修改样本编号，
        if obj:
            self.readonly_fields = (
                'sample_number' , 'carbon_source' , 'genus' , 'fecal_nitrogen_status' ,
                'fecal_nitrogen_reference_range' ,
                'bile_acid_status' , 'bile_acid_reference_range' , 'is_status')
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
                obj_progress , created = Progress.objects.get_or_create( sample_number = obj.sample_number )
                if obj_progress.is_shzb:
                    obj_progress.shzb_testing_date = datetime.date.today( )
                    obj_progress.shzb_testing_staff = request.user.last_name + ' ' + request.user.first_name
                    obj_progress.save( )
                    obj.is_status = 2  # 2是标记为完成的
                    obj.save( )
                    i += 1
                else:
                    n += 1
            else:
                n += 1
        self.message_user( request , '选择%s条信息，完成操作%s条，不操作%s条' % (t , i , n) , level = messages.SUCCESS )

    make_finish.short_description = '1标记完成'

    def save_model(self , request , obj , form , change):
        if obj.fecal_nitrogen is not None:
            if ReferenceRange.objects.filter( index_name = BioChemicalIndexes._meta.get_field(
                    'fecal_nitrogen' ).verbose_name , carbon_source = obj.carbon_source ,
                                              tax_name = obj.genus.english_name ).count( ) != 0:  # 根据字段的名称查询参考访问
                status , reference_range = get_referenceRange( BioChemicalIndexes , obj.carbon_source ,
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
                status , reference_range = get_referenceRange( BioChemicalIndexes , obj.carbon_source ,
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
            'id' , 'sample_number' , 'carbon_source' , 'genus' , 'carbon_source_zh' , 'genus_zh' , 'ct' ,
            'formula_number' ,
            'concentration')
        export_order = (
            'id' , 'sample_number' , 'carbon_source' , 'genus' , 'carbon_source_zh' , 'genus_zh' , 'ct' ,
            'formula_number' ,
            'concentration')

    def get_diff_headers(self):
        return ['id' , '样本编号' , '碳源' , '菌种' , '碳源中文名称' , '菌种中文名称' , 'ct' , '公式编号' , '浓度']

    def get_export_headers(self):
        return ['id' , '样本编号' , '碳源' , '菌种' , '碳源中文名称' , '菌种中文名称' , 'ct' , '公式编号' , '浓度']

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
            instance.concentration = float( formula( point ) )
            if ReferenceRange.objects.filter( index_name = QpcrIndexes._meta.get_field(
                    'concentration' ).verbose_name , carbon_source = instance.carbon_source ,
                                              tax_name = instance.genus.english_name ).count( ) != 0:  # 根据字段的名称查询参考范围
                status , reference_range = get_referenceRange( QpcrIndexes , instance.carbon_source ,
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


@admin.register( QpcrIndexes )
class QpcrIndexesAdmin( ImportExportActionModelAdmin , admin.ModelAdmin ):
    list_display = (
        'id' , 'sample_number' , 'carbon_source' , 'genus' , 'ct' , 'concentration' , 'concentration_reference_range' ,
        'concentration_status' , 'formula_number' , 'is_status')
    list_display_links = ('sample_number' ,)
    ordering = ('-sample_number' ,)
    view_on_site = False
    list_max_show_all = 100
    list_per_page = 38
    list_filter = ('is_status' ,)
    search_fields = ('sample_number' ,)
    resource_class = QpcrIndexesResource
    form = QpcrIndexesForm
    # list_editable =
    actions = ['make_finish' , 'export_admin_action']
    fields = (
        'sample_number' , 'carbon_source' , 'genus' , 'ct' , 'concentration' , 'concentration_reference_range' ,
        'concentration_status' ,
        'formula_number' , 'is_status')

    def get_readonly_fields(self , request , obj=None):
        # 根据 obj 是否为空来判断,修改数据时不能修改样本编号，
        if obj:
            self.readonly_fields = (
                'sample_number' , 'concentration' , 'concentration_reference_range' , 'concentration_status')
        else:
            self.readonly_fields = ('concentration' , 'concentration_reference_range' , 'concentration_status')
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
                obj_progress , created = Progress.objects.get_or_create( sample_number = obj.sample_number )
                if obj_progress.is_qpcr:
                    obj_progress.qPCR_testing_date = datetime.date.today( )
                    obj_progress.qPCR_testing_staff = request.user.last_name + ' ' + request.user.first_name
                    obj_progress.save( )
                    obj.is_status = 2  # 2是标记为完成的
                    obj.save( )
                    i += 1
                else:
                    n += 1
            else:
                n += 1
        self.message_user( request , '选择%s条信息，完成操作%s条，不操作%s条' % (t , i , n) , level = messages.SUCCESS )

    make_finish.short_description = '1标记完成'

    def get_changeform_initial_data(self , request):
        initial = super( ).get_changeform_initial_data( request )
        initial ['formula_number'] = CTformula.objects.filter( formula_group__id = 2 ).order_by( '-create_date' ) [
            0].number  # id 为2的一定为“CT浓度换算” 类别
        return initial

    def save_model(self , request , obj , form , change):
        formula_content = CTformula.objects.filter( number = obj.formula_number ) [0].formula_content
        formula = Solver( formula_content , precision = 32 )
        point = {'x': obj.ct}
        obj.concentration = float( formula( point ) )
        if ReferenceRange.objects.filter( index_name = QpcrIndexes._meta.get_field(
                'concentration' ).verbose_name , carbon_source = obj.carbon_source ,
                                          tax_name = obj.genus.english_name ).count( ) != 0:  # 根据字段的名称查询参考访问
            status , reference_range = get_referenceRange( QpcrIndexes , obj.carbon_source ,
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
        fields = ('id' , 'sample_number' , 'carbon_source' , 'genus' , 'carbon_source_zh' , 'genus_zh' ,
                  'total_acid' , 'acetic_acid' , 'propionic' , 'butyric' , 'isobutyric_acid' , 'valeric' ,
                  'isovaleric' ,
                  'acid_first' , 'acid_second')
        export_order = ('id' , 'sample_number' , 'carbon_source' , 'genus' , 'carbon_source_zh' , 'genus_zh' ,
                        'total_acid' , 'acetic_acid' , 'propionic' , 'butyric' , 'isobutyric_acid' , 'valeric' ,
                        'isovaleric' ,
                        'acid_first' , 'acid_second')

    def get_diff_headers(self):
        return ['id' , '样本编号' , '碳源' , '菌种' , '碳源中文名称' , '菌种中文名称' , '总酸' , '乙酸' , '丙酸' , '丁酸' ,
                '异丁酸' , '戊酸' , '异戊酸' , '乙丙丁酸占总酸比' , '异丁戊异戊占总酸比']

    def get_export_headers(self):
        return ['id' , '样本编号' , '碳源' , '菌种' , '碳源中文名称' , '菌种中文名称' , '总酸' , '乙酸' , '丙酸' , '丁酸' ,
                '异丁酸' , '戊酸' , '异戊酸' , '乙丙丁酸占总酸比' , '异丁戊异戊占总酸比']

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

        if total_acid_referenceRanges.count( ) == 0:
            raise forms.ValidationError( '%s 总酸参考范围有误，请到基础数据中核实。' % (genuss [0].english_name) )
        if acetic_acid_referenceRanges.count( ) == 0:
            raise forms.ValidationError( '%s 乙酸参考范围有误，请到基础数据中核实。' % (genuss [0].english_name) )
        if propionic_referenceRanges.count( ) == 0:
            raise forms.ValidationError( '%s 丙酸参考范围有误，请到基础数据中核实' % (genuss [0].english_name) )
        if butyric_referenceRanges.count( ) == 0:
            raise forms.ValidationError( '%s 丁酸参考范围有误，请到基础数据中核实' % (genuss [0].english_name) )
        if isobutyric_acid_referenceRanges.count( ) == 0:
            raise forms.ValidationError( '%s 异丁酸参考范围有误，请到基础数据中核实' % (genuss [0].english_name) )
        if valeric_referenceRanges.count( ) == 0:
            raise forms.ValidationError( '%s 戊酸参考范围有误，请到基础数据中核实' % (genuss [0].english_name) )
        if isovaleric_reference_ranges.count( ) == 0:
            raise forms.ValidationError( '%s 异戊酸参考参考范围有误，请到基础数据中核实' % (genuss [0].english_name) )
        if isovaleric1_reference_ranges.count( ) == 0:
            raise forms.ValidationError( '%s 扩展酸1参考范围有误，请到基础数据中核实' % (genuss [0].english_name) )
        if isovaleric2_reference_ranges.count( ) == 0:
            raise forms.ValidationError( '%s 扩展酸2参考范围有误，请到基础数据中核实' % (genuss [0].english_name) )
        if isovaleric3_reference_ranges.count( ) == 0:
            raise forms.ValidationError( '%s 扩展酸3参考范围有误，请到基础数据中核实' % (genuss [0].english_name) )
        if acid_first_reference_ranges.count( ) == 0:
            raise forms.ValidationError( '%s 乙丙丁酸占总酸比参考范围有误，请到基础数据中核实' % (genuss [0].english_name) )
        if acid_second_reference_ranges.count( ) == 0:
            raise forms.ValidationError( '%s 异丁戊异戊占总酸比参考范围有误，请到基础数据中核实' % (genuss [0].english_name) )

    def get_or_init_instance(self , instance_loader , row):
        """
        Either fetches an already existing instance or initializes a new one.
        """
        instance = self.get_instance( instance_loader , row )
        row ['sample_number'] = row ['样本编号']
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

        if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                'total_acid' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
            status , reference_range = get_referenceRange( ScfasIndexes , instance.carbon_source ,
                                                           instance.genus.english_name , 'total_acid' ,
                                                           instance.total_acid )
            instance.total_acid_reference_range = reference_range
            instance.total_acid_status = status
        if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                'acetic_acid' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
            status , reference_range = get_referenceRange( ScfasIndexes , instance.carbon_source ,
                                                           instance.genus.english_name , 'acetic_acid' ,
                                                           instance.acetic_acid )
            instance.acetic_acid_reference_range = reference_range
            instance.acetic_acid_status = status
        if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                'propionic' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
            status , reference_range = get_referenceRange( ScfasIndexes , instance.carbon_source ,
                                                           instance.genus.english_name , 'propionic' ,
                                                           instance.propionic )
            instance.propionic_reference_range = reference_range
            instance.propionic_status = status
        if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                'butyric' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
            status , reference_range = get_referenceRange( ScfasIndexes , instance.carbon_source ,
                                                           instance.genus.english_name , 'butyric' , instance.butyric )
            instance.butyric_reference_range = reference_range
            instance.butyric_status = status
        if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                'isobutyric_acid' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
            status , reference_range = get_referenceRange( ScfasIndexes , instance.carbon_source ,
                                                           instance.genus.english_name , 'isobutyric_acid' ,
                                                           instance.isobutyric_acid )
            instance.isobutyric_acid_reference_range = reference_range
            instance.isobutyric_acid_status = status
        if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                'valeric' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
            status , reference_range = get_referenceRange( ScfasIndexes , instance.carbon_source ,
                                                           instance.genus.english_name , 'valeric' , instance.valeric )
            instance.valeric_reference_range = reference_range
            instance.valeric_status = status
        if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                'isovaleric' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
            status , reference_range = get_referenceRange( ScfasIndexes , instance.carbon_source ,
                                                           instance.genus.english_name , 'isovaleric' ,
                                                           instance.isovaleric )
            instance.isovaleric_reference_range = reference_range
            instance.isovaleric_status = status
        if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                'acid_first' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
            status , reference_range = get_referenceRange( ScfasIndexes , instance.carbon_source ,
                                                           instance.genus.english_name , 'acid_first' ,
                                                           instance.acid_first )
            instance.acid_first_reference_range = reference_range
            instance.acid_first_status = status
        if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                'acid_second' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
            status , reference_range = get_referenceRange( ScfasIndexes , instance.carbon_source ,
                                                           instance.genus.english_name , 'acid_second' ,
                                                           instance.acid_second )
            instance.acid_second_reference_range = reference_range
            instance.acid_second_status = status


@admin.register( ScfasIndexes )
class ScfasIndexesAdmin( ImportExportActionModelAdmin , admin.ModelAdmin ):
    list_display = ('id' , 'sample_number' , 'carbon_source' , 'genus' ,
                    'total_acid' , 'acetic_acid' , 'propionic' , 'butyric' , 'isobutyric_acid' , 'valeric' ,
                    'isovaleric' ,
                    'acid_first' , 'acid_second' , 'is_status')
    list_display_links = ('sample_number' ,)
    ordering = ('-sample_number' ,)
    view_on_site = False
    list_max_show_all = 100
    list_per_page = 20
    list_filter = ('is_status' ,)
    search_fields = ('sample_number' ,)
    import_export_args = {'import_resource_class': ScfasIndexesResource , 'export_resource_class': ScfasIndexesResource}
    resource_class = ScfasIndexesResource
    # form =
    # list_editable =
    actions = ['make_save' , 'make_finish' , 'export_admin_action']
    exclude = (
    'isovaleric1' , 'isovaleric1_status' , 'isovaleric1_reference_range' , 'isovaleric2' , 'isovaleric2_status' ,
    'isovaleric2_reference_range' , 'isovaleric3' , 'isovaleric3_status' , 'isovaleric3_reference_range','carbon_source_zh','genus_zh')

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

    def make_save(self , request , queryset):
        i = 0  # 提交成功的数据
        n = 0  # 提交过的数量
        t = 0  # 选中状态
        for obj in queryset:
            t += 1
            super( ).save_model( request , obj , self.form , self.change )
            i += 1
        self.message_user( request , '选择%s条信息，完成操作%s条，不操作%s条' % (t , i , n) , level = messages.SUCCESS )

    make_save.short_description = '1保存'

    def make_finish(self , request , queryset):
        i = 0  # 提交成功的数据
        n = 0  # 提交过的数量
        t = 0  # 选中状态
        for obj in queryset:
            t += 1
            if obj.is_status < 1:
                obj_progress , created = Progress.objects.get_or_create( sample_number = obj.sample_number )
                if obj_progress.is_scfa:
                    obj_progress.SCFAs_testing_date = datetime.date.today( )
                    obj_progress.SCFAs_testing_staff = request.user.last_name + ' ' + request.user.first_name
                    obj_progress.save( )
                    obj.is_status = 2  # 2是标记为完成的
                    obj.save( )
                    i += 1
                else:
                    n += 1
            else:
                n += 1
        self.message_user( request , '选择%s条信息，完成操作%s条，不操作%s条' % (t , i , n) , level = messages.SUCCESS )

    make_finish.short_description = '2标记完成'

    def save_model(self , request , obj , form , change):

        if obj.acetic_acid is not None:
            if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                    'acetic_acid' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问

                status , reference_range = get_referenceRange( ScfasIndexes , obj.carbon_source ,
                                                               obj.genus.english_name , 'acetic_acid' ,
                                                               obj.acetic_acid )
                obj.acetic_acid_reference_range = reference_range
                obj.acetic_acid_status = status
            else:
                self.message_user( request , '乙酸 检测指标没有参考范围的基础数据，请先添加基础数据中心' , level = messages.ERROR )
        if obj.propionic is not None:
            if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                    'propionic' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
                status , reference_range = get_referenceRange( ScfasIndexes , obj.carbon_source ,
                                                               obj.genus.english_name , 'propionic' , obj.propionic )
                obj.propionic_reference_range = reference_range
                obj.propionic_status = status
            else:
                self.message_user( request , '丙酸 检测指标没有参考范围的基础数据，请先添加基础数据中心' , level = messages.ERROR )
        if obj.butyric is not None:
            if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                    'butyric' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
                status , reference_range = get_referenceRange( ScfasIndexes , obj.carbon_source ,
                                                               obj.genus.english_name , 'butyric' , obj.butyric )
                obj.butyric_reference_range = reference_range
                obj.butyric_status = status
            else:
                self.message_user( request , '丁酸 检测指标没有参考范围的基础数据，请先添加基础数据中心' , level = messages.ERROR )
        if obj.isobutyric_acid is not None:
            if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                    'isobutyric_acid' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
                status , reference_range = get_referenceRange( ScfasIndexes , obj.carbon_source ,
                                                               obj.genus.english_name , 'isobutyric_acid' ,
                                                               obj.isobutyric_acid )
                obj.isobutyric_acid_reference_range = reference_range
                obj.isobutyric_acid_status = status
            else:
                self.message_user( request , '异丁酸 检测指标没有参考范围的基础数据，请先添加基础数据中心' , level = messages.ERROR )
        if obj.valeric is not None:
            if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                    'valeric' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
                status , reference_range = get_referenceRange( ScfasIndexes , obj.carbon_source ,
                                                               obj.genus.english_name , 'valeric' , obj.valeric )
                obj.valeric_reference_range = reference_range
                obj.valeric_status = status
            else:
                self.message_user( request , '戊酸 检测指标没有参考范围的基础数据，请先添加基础数据中心' , level = messages.ERROR )
        if obj.isovaleric is not None:
            if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                    'isovaleric' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
                status , reference_range = get_referenceRange( ScfasIndexes , obj.carbon_source ,
                                                               obj.genus.english_name , 'isovaleric' , obj.isovaleric )
                obj.isovaleric_reference_range = reference_range
                obj.isovaleric_status = status
            else:
                self.message_user( request , '异戊酸 检测指标没有参考范围的基础数据，请先添加基础数据中心' , level = messages.ERROR )

        if (obj.acetic_acid is not None) and (obj.propionic is not None) and (obj.butyric is not None) and (
                obj.isobutyric_acid is not None) and (obj.valeric is not None) and (obj.isovaleric is not None):
            obj.total_acid = obj.acetic_acid + obj.propionic + obj.butyric + obj.isobutyric_acid + obj.valeric + \
                             obj.isovaleric

        if (obj.acetic_acid is not None) and (obj.propionic is not None) and (obj.butyric is not None):
            obj.acid_first = (obj.acetic_acid + obj.propionic + obj.butyric) / obj.total_acid

        if (obj.isobutyric_acid is not None) and (obj.valeric is not None) and (obj.isovaleric is not None):
            obj.acid_second = (obj.isobutyric_acid + obj.valeric + obj.isovaleric) / obj.total_acid

        if obj.acid_first is not None:
            if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                    'acid_first' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
                status , reference_range = get_referenceRange( ScfasIndexes , obj.carbon_source ,
                                                               obj.genus.english_name , 'acid_first' , obj.acid_first )
                obj.acid_first_reference_range = reference_range
                obj.acid_first_status = status

            else:
                self.message_user( request , '乙丙丁酸占总酸比 检测指标没有参考范围的基础数据，请先添加基础数据中心' , level = messages.ERROR )

        if obj.acid_second is not None:
            if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                    'acid_second' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
                status , reference_range = get_referenceRange( ScfasIndexes , obj.carbon_source ,
                                                               obj.genus.english_name , 'acid_second' ,
                                                               obj.acid_second )
                obj.acid_second_reference_range = reference_range
                obj.acid_second_status = status
            else:
                self.message_user( request , '异丁戊异戊占总酸比 检测指标没有参考范围的基础数据，请先添加基础数据中心' , level = messages.ERROR )

        if obj.total_acid is not None:
            if ReferenceRange.objects.filter( index_name = ScfasIndexes._meta.get_field(
                    'total_acid' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
                status , reference_range = get_referenceRange( ScfasIndexes , obj.carbon_source ,
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
            'id' , 'sample_number' , 'carbon_source' , 'genus' , 'carbon_source_zh' , 'genus_zh' , 'degradation' ,
            'gas')
        export_order = (
            'id' , 'sample_number' , 'carbon_source' , 'genus' , 'carbon_source_zh' , 'genus_zh' , 'degradation' ,
            'gas')

    def get_export_headers(self):
        return ['id' , '样本编号' , '碳源' , '菌种' , '碳源中文名称' , '菌种中文名称' , '降解率' , '产气']

    def get_diff_headers(self):
        return ['id' , '样本编号' , '碳源' , '菌种' , '碳源中文名称' , '菌种中文名称' , '降解率' , '产气']

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
            status , reference_range = get_referenceRange( DegradationIndexes , instance.carbon_source ,
                                                           instance.genus.english_name , 'degradation' ,
                                                           instance.degradation )
            instance.degradation_reference_range = reference_range
            instance.degradation_status = status
        if ReferenceRange.objects.filter( index_name = DegradationIndexes._meta.get_field(
                'gas' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
            status , reference_range = get_referenceRange( DegradationIndexes , instance.carbon_source ,
                                                           instance.genus.english_name , 'gas' , instance.gas )
            instance.gas_reference_range = reference_range
            instance.gas_status = status


@admin.register( DegradationIndexes )
class DegradationIndexesAdmin( ImportExportActionModelAdmin , admin.ModelAdmin ):
    list_display = ('sample_number' , 'carbon_source' , 'genus' ,
                    'degradation' , 'gas' , 'is_status')
    list_display_links = ('sample_number' ,)
    ordering = ('-sample_number' ,)
    view_on_site = False
    list_max_show_all = 100
    list_per_page = 20
    list_filter = ('is_status' ,)
    search_fields = ('sample_number' ,)
    resource_class = DegradationIndexesResource
    # form =
    # list_editable =
    actions = ['make_finish' , 'export_admin_action']

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
                obj_progress , created = Progress.objects.get_or_create( sample_number = obj.sample_number )
                if obj_progress.is_qyjj:
                    obj_progress.degradation_testing_date = datetime.date.today( )
                    obj_progress.degradation_testing_staff = request.user.last_name + ' ' + request.user.first_name
                    obj_progress.save( )
                    obj.is_status = 2  # 2是标记为完成的
                    obj.save( )
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
                status , reference_range = get_referenceRange( DegradationIndexes , obj.carbon_source ,
                                                               obj.genus.english_name , 'degradation' ,
                                                               obj.degradation )
                obj.degradation_reference_range = reference_range
                obj.degradation_status = status
            else:
                self.message_user( request , '降解率 检测指标没有参考范围的基础数据，请先添加基础数据中心' , level = messages.ERROR )

        if obj.gas is not None:
            if ReferenceRange.objects.filter( index_name = DegradationIndexes._meta.get_field(
                    'gas' ).verbose_name ).count( ) != 0:  # 根据字段的名称查询参考访问
                status , reference_range = get_referenceRange( DegradationIndexes , obj.carbon_source ,
                                                               obj.genus.english_name , 'gas' , obj.gas )
                obj.gas_reference_range = reference_range
                obj.gas_status = status
            else:
                self.message_user( request , '产气量 检测指标没有参考范围的基础数据，请先添加基础数据中心' , level = messages.ERROR )
        obj.save( )
