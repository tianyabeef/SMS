from django import forms
from django.contrib import admin
from import_export import resources
from basicdata.models import Agent , Province , Age , CheckType , RiskItem , RiskReferenceRange , RiskItemDefault
from basicdata.models import CTformula
from basicdata.models import Carbon
from basicdata.models import CheckItem
from basicdata.models import Genus
from basicdata.models import Product
from basicdata.models import ReferenceRange
from basicdata.models import Template
import datetime
import re
import tablib
from formula import Solver
from basicdata.models import FormulaGroup
from import_export.admin import ImportExportActionModelAdmin
from django.db.models.query import QuerySet

admin.site.empty_value_display = '-empty-'


def tran_format(value):
    if value is not None:
        if float( value ) > 1000 or (0.001 > float( value ) > 0) or float( value ) < -0.001:  # TODO 当数值多少用科学计数法比较合理
            value = "%.2e" % value
    else:
        value = 0
    return value


class FormulaGroupResource( resources.ModelResource ):
    class Meta:
        model = FormulaGroup
        skip_unchanged = True
        fields = ('id' , 'name')
        export_order = ('id' , 'name')


@admin.register( FormulaGroup )
class FormulaGroupAdmin( ImportExportActionModelAdmin , admin.ModelAdmin ):
    list_display = ('id' , 'name' , 'number')
    list_display_links = ('name' ,)
    # readonly_fields =
    ordering = ('id' ,)
    view_on_site = False
    list_max_show_all = 100
    list_per_page = 20
    # list_filter = ['formula_group__name' , ]
    search_fields = ('name' ,)
    resource_class = FormulaGroupResource
    # form =
    # list_editable =
    # actions =


def is_Chinese(word):
    for ch in word:
        if '\u4e00' <= ch <= '\u9fff':
            return True
        if ch is "=":
            return True
    return False


class CTformulaForm( forms.ModelForm ):
    formula_content = forms.CharField( label = "计算公式" , help_text = "示例：(3^2*x^2+x+3e-50)/sin(-pi/2)" ,
                                       required = True , widget = forms.TextInput(
            attrs = {'class': 'form-control' , 'placeholder': '数学计算公式，不能有中文,不能有=号'} ) ,
                                       error_messages = {'required': '这个字段是必填项。'} )

    class Meta:
        model = CTformula
        exclude = ("" ,)

    def clean(self):
        cleaned_data = super( CTformulaForm , self ).clean( )  # 继承父类clean()
        formula_content = cleaned_data.get( 'formula_content' )
        example_data = cleaned_data.get( 'example_data' )
        result_data = cleaned_data.get( 'result_data' )
        tax_name = cleaned_data.get( 'tax_name' )
        if (formula_content is not None) and (example_data is not None) and (result_data is not None):
            if is_Chinese( formula_content ):
                raise forms.ValidationError( "计算公式不能有中文,不能有=号，请检查输入的计算公式" )
            formula = Solver( formula_content , precision = 32 )
            point = {"x": example_data}
            if round( float( formula( point ) ) , 10 ) != float( cleaned_data.get( 'result_data' ) ):
                raise forms.ValidationError(
                    "系统计算预期与输出结果不一致，请检查输出结果。系统的结果是%s" % round( float( formula( point ) ) , 10 ) )

        return cleaned_data

    def clean_tax_name(self):
        if Genus.objects.filter( china_name = self.cleaned_data ["tax_name"] ).count( ) == 0:
            raise forms.ValidationError( "菌种名称在基础数据管理中无法查询到" )
        return self.cleaned_data ["tax_name"]


class CTformulaResource( resources.ModelResource ):
    class Meta:
        model = CTformula
        skip_unchanged = True
        fields = (
            'id' , 'number' , 'formula_group' , 'formula_name' , 'formula_content' , 'tax_name' , 'version_num' ,
            'example_data' , 'result_data' , 'writer' , 'note')
        export_order = (
            'id' , 'number' , 'formula_group' , 'formula_content' , 'formula_name' , 'tax_name' , 'version_num' ,
            'example_data' , 'result_data' , 'writer' , 'note')

    def before_import_row(self , row , **kwargs):
        """
        Calls :meth:`import_export.fields.Field.save` if ``Field.attribute``
        and ``Field.column_name`` are found in ``data``.
        """
        genuss = Genus.objects.filter( china_name = row ['tax_name'] )
        if genuss.count( ) == 0:
            raise forms.ValidationError( '菌属名称有误，请到基础数据中核实。' )
        fgroups = FormulaGroup.objects.filter( id = row ['formula_group'] )
        if fgroups.count( ) == 0:
            raise forms.ValidationError( '公式大类id有误，请到基础数据中核实。' )


@admin.register( CTformula )
class CTformulaAdmin( ImportExportActionModelAdmin , admin.ModelAdmin ):
    list_display = ('number' , 'formula_name' , 'formula_content' , 'tax_name' , 'create_date')
    list_display_links = ('number' , 'formula_name')
    readonly_fields = ('historys' ,)
    ordering = ('-create_date' ,)
    view_on_site = False
    list_max_show_all = 100
    list_per_page = 20
    list_filter = ['formula_group__name' , ]
    search_fields = ('number' ,)
    resource_class = CTformulaResource
    form = CTformulaForm
    # list_editable = ('formula_content' ,)
    # actions =

    fieldsets = (
        ('基本信息' , {
            'fields': ('number' , 'formula_group' , 'version_num' , 'tax_name')
        }) ,
        ('关键信息' , {
            'fields': ('formula_content' , 'example_data' , 'result_data')
        }) ,
        ('历史版本' , {
            'fields': ('historys' , 'writer' , 'note') ,
        }) ,
    )

    def get_changeform_initial_data(self , request):
        initial = super( ).get_changeform_initial_data( request )
        initial ['writer'] = request.user.last_name + ' ' + request.user.first_name
        return initial

    def save_model(self , request , obj , form , change):
        obj.formula_name = obj.formula_group.name
        if obj.historys is None:
            obj.historys = "编号:" + obj.number + ";公式:" + obj.formula_content + ";版本:" + str(
                obj.version_num ) + ";时间:" + datetime.date.today( ).__str__( )
        else:
            obj.historys = obj.historys + "\n" + "编号:" + obj.number + ";公式:" + obj.formula_content + ";版本:" + str(
                obj.version_num ) + ";时间:" + obj.create_date.__str__( )
        # obj.writer = "%s %s" % (request.user.last_name , request.user.first_name)  # 系统自动添加创建人
        obj.save( )


