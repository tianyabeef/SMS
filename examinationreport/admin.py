from django.contrib import admin , messages
from django.core import serializers
import json
from docxtpl import DocxTemplate

from basicdata.models import CheckItem
from datacenter.models import DataInformation
from examinationreport.models import Reports
from import_export.admin import ImportExportActionModelAdmin
import datetime
from docxtpl import DocxTemplate
from examinationsample.models import Sample , Checks
from examinationsample.models import Progress
from questionnairesurvey.models import Quenstion
from labinformation.models import ConventionalIndex , QpcrIndexes , BioChemicalIndexes , ScfasIndexes , \
    DegradationIndexes

admin.site.empty_value_display = '-empty-'


@admin.register( Reports )
class ReportsAdmin( ImportExportActionModelAdmin , admin.ModelAdmin ):
    list_display = ( 'id' , 'sample_number' , 'word_report' , 'pdf_report' , 'report_testing_date' , 'report_user' , 'is_status')
    list_display_links = ('sample_number' ,)
    # readonly_fields = ('report_testing_date','report_user')
    ordering = ('-sample_number' ,)
    view_on_site = False
    list_max_show_all = 100
    list_per_page = 20
    list_filter = ['is_status' , ]
    search_fields = ('sample_number' ,)
    # resource_class =
    # form =
    # list_editable =
    actions = ['make_create' , 'make_published']

    def make_create(self , request , queryset):
        i = 0  # 提交成功的数据
        n = 0  # 提交过的数量
        t = 0  # 选中状态
        for obj in queryset:
            t += 1
            if obj.is_status < 1:
                obj.is_status = 1
                obj.save( )
                i += 1
            else:
                n += 1
        self.message_user( request , "选择%s条信息，完成操作%s条，不操作%s条" % (t , i , n) , level = messages.SUCCESS )

    make_create.short_description = "1同步数据"

    def make_published(self , request , queryset):
        i = 0  # 提交成功的数据
        n = 0  # 提交过的数量
        t = 0  # 选中状态
        for obj in queryset:
            t += 1
            if obj.is_status == 1:
                obj.is_status = 2
                obj.save( )
                i += 1
                obj_progress , created = Progress.objects.get_or_create( sample_number = obj.sample_number )
                if obj.report_testing_date is not None:
                    obj_progress.report_testing_date = obj.report_testing_date
                else:
                    obj_progress.report_testing_date = datetime.date.today( )
                obj_progress.report_testing_staff = request.user.last_name + ' ' + request.user.first_name
                obj_progress.is_status = 3
                obj_progress.save( )

            else:
                n += 1
        self.message_user( request , "选择%s条信息，完成操作%s条，不操作%s条" % (t , i , n) , level = messages.SUCCESS )

    make_published.short_description = "2标记完成"

    def get_changeform_initial_data(self , request):
        initial = super( ).get_changeform_initial_data( request )
        initial ['report_user'] = request.user.last_name + ' ' + request.user.first_name
        initial ['report_testing_date'] = datetime.date.today( )
        return initial

    def save_model(self , request , obj , form , change):
        obj.report_user = "%s %s" % (request.user.last_name , request.user.first_name)  # 系统自动添加创建人
        obj.report_user = request.user.last_name + ' ' + request.user.first_name
        obj.report_testing_date = datetime.date.today( )
        # 先同步数据
        # checkss = Checks.objects.filter(
        #     sample_number__sample_number = obj.sample_number )  # TODO 假设不存在样本收样后，检查项为空的情况
        # for checks in checkss:
        #     check_item = CheckItem.objects.get( number = checks.check_number )
        #     data = {}
        #     key_tmp = obj.sample_number + check_item.carbon_source + check_item.genus
        #     if key_tmp in data.keys( ):
        #         data [key_tmp] = {'sample_number': obj.sample_number , 'carbon_source': check_item.carbon_source ,
        #                           'genus': check_item.genus}
        #         if check_item.type.number == "JCMK0001":  # 问卷调查
        #             quenstion = Quenstion.objects.filter( sample_number = obj.sample_number ,
        #                                                   carbon_source = check_item.carbon_source ,
        #                                                   genus = check_item.genus )
        #             tmp = serializers.serialize( 'json' , queryset = quenstion )
        #             quenstion_data = json.loads( tmp ) [0] ['fields']
        #             data [key_tmp] = data [key_tmp].update( quenstion_data )
        #
        #         if check_item.type.number == "JCMK0002":  # 常规指标项
        #             conventional = ConventionalIndex.objects.filter( sample_number = obj.sample_number ,
        #                                                              carbon_source = check_item.carbon_source ,
        #                                                              genus = check_item.genus )
        #             tmp = serializers.serialize( 'json' , queryset = conventional )
        #             conventional_data = json.loads( tmp ) [0] ['fields']
        #             data [key_tmp] = data [key_tmp].update( conventional_data )
        #         if check_item.type.number == "JCMK0003":  # 生化指标项
        #             bio = BioChemicalIndexes.objects.filter( sample_number = obj.sample_number ,
        #                                                      carbon_source = check_item.carbon_source ,
        #                                                      genus = check_item.genus )
        #             tmp = serializers.serialize( 'json' , queryset = bio )
        #             bio_data = json.loads( tmp ) [0] ['fields']
        #             data [key_tmp] = data [key_tmp].update( bio_data )
        #         if check_item.type.number == "JCMK0004":  # qPCR检测项
        #             qpcr = QpcrIndexes.objects.filter( sample_number = obj.sample_number ,
        #                                                carbon_source = check_item.carbon_source ,
        #                                                genus = check_item.genus )
        #             tmp = serializers.serialize( 'json' , queryset = qpcr )
        #             qpcr_data = json.loads( tmp ) [0] ['fields']
        #             data [key_tmp] = data [key_tmp].update( qpcr_data )
        #         if check_item.type.number == "JCMK0005":  # SCFAs检测项
        #             scfas = ScfasIndexes.objects.filter( sample_number = obj.sample_number ,
        #                                                  carbon_source = check_item.carbon_source ,
        #                                                  genus = check_item.genus )
        #             tmp = serializers.serialize( 'json' , queryset = scfas )
        #             scfas_data = json.loads( tmp ) [0] ['fields']
        #             data [key_tmp] = data [key_tmp].update( scfas_data )
        #         if check_item.type.number == "JCMK0006":  # 气压和降解率检测项
        #             degradation = DegradationIndexes.objects.filter( sample_number = obj.sample_number ,
        #                                                              carbon_source = check_item.carbon_source ,
        #                                                              genus = check_item.genus )
        #             tmp = serializers.serialize( 'json' , queryset = degradation )
        #             degradation_data = json.loads( tmp ) [0] ['fields']
        #             data [key_tmp] = data [key_tmp].update( degradation_data )
        #     # for tmp in data.values( ):
        #     #     DataInformation( *tmp ).save( )
        #
        # # 生成word报告
        # doc = DocxTemplate(
        #     'media/' + str( Sample.objects.filter( sample_number = obj.sample_number ) [0].report_template_url ) )
        # checks = Checks.objects.filter( sample_number__sample_number = obj.sample_number )
        #
        #
        # context = {'company_name': str( checks.count( ) ) + "202年↑↑↑↑10月"}
        # doc.render( context )
        # doc.save( 'media/' + str( obj.word_report ) )

        obj.save( )
