import datetime
from django import forms
from django.contrib import admin , messages
from import_export import resources
from import_export.admin import ImportExportActionModelAdmin
from import_export.formats import base_formats
from basicdata.models import Age
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
    weight = forms.CharField( label = "体重" , help_text = "单位：千克" ,required = True ,
                                 widget = forms.NumberInput(
            attrs = {'class': ' form-control' , 'placeholder': '示例：60.01'} ) ,
                                error_messages = {'required': '单位：千克'} )
    height = forms.CharField( label = "身高" , help_text = "单位：米" ,required = True ,
                              widget = forms.NumberInput(
                                  attrs = {'class': ' form-control' , 'placeholder': '示例：1.68'} ) ,
                              error_messages = {'required': '单位：米'} )
    class Meta:
        model = Quenstion
        exclude = ("" ,)

    def clean_age_sgement(self , exclude=None):
        if Age.objects.filter( name = self.cleaned_data ["age_sgement"] ).count( ) == 0:
            raise forms.ValidationError( "年龄段在数据库中无法查询到" )
        return self.cleaned_data ["age_sgement"]

    def clean_province(self , exclude=None):
        if Province.objects.filter( name = self.cleaned_data ["province"] ).count( ) == 0:
            raise forms.ValidationError( "地域在数据库中无法查询到" )
        return self.cleaned_data ["province"]


class QuenstionResource( resources.ModelResource ):
    class Meta:
        model = Quenstion
        skip_unchanged = True

        fields = (
            'id' , 'sample_number' ,'carbon_source' ,'genus', 'name' , 'gender' , 'age' , 'height' , 'weight' ,
            'waistline' , 'bmi_value' , 'phone' , 'email' , 'complaint' , 'condition' , 'exhaust' , 'smoke' ,
            'antibiotic_consumption' , 'probiotic_supplements' ,
            'prebiotics_supplement' , 'dietary_habit' , 'allergen' , 'anamnesis' , 'triglyceride' , 'cholesterol' ,
            'hdl' , 'blood_glucose' , 'trioxypurine' , 'is_status')
        export_order = (
            'id' , 'sample_number' ,'carbon_source' ,'genus', 'name' , 'gender' , 'age' , 'height' , 'weight' ,
            'waistline' , 'bmi_value' , 'phone' , 'email' , 'complaint' , 'condition' , 'exhaust' , 'smoke' ,
            'antibiotic_consumption' , 'probiotic_supplements' ,
            'prebiotics_supplement' , 'dietary_habit' , 'allergen' , 'anamnesis' , 'triglyceride' , 'cholesterol' ,
            'hdl' , 'blood_glucose' , 'trioxypurine' , 'is_status')


@admin.register( Quenstion )
class QuenstionIndexesAdmin( ImportExportActionModelAdmin , admin.ModelAdmin ):
    list_display = ('sample_number' , 'name' , 'gender' , 'age' , 'height' , 'weight' ,
                    'waistline' , 'bmi_value' , 'phone' , 'email' , 'is_status')
    list_display_links = ('sample_number' ,)
    # readonly_fields =
    ordering = ('-sample_number' ,)
    view_on_site = False
    list_max_show_all = 100
    list_per_page = 20
    list_filter = ('gender' ,)
    search_fields = ('sample_number' ,)
    resource_class = QuenstionResource
    form = QuenstionForm
    # list_editable =
    actions = ['make_finish' , 'export_admin_action']

    fieldsets = (
        ('基本信息' , {
            'fields': (('sample_number' ,'carbon_source' ,'genus',) ,
                       ('name' , 'gender' , 'age') ,
                       ('age_sgement' , 'province' ,) ,
                       ('height' , 'weight' , 'waistline' , 'bmi_value' ,) ,
                       ('phone' , 'email' ,) ,)
        }) ,
        ('生活习惯' , {
            'fields': (('complaint' , 'condition' ,) ,
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
            self.readonly_fields = ('sample_number' , 'carbon_source' ,'genus','bmi_value')
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
                    obj.is_status = 2  # 2是标记为完成的
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