class AgentResource( resources.ModelResource ):
    class Meta:
        model = Agent
        skip_unchanged = True
        fields = (
            'id' , 'number' , 'name' , 'responsible_user' , 'phone' , 'email' , 'area' , 'create_date' ,
            'writer' ,
            'note')
        export_order = (
            'id' , 'number' , 'name' , 'responsible_user' , 'phone' , 'email' , 'area' , 'create_date' ,
            'writer' ,
            'note')


@admin.register( Agent )
class AgentAdmin( ImportExportActionModelAdmin , admin.ModelAdmin ):
    list_display = ('number' , 'name' , 'responsible_user' , 'phone' , 'email' , 'area' , 'create_date')
    list_display_links = ('number' ,)
    readonly_fields = ('historys' ,)
    ordering = ('-create_date' ,)
    view_on_site = False
    list_max_show_all = 100
    list_per_page = 20
    list_filter = ('area' ,)
    search_fields = ('number' , 'name' , 'responsible_user')
    resource_class = AgentResource

    # form
    # list_editable =
    # actions =

    # def get_changeform_initial_data(self , request):
    #     initial = super( ).get_changeform_initial_data( request )
    #     # initial ['writer'] = request.user.last_name + ' ' + request.user.first_name
    #     return initial

    def save_model(self , request , obj , form , change):
        if obj.historys is None:
            obj.historys = "编号:" + obj.number + ";名称:" + obj.name + ";负责人:" + obj.responsible_user.last_name + ";时间:" + datetime.date.today( ).__str__( )
        else:
            obj.historys = obj.historys + "\n" + "编号:" + obj.number + ";名称:" + obj.name + ";负责人:" + obj.responsible_user.last_name + ";时间:" + datetime.date.today( ).__str__( )
        # obj.writer = "%s %s" % (request.user.last_name , request.user.first_name)  # 系统自动添加创建人
        obj.save( )


class GenusResource( resources.ModelResource ):
    class Meta:
        model = Genus
        skip_unchanged = True
        fields = ('id' , 'taxid' , 'china_name' , 'english_name' , 'create_date' , 'historys' , 'writer' , 'note')
        export_order = ('id' , 'taxid' , 'china_name' , 'english_name' , 'create_date' , 'historys' , 'writer' , 'note')


@admin.register( Genus )
class GenusAdmin( ImportExportActionModelAdmin , admin.ModelAdmin ):
    list_display = ('id' , 'taxid' , 'china_name' , 'english_name' , 'create_date' , 'writer')
    list_display_links = ('taxid' ,)
    readonly_fields = ('historys' , 'writer')
    ordering = ('-create_date' ,)
    view_on_site = False
    list_max_show_all = 100
    list_per_page = 20
    # list_filter =
    search_fields = ('china_name' , 'english_name')
    resource_class = GenusResource

    # form = CarbonForm
    # list_editable =
    # actions =

    def get_changeform_initial_data(self , request):
        initial = super( ).get_changeform_initial_data( request )
        initial ['writer'] = request.user.last_name + ' ' + request.user.first_name
        return initial

    def save_model(self , request , obj , form , change):
        if obj.historys is None:
            obj.historys = "编号:" + str(
                obj.taxid ) + ";中文名称:" + obj.china_name + ";英文名称:" + obj.english_name + ";时间:" + datetime.date.today( ).__str__( )
        else:
            obj.historys = obj.historys + "\n" + "编号:" + str(
                obj.taxid ) + ";中文名称:" + obj.china_name + ";英文名称:" + obj.english_name + ";时间:" + datetime.date.today( ).__str__( )
        # obj.writer = "%s %s" % (request.user.last_name , request.user.first_name)  # 系统自动添加创建人
        obj.save( )


class ProductResource( resources.ModelResource ):
    class Meta:
        model = Product
        skip_unchanged = True
        fields = ('id' , 'number' , 'name' , 'price' , 'check_content' , 'create_date' , 'writer' , 'note')
        export_order = ('id' , 'number' , 'name' , 'price' , 'check_content' , 'create_date' , 'writer' , 'note')

    def get_diff_headers(self):
        return ['id' , '套餐编号' , '套餐名称' , '套餐价格' , '检测模块' , '创建时间' , '创建人' , '备注']

    def get_export_headers(self):
        return ['id' , '套餐编号' , '套餐名称' , '套餐价格' , '检测模块' , '创建时间' , '创建人' , '备注']

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
            tmp_list = [CheckItem.objects.get( number = cc ).check_name for cc in
                        re.split( '[；;]' , obj.check_content.strip( ) )]
            checkItem_check_name = ";".join( tmp_list )
            obj.check_content = checkItem_check_name
            data.append( self.export_resource( obj ) )
        self.after_export( queryset , data , *args , **kwargs )
        return data

    def before_import_row(self , row , **kwargs):
        """
        Calls :meth:`import_export.fields.Field.save` if ``Field.attribute``
        and ``Field.column_name`` are found in ``data``.
        """
        for cn in re.split( '[；;]' , row ['检测模块'].strip( ) ):
            if CheckItem.objects.filter( check_name = cn ).count( ) == 0:
                raise forms.ValidationError( '检测模块名称不对，请到基础数据管理中核实。' )
        products = Product.objects.filter( number = row ['套餐编号'] )  # 导入的表格中套餐编号列填写的是根据套餐编号
        if (row ['id'] is None) and (products.count( ) > 0):
            raise forms.ValidationError( "套餐编号有重复。" )

    def get_or_init_instance(self , instance_loader , row):
        """
        Either fetches an already existing instance or initializes a new one.
        """
        instance = self.get_instance( instance_loader , row )
        row ['number'] = row ['套餐编号']
        row ['name'] = row ['套餐名称']
        row ['price'] = row ['套餐价格']
        row ['check_content'] = row ['检测模块']
        row ['create_date'] = row ['创建时间']
        row ['writer'] = row ['创建人']
        row ['note'] = row ['备注']
        if instance:
            return instance , False
        else:
            return self.init_instance( row ) , True

    def before_save_instance(self , instance , using_transactions , dry_run):
        """
            Override to add additional logic. Does nothing by default.
        """
        tmp_list = [CheckItem.objects.get( check_name = cc ).number for cc in
                    re.split( '[；;]' , instance.check_content.strip( ) )]
        checkItem_check_name = ";".join( tmp_list )
        instance.check_content = checkItem_check_name


