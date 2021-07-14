import datetime
from django import forms
from django.contrib import admin , messages
from import_export import resources
from import_export.admin import ImportExportActionModelAdmin
from import_export.formats import base_formats
from basicdata.models import Age , Carbon , Genus
from basicdata.models import Province
from examinationsample.models import Progress
from questionnairesurvey.models import Quenstion

admin.site.empty_value_display = '-empty-'


class QuenstionForm( forms.ModelForm ):
    age_sgement = forms.CharField( label = "年龄分段" , help_text = "不能为空。示例：青年" ,
                                   required = True , widget = forms.TextInput(
            attrs = {'class': 'vTextField , form-control' , 'placeholder': '示例：青年'} ) ,
                                   error_messages = {'required': '这个字段是必填项。'} )
    province = forms.CharField( label = "地域" , help_text = "不能为空。示例：江浙沪" ,
                                required = True , widget = forms.TextInput(
            attrs = {'class': 'vTextField , form-control' , 'placeholder': '示例：江浙沪'} ) ,
                                error_messages = {'required': '这个字段是必填项。'} )
    weight = forms.CharField( label = "体重" , help_text = "单位：千克" , required = True ,
                              widget = forms.NumberInput(
                                  attrs = {'class': ' form-control' , 'placeholder': '示例：60.01'} ) ,
                              error_messages = {'required': '单位：千克'} )
    height = forms.CharField( label = "身高" , help_text = "单位：米" , required = True ,
                              widget = forms.NumberInput(
                                  attrs = {'class': ' form-control' , 'placeholder': '示例：1.68'} ) ,
                              error_messages = {'required': '单位：米'} )

    class Meta:
        model = Quenstion
        exclude = ("" ,)

    def clean_age_sgement(self):
        if Age.objects.filter( name = self.cleaned_data ["age_sgement"] ).count( ) == 0:
            raise forms.ValidationError( "年龄段在数据库中无法查询到" )
        return self.cleaned_data ["age_sgement"]

    def clean_province(self):
        if Province.objects.filter( name = self.cleaned_data ["province"] ).count( ) == 0:
            raise forms.ValidationError( "地域在数据库中无法查询到" )
        return self.cleaned_data ["province"]


class QuenstionResource( resources.ModelResource ):
    class Meta:
        model = Quenstion
        skip_unchanged = True

        fields = (
            'id' , 'sample_number' , 'carbon_source' , 'genus' , 'carbon_source_zh' , 'genus_zh' , 'name' , 'gender' ,
            'age' , 'age_sgement' , 'province' , 'height' , 'weight' , 'waistline' , 'bmi_value' , 'phone' ,
            'email' , 'complaint' , 'condition' , 'exhaust' , 'classification' , 'unwell' , 'smoke' ,
            'antibiotic_consumption' , 'probiotic_supplements' , 'prebiotics_supplement' , 'dietary_habit' ,
            'allergen' , 'anamnesis' , 'triglyceride' , 'cholesterol' , 'hdl' , 'blood_glucose' , 'blood_pressure' ,
            'trioxypurine')
        export_order = (
            'id' , 'sample_number' , 'carbon_source' , 'genus' , 'carbon_source_zh' , 'genus_zh' , 'name' , 'gender' ,
            'age' , 'age_sgement' , 'province' , 'height' , 'weight' , 'waistline' , 'bmi_value' , 'phone' ,
            'email' , 'complaint' , 'condition' , 'exhaust' , 'classification' , 'unwell' , 'smoke' ,
            'antibiotic_consumption' , 'probiotic_supplements' , 'prebiotics_supplement' , 'dietary_habit' ,
            'allergen' , 'anamnesis' , 'triglyceride' , 'cholesterol' , 'hdl' , 'blood_glucose' , 'blood_pressure' ,
            'trioxypurine')

    def get_diff_headers(self):
        return ['id' , '样本编号' , '碳源' , '菌种' , '碳源中文名称' , '菌种中文名称' , '姓名' , '性别' , '年龄' , '年龄分段' , '地域' , '身高' , '体重' ,
                '腰围' , 'BMI值' , '电话' , "邮箱" , '主诉' , '近1个月排便情况' , '近1个月大便频次' , '自评布里斯托分级' , '近1个月胃肠道不适症状' , '吸烟饮酒' ,
                '近1个月抗生素食用' , '近两周益生菌补充' , '近两周益生元补充' , '饮食习惯' , '过敏源' , '既往病史' , '甘油三酯' , '总胆固醇' , 'HDL-C' , '餐后血糖' ,
                '血压' , '尿酸']

    def get_export_headers(self):
        return ['id' , '样本编号' , '碳源' , '菌种' , '碳源中文名称' , '菌种中文名称' , '姓名' , '性别' , '年龄' , '年龄分段' , '地域' , '身高' , '体重' ,
                '腰围' , 'BMI值' , '电话' , "邮箱" , '主诉' , '近1个月排便情况' , '近1个月大便频次' , '自评布里斯托分级' , '近1个月胃肠道不适症状' , '吸烟饮酒' ,
                '近1个月抗生素食用' , '近两周益生菌补充' , '近两周益生元补充' , '饮食习惯' , '过敏源' , '既往病史' , '甘油三酯' , '总胆固醇' , 'HDL-C' , '餐后血糖' ,
                '血压' , '尿酸']

    def before_import_row(self , row , **kwargs):
        """
        Calls :meth:`import_export.fields.Field.save` if ``Field.attribute``
        and ``Field.column_name`` are found in ``data``.
        """
        carbons = Carbon.objects.filter( id = row ['碳源'] )
        genuss = Genus.objects.filter( id = row ['菌种'] )
        if carbons.count( ) == 0:
            raise forms.ValidationError( '碳源名称有误，请到基础数据中核实。' )
        if genuss.count( ) == 0:
            raise forms.ValidationError( '菌属名称有误，请到基础数据中核实。' )
        if (row ['id'] is None) and (    # TODO 样本编号已经设置唯一，联合唯一有待删除
                Quenstion.objects.filter( sample_number = row ['样本编号'] , carbon_source = row ['碳源'] ,
                                          genus = row ['菌种'] ).count( ) > 0):
            raise forms.ValidationError( '样本编号、碳源、菌种 记录内容联合唯一，不能有冲突。' )
        if Age.objects.filter( name = row ["年龄分段"] ).count( ) == 0:
            raise forms.ValidationError( "年龄段在数据库中无法查询到" )
        if Province.objects.filter( name = row ["地域"] ).count( ) == 0:
            raise forms.ValidationError( "地域在数据库中无法查询到" )

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
        row ['name'] = row ['姓名']
        row ['gender'] = row ['性别']
        row ['age'] = row ['年龄']
        row ['age_sgement'] = row ['年龄分段']
        row ['province'] = row ['地域']
        row ['height'] = row ['身高']
        row ['weight'] = row ['体重']
        row ['waistline'] = row ['腰围']
        row ['bmi_value'] = row ['BMI值']
        row ['phone'] = row ['电话']
        row ['email'] = row ['邮箱']
        row ['complaint'] = row ['主诉']
        row ['condition'] = row ['近1个月排便情况']
        row ['exhaust'] = row ['近1个月大便频次']
        row ['classification'] = row ['自评布里斯托分级']
        row ['unwell'] = row ['近1个月胃肠道不适症状']
        row ['smoke'] = row ['吸烟饮酒']
        row ['antibiotic_consumption'] = row ['近1个月抗生素食用']
        row ['probiotic_supplements'] = row ['近两周益生菌补充']
        row ['prebiotics_supplement'] = row ['近两周益生元补充']
        row ['dietary_habit'] = row ['饮食习惯']
        row ['allergen'] = row ['过敏源']
        row ['anamnesis'] = row ['既往病史']
        row ['triglyceride'] = row ['甘油三酯']
        row ['cholesterol'] = row ['总胆固醇']
        row ['hdl'] = row ['HDL-C']
        row ['blood_glucose'] = row ['餐后血糖']
        row ['blood_pressure'] = row ['血压']
        row ['trioxypurine'] = row ['尿酸']
        if instance:
            return instance , False
        else:
            return self.init_instance( row ) , True