class ProductForm( forms.ModelForm ):
    check_content = forms.CharField( label = "检测模块" ,
                                     help_text = "不能为空，可填写多个模块，模块之间用;隔开。示例：JCMK0001;JCMK0002;JCMK0003;JCMK0004" ,
                                     required = True , widget = forms.TextInput(
            attrs = {'class': 'vTextField , form-control' , 'placeholder': "示例：JCMK0001;JCMK0002;JCMK0003"} ) ,
                                     error_messages = {'required': '这个字段是必填项。'} )

    class Meta:
        model = Product
        exclude = ("" ,)

    def clean_check_content(self , exclude=None):
        numbers = re.split( '[；;]' , self.cleaned_data ["check_content"].strip( ) )
        if len( numbers ) > 1:
            for number in numbers:
                if CheckItem.objects.filter( number = number ).count( ) == 0:
                    raise forms.ValidationError( number + "检测模块编号不存在,请到基础数据管理核查" )
        else:
            if CheckItem.objects.filter( number = numbers [0] ).count( ) == 0:
                raise forms.ValidationError( numbers [0] + "检测模块编号不存在" )
        return self.cleaned_data ["check_content"].strip( )


@admin.register( Product )
class ProductAdmin( ImportExportActionModelAdmin , admin.ModelAdmin ):
    list_display = ('number' , 'name' , 'price' , 'check_content' , 'create_date' , 'days')
    list_display_links = ('number' ,)
    readonly_fields = ('historys' ,)
    ordering = ('-create_date' ,)
    view_on_site = False
    list_max_show_all = 100
    list_per_page = 20
    # list_filter =
    search_fields = ("number" , 'name')
    resource_class = ProductResource
    form = ProductForm

    # list_editable =
    # actions =

    def get_changeform_initial_data(self , request):
        initial = super( ).get_changeform_initial_data( request )
        initial ['writer'] = request.user.last_name + ' ' + request.user.first_name
        return initial

    def save_model(self , request , obj , form , change):
        if obj.historys is None:
            obj.historys = "编号:" + obj.number + ";名称:" + obj.name + ";价格:" + str(
                obj.price ) + ";时间:" + datetime.date.today( ).__str__( )
        else:
            obj.historys = obj.historys + "\n" + "编号:" + obj.number + ";名称:" + obj.name + ";价格:" + str(
                obj.price ) + ";时间:" + datetime.date.today( ).__str__( )
        # obj.writer = "%s %s" % (request.user.last_name , request.user.first_name)  # 系统自动添加创建人
        obj.save( )


class CarbonResource( resources.ModelResource ):
    class Meta:
        model = Carbon
        skip_unchanged = True
        fields = ('id' , 'cid' , 'name' , 'ratio' , 'create_date' , 'writer' , 'note')
        export_order = ('id' , 'cid' , 'name' , 'ratio' , 'create_date' , 'writer' , 'note')


@admin.register( Carbon )
class CarbonAdmin( ImportExportActionModelAdmin , admin.ModelAdmin ):
    list_display = ('id' , 'cid' , 'name' , 'ratio' , 'create_date')
    list_display_links = ('cid' ,)
    readonly_fields = ('historys' ,)
    ordering = ('-create_date' ,)
    view_on_site = False
    list_max_show_all = 100
    list_per_page = 20
    # list_filter =
    search_fields = ('name' ,)
    resource_class = CarbonResource

    # form = CarbonForm
    # list_editable =
    # actions =

    def get_changeform_initial_data(self , request):
        initial = super( ).get_changeform_initial_data( request )
        initial ['writer'] = request.user.last_name + ' ' + request.user.first_name
        return initial

    def save_model(self , request , obj , form , change):
        if obj.historys is None:
            obj.historys = "编号:" + obj.cid + ";名称:" + obj.name + ";配比:" + obj.ratio + ";时间:" + datetime.date.today( ).__str__( )
        else:
            obj.historys = obj.historys + "\n" + "编号:" + obj.cid + ";名称:" + obj.name + ";配比:" + obj.ratio + ";时间:" + datetime.date.today( ).__str__( )
        # obj.writer = "%s %s" % (request.user.last_name , request.user.first_name)  # 系统自动添加创建人
        obj.save( )


def SciNotation(num , point):
    if num == 0:
        return 0
    else:
        rule = "{0:.%se}" % point
        x = rule.format( num )
        x = x.split( 'e' )
        if (x [1]) [0] == "-":
            if (x [1] [1:]) == "00":
                return x [0] + "x10^(" + (x [1]) [0] + "0)"
            else:
                return x [0] + "x10^(" + (x [1]) [0] + (x [1] [1:]).lstrip( '0' ) + ")"
        else:
            if (x [1] [1:]) == "00":
                return x [0] + "x10^0"
            else:
                return x [0] + "x10^" + (x [1]) [1:].lstrip( '0' )


def get_reference_range(min_value , max_value , layout , point):
    """
    :param min_value: 调用函数前判断有值
    :param max_value: 
    :param layout: 
    :param point: 
    :return: 
    (0 , '数值') ,
    (1 , '科学记数法') ,
    (2 , '百分数') ,
    (3 , '阴阳') ,
    """
    if layout == 0:
        rule = "{0:.%sf}" % point
        reference_range = "%s~%s" % (rule.format( min_value ) , rule.format( max_value ))
    elif layout == 1:
        reference_range = '%s~%s' % (SciNotation( min_value , point ) , SciNotation( max_value , point ))
    elif layout == 2:
        rule = f'.{point}%'
        reference_range = "%s~%s" % (format( min_value , rule ) , format( max_value , rule ))
    else:
        if (min_value == 1) and (max_value == 1):
            reference_range = "阳性（+）"
        elif (min_value == 0) and (max_value == 0):
            reference_range = "阴性（-）"
        else:
            reference_range = ""

    return reference_range


class ReferenceRangeForm( forms.ModelForm ):
    tax_name = forms.CharField( label = "菌种" , help_text = "与基础数据管理菌种信息名称保持一致,填入英文名称" ,
                                required = True , widget = forms.TextInput(
            attrs = {'class': 'vTextField , form-control' , 'placeholder': '与基础数据管理的菌种信息名称保持一致,填入英文名称'} ) ,
                                error_messages = {'required': '这个字段是必填项,输入菌种英文名称。'} )

    class Meta:
        model = ReferenceRange
        exclude = ("" ,)

    def clean_tax_name(self):
        if Genus.objects.filter( english_name = self.cleaned_data ["tax_name"] ).count( ) == 0:
            raise forms.ValidationError( "菌种名称在基础数据管理中无法查询到" )
        return self.cleaned_data ["tax_name"]


class ReferenceRangeResource( resources.ModelResource ):
    class Meta:
        model = ReferenceRange
        skip_unchanged = True
        fields = (
            'id' , 'index_name' , 'carbon_source' , 'tax_name' , 'version_num' , 'max_value' , 'min_value' , 'point' ,
            'layout' , 'reference_range' , 'create_date' , 'writer' , 'note')
        export_order = (
            'id' , 'index_name' , 'carbon_source' , 'tax_name' , 'version_num' , 'max_value' , 'min_value' , 'point' ,
            'layout' , 'reference_range' , 'create_date' , 'writer' , 'note')

    def get_diff_headers(self):
        return ['id' , '指标名称' , '碳源' , '菌种名称' , '版本号' , '最大值' , '最小值' , '小数点位数' , '报告显示形式' , '参考值' ,
                '创建时间' , '创建人' , '备注']

    def get_export_headers(self):
        return ['id' , '指标名称' , '碳源' , '菌种名称' , '版本号' , '最大值' , '最小值' , '小数点位数' , '报告显示形式' , '参考值' ,
                '创建时间' , '创建人' , '备注']

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
            cs = Carbon.objects.get( id = obj.carbon_source.id )  # 导出的表格中渠道来源列填写的是根据渠道编号
            obj.carbon_source.id = cs.name
            data.append( self.export_resource( obj ) )
        self.after_export( queryset , data , *args , **kwargs )
        return data

    def before_import_row(self , row , **kwargs):
        """
        Calls :meth:`import_export.fields.Field.save` if ``Field.attribute``
        and ``Field.column_name`` are found in ``data``.
        """
        carbons = Carbon.objects.filter( name = row ['碳源'] )
        genuss = Genus.objects.filter( english_name = row ['菌种名称'] )
        if carbons.count( ) == 0:
            raise forms.ValidationError( '碳源名称有误，请到基础数据中核实。' )
        if genuss.count( ) == 0:
            raise forms.ValidationError( '菌属名称有误，请到基础数据中核实。' )
        if (row ['id'] is None) and (
                ReferenceRange.objects.filter( index_name = row ['指标名称'] , carbon_source = carbons [0].id ,
                                               tax_name = row ['菌种名称'] ,
                                               version_num = row ['版本号'] ).count( ) > 0):
            raise forms.ValidationError( '名称、碳源、菌种,版本，记录内容联合唯一，不能有冲突。' )

    def get_or_init_instance(self , instance_loader , row):
        """
        Either fetches an already existing instance or initializes a new one.
        """
        carbons = Carbon.objects.get( name = row ['碳源'] )
        instance = self.get_instance( instance_loader , row )
        row ['index_name'] = row ['指标名称']
        row ['carbon_source'] = carbons.id  # 转换为对象的ID进行导入
        row ['tax_name'] = row ['菌种名称']
        row ['version_num'] = row ['版本号']
        row ['max_value'] = row ['最大值']
        row ['min_value'] = row ['最小值']
        row ['point'] = row ['小数点位数']
        row ['layout'] = row ['报告显示形式']
        row ['reference_range'] = get_reference_range( row ['最小值'] , row ['最大值'] , row ['报告显示形式'] , row ['小数点位数'] )
        row ['create_date'] = row ['创建时间']
        row ['writer'] = row ['创建人']
        row ['note'] = row ['备注']
        if instance:
            return instance , False
        else:
            return self.init_instance( row ) , True

    def before_save_instance(self , instance , using_transactions , dry_run):
        """
            Override to add additional logic. Does nothing by default.
        """
        cs = Carbon.objects.get( id = instance.carbon_source.id )  # 导入的表格中渠道来源列填写的是根据渠道编号
        instance.carbon_source = cs