@admin.register( Quenstion )
class QuenstionIndexesAdmin( ImportExportActionModelAdmin , admin.ModelAdmin ):
    list_display = ('sample_number' , 'name' , 'gender' , 'age' , 'bmi_value' , 'phone' , 'email' , 'is_status')
    list_display_links = ('sample_number' ,)
    # readonly_fields =
    ordering = ('-sample_number' ,)
    view_on_site = False
    list_max_show_all = 100
    list_per_page = 20
    list_filter = ('gender' , 'age_sgement' , 'province')
    search_fields = ('sample_number' , 'name')
    resource_class = QuenstionResource
    form = QuenstionForm
    # list_editable =
    actions = ['make_finish' , 'export_admin_action']

    fieldsets = (
        ('基本信息' , {
            'fields': (('sample_number' , 'carbon_source' , 'genus' ,) ,
                       ('name' , 'gender' , 'age') ,
                       ('age_sgement' , 'province' ,) ,
                       ('height' , 'weight' , 'waistline' , 'bmi_value' ,) ,
                       ('phone' , 'email' ,) ,)
        }) ,
        ('生活习惯' , {
            'fields': (('complaint' , 'condition' ,) ,
                       ('classification' , 'unwell' ,) ,
                       ('exhaust' , 'smoke' ,))
        }) ,
        ('疾病' , {
            'fields': (('antibiotic_consumption' , 'probiotic_supplements') ,
                       ('prebiotics_supplement' , 'dietary_habit' ,) ,
                       ('allergen' , 'anamnesis' ,) ,
                       ('triglyceride' , 'cholesterol' ,) ,
                       ('hdl' , 'blood_glucose' , 'trioxypurine'))
        })
    )

    def get_readonly_fields(self , request , obj=None):
        # 根据 obj 是否为空来判断,修改数据时不能修改样本编号，
        if obj:
            self.readonly_fields = ('sample_number' , 'carbon_source' , 'genus' , 'bmi_value')
        else:
            self.readonly_fields = ('bmi_value' ,)
        # if request.user.is_superuser:  # TODO 上线时打开
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
                if obj_progress.is_wjxx:  # 条件：未标记完成，同时需要检测该项内容
                    obj_progress.wjxx_testing_date = datetime.date.today( )
                    obj_progress.wjxx_testing_staff = request.user.last_name + ' ' + request.user.first_name
                    obj_progress.save( )
                    obj.is_status = 1  # 1是标记为完成的
                    obj.save( )
                    i += 1
                else:
                    n += 1
            else:
                n += 1
        self.message_user( request , "选择%s条信息，完成操作%s条，不操作%s条" % (t , i , n) , level = messages.SUCCESS )

    make_finish.short_description = "1标记完成"

    def save_model(self , request , obj , form , change):
        if (obj.height is not None) and (obj.weight is not None):
            if (obj.height > 0) and (obj.weight > 0):
                obj.bmi_value = float( obj.weight ) / (float( obj.height ) * float( obj.height ))
        else:
            self.message_user( request , "BMI值无法计算，请先填写体重和身高的数据" , level = messages.ERROR )
        obj.save( )