@admin.register( ReferenceRange )
class ReferenceRangeAdmin( ImportExportActionModelAdmin , admin.ModelAdmin ):
    list_display = (
        'index_name' , 'carbon_source' , 'tax_names' , 'version_num' , 'reference_range' , 'max_value' , 'min_value' ,
        'create_date' , 'writer')
    list_display_links = ('index_name' ,)
    readonly_fields = ('historys' , 'writer' , 'reference_range')
    ordering = ('-create_date' ,)
    view_on_site = False
    list_max_show_all = 100
    list_per_page = 20
    list_filter = ['carbon_source' , 'tax_name' , ]
    search_fields = ('index_name' ,)
    resource_class = ReferenceRangeResource
    form = ReferenceRangeForm
    # list_editable =
    # actions =
    fieldsets = (
        ('基本信息' , {
            'fields': ('index_name' , 'carbon_source' , 'tax_name' , 'version_num' , 'max_value' , 'min_value')
        }) ,
        ('参考范围' , {
            'fields': ('point' , 'layout' , 'reference_range') ,
        }) ,
        ('历史版本' , {
            'fields': ('historys' , 'writer' , 'note') ,
        }) ,
    )

    def tax_names(self , obj):
        return Genus.objects.get( english_name = obj.tax_name ).china_name

    tax_names.short_description = '菌种'

    def get_changeform_initial_data(self , request):
        initial = super( ).get_changeform_initial_data( request )
        initial ['writer'] = request.user.last_name + ' ' + request.user.first_name
        return initial

    def save_model(self , request , obj , form , change):
        if obj.historys is None:
            obj.historys = "编号:" + obj.index_name + ";碳源:" + obj.carbon_source.name + ";菌种:" + obj.tax_name + ";最小:" + str(
                obj.min_value ) + ";最大:" + str( obj.max_value ) + ";时间:" + datetime.date.today( ).__str__( )
        else:
            obj.historys = obj.historys + "\n" + "编号:" + obj.index_name + ";碳源:" + obj.carbon_source.name + ";菌种:" + obj.tax_name + ";最小:" + str(
                obj.min_value ) + ";最大:" + str( obj.max_value ) + ";时间:" + datetime.date.today( ).__str__( )
        # obj.writer = "%s %s" % (request.user.last_name , request.user.first_name)  # 系统自动添加创建人
        if (obj.max_value is not None) and (obj.min_value is not None):
            obj.reference_range = get_reference_range( obj.min_value , obj.max_value , obj.layout , obj.point )
        obj.save( )


class TemplateForm( forms.ModelForm ):
    class Meta:
        model = Template
        exclude = ("" ,)

    def clean_file_template(self):
        ext = self.cleaned_data ["file_template"]._name.split( '.' ) [-1].lower( )
        if ext not in ['doc' , 'docx' , 'xlsx' , 'xls' , 'txt']:
            raise forms.ValidationError( "只能上传doc,docx后缀的word文档" )
        return self.cleaned_data ["file_template"]


class TemplateResource( resources.ModelResource ):
    class Meta:
        model = Template
        skip_unchanged = True
        fields = (
            'id' , 'product_name' , 'version_num' , 'upload_time' , 'use_count' , 'file_template' , 'create_date' ,
            'writer' , 'note')
        export_order = (
            'id' , 'product_name' , 'version_num' , 'upload_time' , 'use_count' , 'file_template' , 'create_date' ,
            'writer' , 'note')


@admin.register( Template )
class TemplateAdmin( ImportExportActionModelAdmin , admin.ModelAdmin ):
    list_display = ('product_name' , 'version_num' , 'upload_time' , 'use_count' , 'file_template' , 'create_date')
    list_display_links = ('product_name' ,)
    readonly_fields = ('historys' , 'use_count')
    ordering = ('-create_date' ,)
    view_on_site = False
    list_max_show_all = 100
    list_per_page = 20
    # list_filter=
    search_fields = ("product_name" ,)
    resource_class = TemplateResource
    form = TemplateForm

    # list_editable =
    # actions =

    # form = CarbonForm
    def get_changeform_initial_data(self , request):
        initial = super( ).get_changeform_initial_data( request )
        initial ['writer'] = request.user.last_name + ' ' + request.user.first_name
        return initial

    def save_model(self , request , obj , form , change):
        if obj.historys is None:
            obj.historys = "编号:" + obj.product_name + ";版本:" + str( obj.version_num ) + ";模板:" + str(
                obj.file_template ) + ";时间:" + datetime.date.today( ).__str__( )
        else:
            obj.historys = obj.historys + "\n" + "编号:" + obj.product_name + ";版本:" + str(
                obj.version_num ) + ";模板:" + str(
                obj.file_template ) + ";时间:" + datetime.date.today( ).__str__( )
        # obj.writer = "%s %s" % (request.user.last_name , request.user.first_name)  # 系统自动添加创建人
        obj.save( )


class CheckTypeResource( resources.ModelResource ):
    class Meta:
        model = CheckType
        skip_unchanged = True
        fields = ('id' , 'number' , 'name' , 'note' , 'create_date' , 'writer' , 'note')
        export_order = ('id' , 'number' , 'name' , 'note' , 'create_date' , 'writer' , 'note')


@admin.register( CheckType )
class CheckTypeAdmin( ImportExportActionModelAdmin , admin.ModelAdmin ):
    list_display = ('id' , 'number' , 'name' , 'create_date')
    list_display_links = ('number' , 'name' ,)
    readonly_fields = ('historys' ,)
    ordering = ('-create_date' ,)
    view_on_site = False
    list_max_show_all = 100
    list_per_page = 20
    # list_filter =
    search_fields = ('name' ,)
    resource_class = CheckTypeResource

    # form = CheckTypeForm

    # list_editable =
    # actions =

    def get_changeform_initial_data(self , request):
        initial = super( ).get_changeform_initial_data( request )
        initial ['writer'] = request.user.last_name + ' ' + request.user.first_name
        return initial

    def save_model(self , request , obj , form , change):
        if obj.historys is None:
            obj.historys = "检测编号:" + obj.number + ":检测大类:" + obj.name + ";时间:" + datetime.date.today( ).__str__( )
        else:
            obj.historys = obj.historys + "\n" + "检测编号:" + obj.number + ":检测大类:" + obj.name + ";时间:" + datetime.date.today( ).__str__( )
        # obj.writer = "%s %s" % (request.user.last_name , request.user.first_name)  # 系统自动添加创建人
        obj.save( )


class CheckItemForm( forms.ModelForm ):
    carbon_source = forms.CharField( label = "碳源" ,
                                     help_text = "不能为空，可填写多个碳源，碳源之间用;隔开。示例：TY0001;TY0002;TY0003;TY0004" ,
                                     required = True , widget = forms.TextInput(
            attrs = {'class': 'vTextField , form-control' , 'placeholder': "示例：TY0001;TY0002;TY0003"} ) ,
                                     error_messages = {'required': '这个字段是必填项。'} )

    genus = forms.CharField( label = "菌种" , help_text = "不能为空。输入与基础数据菌种信息名称保持的英文菌名，" ,
                             required = True , widget = forms.TextInput(
            attrs = {'class': 'vTextField , form-control' , 'placeholder': '示例：lactobacillus,字母大小写保持一致'} ) ,
                             error_messages = {'required': '这个字段是必填项。'} )

    class Meta:
        model = CheckItem
        exclude = ("" ,)

    def clean_carbon_source(self):
        numbers = re.split( '[；;]' , self.cleaned_data ["carbon_source"].strip( ) )
        if len( numbers ) > 1:
            for number in numbers:
                if Carbon.objects.filter( cid = number ).count( ) == 0:
                    raise forms.ValidationError( number + "碳源编号不存在,请到基础数据管理核查" )
        else:
            if Carbon.objects.filter( cid = numbers [0] ).count( ) == 0:
                raise forms.ValidationError( numbers [0] + "碳源编号不存在" )
        return self.cleaned_data ["carbon_source"].strip( )

    def clean_genus(self):
        if Genus.objects.filter( english_name = self.cleaned_data ["genus"] ).count( ) == 0:
            raise forms.ValidationError( "菌属名称在数据库中无法查询到" )
        return self.cleaned_data ["genus"]


class CheckItemResource( resources.ModelResource ):
    class Meta:
        model = CheckItem
        skip_unchanged = True
        fields = (
            'id' , 'number' , 'check_name' , 'type' , 'carbon_source' , 'genus' , 'create_date' ,
            'writer' ,
            'note')
        export_order = (
            'id' , 'number' , 'check_name' , 'type' , 'carbon_source' , 'genus' , 'create_date' ,
            'writer' ,
            'note')

    def get_diff_headers(self):
        return ['id' , '检测模块编号' , '检测模块名称' , '检测大类' , '碳源' , '菌种' , '创建时间' , '创建人' , '备注']

    def get_export_headers(self):
        return ['id' , '检测模块编号' , '检测模块名称' , '检测大类' , '碳源' , '菌种' , '创建时间' , '创建人' , '备注']

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
            checkType = CheckType.objects.get( id = obj.type.id )  # 导出的表格中渠道来源列填写的是根据渠道编号
            obj.type.id = checkType.name  # 继承框架函数，增加以上2行代码
            tmp_list = [Carbon.objects.get( cid = cb ).name for cb in
                        re.split( '[；;]' , obj.carbon_source.strip( ) )]
            carbon_source = ";".join( tmp_list )
            obj.carbon_source = carbon_source
            data.append( self.export_resource( obj ) )
        self.after_export( queryset , data , *args , **kwargs )
        return data

    def before_import_row(self , row , **kwargs):
        """
        Calls :meth:`import_export.fields.Field.save` if ``Field.attribute``
        and ``Field.column_name`` are found in ``data``.
        """
        checkitems = CheckItem.objects.filter( number = row ['检测模块编号'] )
        checkitems_name = CheckItem.objects.filter( check_name = row ['检测模块名称'] )
        checktypes = CheckType.objects.filter( name = row ['检测大类'] )
        genuss = Genus.objects.filter( english_name = row ['菌种'] )  # 导入的表格中菌种列填写的是根据套餐编号
        if (row ['id'] is None) and (checkitems.count( ) > 0):
            raise forms.ValidationError( "检测模块编号有重复。" )
        if (row ['id'] is None) and (checkitems_name.count( ) > 0):
            raise forms.ValidationError( "检测模块名称有重复。" )
        if checktypes.count( ) == 0:
            raise forms.ValidationError( '检测大类有误，请到基础数据管理中核实。' )
        for cn in re.split( '[；;]' , row ['碳源'].strip( ) ):
            if Carbon.objects.filter( name = cn ).count( ) == 0:
                raise forms.ValidationError( '碳源有误，请到基础数据管理中核实。' )
        if genuss.count( ) == 0:
            raise forms.ValidationError( '菌属名称有误，请到基础数据管理中核实。' )

    def get_or_init_instance(self , instance_loader , row):
        """
        Either fetches an already existing instance or initializes a new one.
        """
        checktype = CheckType.objects.get( name = row ['检测大类'] )
        instance = self.get_instance( instance_loader , row )
        row ['number'] = row ['检测模块编号']
        row ['check_name'] = row ['检测模块名称']
        row ['type'] = checktype.id  # 转换为对象的ID进行导入
        row ['carbon_source'] = row ['碳源']
        row ['genus'] = row ['菌种']
        row ['create_date'] = row ['创建时间']
        row ['writer'] = row ['创建人']
        row ['note'] = row ['备注']
        if instance:
            return instance , False
        else:
            return self.init_instance( row ) , True

    def before_save_instance(self , instance , using_transactions , dry_run):
        """
            Override to add additional logic. Does nothing by default.
        """
        tmp_list = [Carbon.objects.get( name = cb ).cid for cb in
                    re.split( '[；;]' , instance.carbon_source.strip( ) )]
        carbon_source = ";".join( tmp_list )
        instance.carbon_source = carbon_source


@admin.register( CheckItem )
class CheckItemAdmin( ImportExportActionModelAdmin , admin.ModelAdmin ):
    list_display = ('id' , 'number' , 'check_name' , 'type' , 'carbon_source' , 'genus' , 'create_date')
    list_display_links = ('check_name' , 'number')
    readonly_fields = ('historys' ,)
    ordering = ('-create_date' ,)
    view_on_site = False
    list_max_show_all = 100
    list_per_page = 20
    list_filter = ['type' , ]
    search_fields = ('check_name' , 'number')
    resource_class = CheckItemResource

    form = CheckItemForm

    # list_editable =
    # actions =

    def get_changeform_initial_data(self , request):
        initial = super( ).get_changeform_initial_data( request )
        initial ['writer'] = request.user.last_name + ' ' + request.user.first_name
        return initial

    def save_model(self , request , obj , form , change):
        if obj.historys is None:
            obj.historys = "检测编号:" + obj.number + ":检测名称:" + obj.check_name + ";时间:" + datetime.date.today( ).__str__( )
        else:
            obj.historys = obj.historys + "\n" + "检测编号:" + obj.number + ":检测名称:" + obj.check_name + ";时间:" + datetime.date.today( ).__str__( )
        # obj.writer = "%s %s" % (request.user.last_name , request.user.first_name)  # 系统自动添加创建人
        obj.save( )


class AgeResource( resources.ModelResource ):
    class Meta:
        model = Age
        skip_unchanged = True
        fields = ('id' , 'name' , 'age_range' , 'create_date' , 'writer' , 'note')
        export_order = ('id' , 'name' , 'age_range' , 'create_date' , 'writer' , 'note')


@admin.register( Age )
class AgeAdmin( ImportExportActionModelAdmin , admin.ModelAdmin ):
    list_display = ('id' , 'name' , "age_range" , "create_date")
    list_display_links = ('name' ,)
    readonly_fields = ('historys' ,)
    ordering = ('-create_date' ,)
    view_on_site = False
    list_max_show_all = 100
    list_per_page = 20
    # list_filter =
    search_fields = ('name' ,)
    resource_class = AgeResource

    # form = AgeForm
    # list_editable =
    # actions =

    def get_changeform_initial_data(self , request):
        initial = super( ).get_changeform_initial_data( request )
        initial ['writer'] = request.user.last_name + ' ' + request.user.first_name
        return initial

    def save_model(self , request , obj , form , change):
        if obj.historys is None:
            obj.historys = "年龄分段:" + obj.name + ":年龄范围:" + obj.age_range + ";时间:" + datetime.date.today( ).__str__( )
        else:
            obj.historys = obj.historys + "\n" + "年龄分段:" + obj.name + ":年龄范围:" + obj.age_range + ";时间:" + datetime.date.today( ).__str__( )
        # obj.writer = "%s %s" % (request.user.last_name , request.user.first_name)  # 系统自动添加创建人
        obj.save( )


class ProvinceResource( resources.ModelResource ):
    class Meta:
        model = Province
        skip_unchanged = True
        fields = ('id' , 'name' , 'create_date' , 'writer' , 'note')
        export_order = ('id' , 'name' , 'create_date' , 'writer' , 'note')


@admin.register( Province )
class ProvinceAdmin( ImportExportActionModelAdmin , admin.ModelAdmin ):
    list_display = ('id' , 'name' , "create_date")
    list_display_links = ('name' ,)
    readonly_fields = ('historys' ,)
    ordering = ('-create_date' ,)
    view_on_site = False
    list_max_show_all = 100
    list_per_page = 20
    # list_filter =
    search_fields = ('name' ,)
    resource_class = ProvinceResource

    # form = CheckItemForm
    # list_editable =
    # actions =

    def get_changeform_initial_data(self , request):
        initial = super( ).get_changeform_initial_data( request )
        initial ['writer'] = request.user.last_name + ' ' + request.user.first_name
        return initial

    def save_model(self , request , obj , form , change):
        if obj.historys is None:
            obj.historys = "地域:" + obj.name + ";时间:" + datetime.date.today( ).__str__( )
        else:
            obj.historys = obj.historys + "\n" + "地域:" + obj.name + ";时间:" + datetime.date.today( ).__str__( )
        # obj.writer = "%s %s" % (request.user.last_name , request.user.first_name)  # 系统自动添加创建人
        obj.save( )


class RiskReferenceRangeForm( forms.ModelForm ):
    reference_range1 = forms.CharField( label = "低风险参考值" ,
                                        help_text = "不能为空，可填写多个参考范围，之间用;隔开。示例：1~3;5~7" ,
                                        required = True , widget = forms.TextInput(
            attrs = {'class': 'vTextField , form-control' , 'placeholder': "示例：1~3;5~7"} ) ,
                                        error_messages = {'required': '这个字段是必填项。'} )
    reference_range2 = forms.CharField( label = "注意参考值" ,
                                        help_text = "不能为空，可填写多个参考范围，之间用;隔开。示例：1~3;5~7" ,
                                        required = True , widget = forms.TextInput(
            attrs = {'class': 'vTextField , form-control' , 'placeholder': "示例：1~3;5~7"} ) ,
                                        error_messages = {'required': '这个字段是必填项。'} )
    reference_range3 = forms.CharField( label = "中风险参考值" ,
                                        help_text = "不能为空，可填写多个参考范围，之间用;隔开。示例：1~3;5~7" ,
                                        required = True , widget = forms.TextInput(
            attrs = {'class': 'vTextField , form-control' , 'placeholder': "示例：1~3;5~7"} ) ,
                                        error_messages = {'required': '这个字段是必填项。'} )
    reference_range4 = forms.CharField( label = "高风险参考值" ,
                                        help_text = "不能为空，可填写多个参考范围，之间用;隔开。示例：1~3;5~7" ,
                                        required = True , widget = forms.TextInput(
            attrs = {'class': 'vTextField , form-control' , 'placeholder': "示例：1~3;5~7"} ) ,
                                        error_messages = {'required': '这个字段是必填项。'} )

    class Meta:
        model = RiskReferenceRange
        exclude = ("" ,)

    def clean_reference_range1(self):
        numbers = re.split( '[；;]' , self.cleaned_data ["reference_range1"].strip( ) )
        if len( numbers ) > 0:
            for number in numbers:
                if not re.match( r'-?\d?\.?\d+~\d?\.?\d+' , number ):
                    raise forms.ValidationError( "没有破折号~" )
        else:
            raise forms.ValidationError( "风险参考范围不存在" )
        return self.cleaned_data ["reference_range1"]

    def clean_reference_range2(self):
        numbers = re.split( '[；;]' , self.cleaned_data ["reference_range2"].strip( ) )
        if len( numbers ) > 0:
            for number in numbers:
                if not re.match( r'-?\d?\.?\d+~\d?\.?\d+' , number ):
                    raise forms.ValidationError( "没有破折号~" )
        else:
            raise forms.ValidationError( "风险参考范围不存在" )
        return self.cleaned_data ["reference_range2"]

    def clean_reference_range3(self):
        numbers = re.split( '[；;]' , self.cleaned_data ["reference_range3"].strip( ) )
        if len( numbers ) > 0:
            for number in numbers:
                if not re.match( r'-?\d?\.?\d+~\d?\.?\d+' , number ):
                    raise forms.ValidationError( "没有破折号~" )
        else:
            raise forms.ValidationError( "风险参考范围不存在" )
        return self.cleaned_data ["reference_range3"]

    def clean_reference_range4(self):
        numbers = re.split( '[；;]' , self.cleaned_data ["reference_range4"].strip( ) )
        if len( numbers ) > 0:
            for number in numbers:
                if not re.match( r'-?\d?\.?\d+~\d?\.?\d+' , number ):
                    raise forms.ValidationError( "没有破折号~" )
        else:
            raise forms.ValidationError( "风险参考范围不存在" )
        return self.cleaned_data ["reference_range4"]


@admin.register( RiskReferenceRange )
class RiskReferenceRangeAdmin( ImportExportActionModelAdmin , admin.ModelAdmin ):
    list_display = ('id' , 'index_name' , "create_date")
    list_display_links = ('index_name' ,)
    readonly_fields = ('historys' ,)
    ordering = ('-create_date' ,)
    view_on_site = False
    list_max_show_all = 100
    list_per_page = 20
    # list_filter =
    search_fields = ('index_name' ,)

    # resource_class = RiskReferenceRangeResource

    form = RiskReferenceRangeForm

    # list_editable =
    # actions =

    def get_changeform_initial_data(self , request):
        initial = super( ).get_changeform_initial_data( request )
        initial ['writer'] = request.user.last_name + ' ' + request.user.first_name
        return initial

    def save_model(self , request , obj , form , change):
        if obj.historys is None:
            obj.historys = "指标:" + obj.index_name + ";时间:" + datetime.date.today( ).__str__( )
        else:
            obj.historys = obj.historys + "\n" + "指标:" + obj.index_name + ";时间:" + datetime.date.today( ).__str__( )
        obj.save( )


@admin.register( RiskItem )
class RiskItemAdmin( ImportExportActionModelAdmin , admin.ModelAdmin ):
    list_display = (
        'id' , 'index_name' , 'risk_type' , 'risk_type_number' , 'check_type' , 'check_type_number' , "create_date")
    list_display_links = ('index_name' ,)
    readonly_fields = ('historys' ,)
    ordering = ('-create_date' ,)
    view_on_site = False
    list_max_show_all = 100
    list_per_page = 20
    # list_filter =
    search_fields = ('index_name' ,)

    # resource_class = ProvinceResource

    # form = CheckItemForm
    # list_editable =
    # actions =

    def get_changeform_initial_data(self , request):
        initial = super( ).get_changeform_initial_data( request )
        initial ['writer'] = request.user.last_name + ' ' + request.user.first_name
        return initial

    def save_model(self , request , obj , form , change):
        if obj.historys is None:
            obj.historys = "风险名称:" + obj.index_name + ";时间:" + datetime.date.today( ).__str__( )
        else:
            obj.historys = obj.historys + "\n" + "风险名称:" + obj.index_name + ";时间:" + datetime.date.today( ).__str__( )
        obj.save( )


@admin.register( RiskItemDefault )
class RiskItemDefaultAdmin( ImportExportActionModelAdmin , admin.ModelAdmin ):
    list_display = (
        'id' , 'index_name' , 'risk_type' , 'risk_type_number' , 'low_value' , 'high_value' ,
        "create_date")
    list_display_links = ('index_name' ,)
    readonly_fields = ('historys' ,)
    ordering = ('-create_date' ,)
    view_on_site = False
    list_max_show_all = 100
    list_per_page = 20
    # list_filter =
    search_fields = ('index_name' ,)

    # resource_class = ProvinceResource

    # form = CheckItemForm
    # list_editable =
    # actions =

    def get_changeform_initial_data(self , request):
        initial = super( ).get_changeform_initial_data( request )
        initial ['writer'] = request.user.last_name + ' ' + request.user.first_name
        return initial

    def save_model(self , request , obj , form , change):
        if obj.historys is None:
            obj.historys = "风险名称:" + obj.index_name + ";时间:" + datetime.date.today( ).__str__( )
        else:
            obj.historys = obj.historys + "\n" + "风险名称:" + obj.index_name + ";时间:" + datetime.date.today( ).__str__( )
        obj.save( )
