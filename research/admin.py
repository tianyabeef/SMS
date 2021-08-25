from django.contrib import admin
import re
from basicdata.models import Carbon , Age , Province
from .models import Invoice , Contract , InvoiceTitle , Bill , Accounting , Stuff , ExperimentalData , Material , \
    Contract
from import_export import resources
from import_export.formats import base_formats
from django import forms
from django.forms.models import BaseInlineFormSet
import datetime
from import_export.admin import ImportExportActionModelAdmin , ExportActionModelAdmin
import numpy as np
from import_export import fields
from django.contrib import messages
from django.db.models import Sum


@admin.register( InvoiceTitle )
class InvoiceTitleAdmin( ImportExportActionModelAdmin , admin.ModelAdmin ):
    pass


class BillInlineFormSet( BaseInlineFormSet ):
    """财务发票的进账的FormSet（Inline）"""

    def clean(self):
        super( ).clean( )
        total = 0
        for form in self.forms:
            if not form.is_valid( ):
                return
            # if form.cleaned_data and not form.cleaned_data['DELETE']:
            if form.cleaned_data:
                total += form.cleaned_data ['income']
                if (form.cleaned_data ['income'] > 0) and (
                        form.cleaned_data ['date'] is None):  # 到账金额大于0 ，到账时间为None，系统自动填写今天时间
                    form.cleaned_data ['date'] = datetime.date.today( )
                if form.cleaned_data ['date'] is not None:
                    self.instance.income_date = form.cleaned_data ['date']
        self.instance.income = total


class BillInline( admin.TabularInline ):
    """
    财务发票管理的进账（Inline）
    """
    model = Bill
    formset = BillInlineFormSet
    extra = 1


class InvoiceResource( resources.ModelResource ):
    """
    按照发票导出
    """

    class Meta:
        model = Invoice
        skip_unchanged = True
        fields = ('id' , 'contract__contract_number' , 'title__title' , 'amount' , 'date' , 'note' , 'income' ,
                  'income_date')
        export_order = (
            'id' , 'contract__contract_number' , 'title__title' , 'amount' , 'date' , 'note' , 'income' ,
            'income_date')

    def get_export_headers(self):
        return ['id' , '合同号' , '发票抬头' , '发票金额' , '开票日期' , '备注' , '到账金额' , '到账日期']


@admin.register( Invoice )
class InvoiceAdmin( ExportActionModelAdmin , admin.ModelAdmin ):
    list_display = (
        'contract' , 'title' , 'amount' , 'date' , 'income' , 'income_date' , 'is_status')
    list_display_links = ('title' ,)
    # readonly_fields =
    ordering = ('-create_date' ,)
    view_on_site = False
    list_max_show_all = 100
    list_per_page = 20
    list_filter = ['is_status' , ]
    search_fields = ('contract__contract_number' , 'title__title' ,)
    radio_fields = {'type': admin.HORIZONTAL , }
    date_hierarchy = 'create_date'
    resource_class = InvoiceResource
    inlines = [BillInline , ]
    # autocomplete_fields = ('contract' , 'title' ,)
    # form = ContractForm
    actions = ['make_invoice_submit' , 'export_admin_action']
    fieldsets = (
        ('开票信息' , {
            'fields': (('contract' , 'title') , ('invoice_code' , 'amount' , 'date') ,
                       ('content' , 'note') ,)
        }) ,
        ('到账信息' , {
            'fields': (('income' , 'income_date') ,)
        }) ,
        ('状态信息' , {
            'fields': (('is_status' , 'writer') , 'historys')
        }) ,
    )

    def get_readonly_fields(self , request , obj=None):

        if request.user.is_superuser:
            self.readonly_fields = ('contract' , 'title' , 'historys' , 'income')
        elif obj is not None:
            if obj.amount != 0:
                self.readonly_fields = (
                    'contract' , 'title' , 'historys' , 'income' , 'income_date' , 'amount' , 'date' , 'is_status')
        else:
            self.readonly_fields = ('contract' , 'title' , 'historys' , 'income' , 'income_date' , 'is_status')
        return self.readonly_fields

    def save_formset(self , request , form , formset , change):
        instances = formset.save( commit = False )
        total = {'del_income': 0}
        for obj in formset.deleted_objects:
            total ['del_income'] += obj.income
            obj.delete( )
        if instances:
            formset.instance.income = formset.instance.income - total ['del_income']  # 更新发票
            formset.instance.save( )
            for instance in instances:
                if (instance.income > 0) and (instance.date is None):  # 到账金额大于0 ，到账时间为None，系统自动填写今天时间
                    instance.date = datetime.date.today( )
                instance.save( )
            formset.save_m2m( )
            # 所有信息保存好之后，更新合同,把合同下所有发票到账求和
            formset.instance.contract.amount_in = \
                Invoice.objects.filter( contract = formset.instance.contract ).aggregate( Sum( 'income' ) ) [
                    'income__sum']
            formset.instance.contract.amount_date = formset.instance.income_date
            formset.instance.contract.save( )

    def make_invoice_submit(self , request , queryset):
        """
        批量提交开票完成
         (1 , '开票中') ,
        (2 , '完成') ,
        """
        i = 0  # 提交成功的数量
        n = 0  # 提交过的数量
        t = 0  # 选中的总数量
        for obj in queryset:
            t += 1
            if obj.is_status == 1:
                obj.is_status = 2
                obj.save( )
                i += 1
            else:
                n += 1

    make_invoice_submit.short_description = '标记完成'

    def get_changeform_initial_data(self , request):
        initial = super( ).get_changeform_initial_data( request )
        initial ['writer'] = request.user.last_name + ' ' + request.user.first_name
        initial ['date'] = datetime.date.today( )
        return initial

    def save_model(self , request , obj , form , change):
        # 到账日期不为空时，在合同管理中的最后一次到账日期做更新
        if obj.income_date is not None:
            obj.contract.amount_date = obj.income_date
            obj.contract.save( )
        # 1、新增快递单号时自动记录时间戳
        if obj.tracking_number and not obj.send_date:
            obj.send_date = datetime.date.today( )
        elif not obj.tracking_number:
            obj.send_date = None

        if obj.historys is None:
            obj.historys = ';合同号:' + obj.contract.contract_number + ';时间:' + datetime.date.today( ).__str__( )
        else:
            if obj.income != 0:
                obj.historys = obj.historys + '\n' + ';合同号:' + obj.contract.contract_number + ';到账金额:' + str(
                    obj.income ) + ';时间:' + datetime.date.today( ).__str__( )
            else:
                obj.historys = obj.historys + '\n' + ';合同号:' + obj.contract.contract_number + ';时间:' + datetime.date.today( ).__str__( )
        obj.save( )


class InvoiceInlineFormSet( BaseInlineFormSet ):
    """
    合同的开票的FormSet
    """

    def clean(self):
        super( ).clean( )
        total = {'amount': 0}
        for form in self.forms:
            if not form.is_valid( ):
                return
            if form.cleaned_data:
                total ['amount'] += form.cleaned_data ['amount']
                if (form.cleaned_data ['amount'] > 0) and (
                        form.cleaned_data ['date'] is None):  # 开票金额大于0 ，开票时间为None，系统自动填写今天时间
                    form.cleaned_data ['date'] = datetime.date.today( )
        self.instance.make_out_amount = total ['amount']


class AccountingInlineFormSet( BaseInlineFormSet ):
    """
    合同的开票的FormSet
    """

    def clean(self):
        super( ).clean( )
        total = {'amount': 0}
        for form in self.forms:
            if not form.is_valid( ):
                return
            if form.cleaned_data:
                total ['amount'] += form.cleaned_data ['amount']
                if (form.cleaned_data ['amount'] > 0) and (
                        form.cleaned_data ['date'] is None):  # 账目金额大于0 ，创建时间为None，系统自动填写今天时间
                    form.cleaned_data ['date'] = datetime.date.today( )
        self.instance.project_amount = total ['amount']


class InvoiceInline( admin.StackedInline ):
    """
     合同管理中的开票（Inline）
    """
    model = Invoice
    formset = InvoiceInlineFormSet
    extra = 1
    fields = (('title' , 'amount') , 'date')
    raw_id_fields = ('title' ,)

    def get_readonly_fields(self , request , obj=None):
        if obj is not None:
            if (obj.is_status == 9) and (not request.user.is_superuser):  # 普通用于修改状态后，无法保存
                self.readonly_fields = ('title' , 'amount' , 'date')
        return self.readonly_fields


class AccountingInline( admin.StackedInline ):
    """
     合同管理中的开票（Inline）
    """
    model = Accounting
    formset = AccountingInlineFormSet
    extra = 1
    fields = ('name' , 'amount' , 'date' , 'note')

    def get_readonly_fields(self , request , obj=None):
        if obj is not None:
            if (obj.is_status == 9) and (not request.user.is_superuser):  # 普通用于修改状态后，无法保存
                self.readonly_fields = ('name' , 'amount' , 'date' , 'note')
        return self.readonly_fields


class ContractResource( resources.ModelResource ):
    """
    按照合同号导出
    """

    class Meta:
        model = Contract
        skip_unchanged = True
        fields = ('id' , 'contract_number' , 'name' , 'partner_company' , 'keyword' , 'contacts' , 'contacts_email' ,
                  'contact_phone' , 'contact_address' , 'all_amount' , 'project_amount' , 'make_out_amount' ,
                  'amount_in' , 'amount_date' , 'is_status' , 'project_leader' , 'report_file' , 'note')
        export_order = (
            'id' , 'contract_number' , 'name' , 'partner_company' , 'keyword' , 'contacts' , 'contacts_email' ,
            'contact_phone' , 'contact_address' , 'all_amount' , 'project_amount' , 'make_out_amount' , 'amount_in' ,
            'amount_date' , 'is_status' , 'project_leader' , 'report_file' , 'note')

    def get_export_headers(self):
        return ['id' , '合同号' , '合同名' , '合同单位' , '项目关键词' , '合同联系人' , '合同联系人邮箱' , '合同联系人电话' , '合同联系人地址' , '合同总款额' ,
                '项目总费用' , '已开票金额' , '已到账金额' , '最后一笔到款日' , '状态' , '项目负责人' , '志愿者报告路径' , '合同备注']


@admin.register( Contract )
class ContractAdmin( ExportActionModelAdmin , admin.ModelAdmin ):
    """
        合同中的Admin
    """
    list_display = (
        'contract_number' , 'name' , 'partner_company_modify' , 'keyword' , 'all_amount' , 'project_amount' ,
        'make_out_amount' , 'amount_in' , 'amount_date' , 'file_link' , 'is_status')
    list_display_links = ('contract_number' ,)
    # readonly_fields =
    ordering = ('-create_date' ,)
    view_on_site = False
    list_max_show_all = 100
    list_per_page = 20
    list_filter = ['is_status' , ]
    search_fields = ('keyword' , 'contract_number' , 'name' , 'partner_company' ,)
    radio_fields = {'ht_choices': admin.HORIZONTAL , }
    date_hierarchy = 'create_date'
    resource_class = ContractResource
    inlines = [InvoiceInline , AccountingInline]
    # autocomplete_fields = ('project_leader' ,)
    # form =
    actions = (
        'export_admin_action' , 'upload_data' , 'make_contract' , 'pre_experiment' ,
        'make_two' , 'make_four' , 'make_six' , 'make_eight' , 'make_report' , 'make_finish')
    # form = ContractForm

    fieldsets = (
        ('基本信息' , {
            'fields': (('contract_number' , 'keyword') , ('name' , 'partner_company' ,) ,
                       ('contacts' , 'contacts_email' , 'contact_phone') ,
                       ('contact_address' ,) ,
                       ('all_amount' , 'project_amount' , 'make_out_amount' , 'amount_in' , 'amount_date') ,
                       )
        }) ,
        ('邮寄信息' , {
            'fields': (('tracking_number' , 'send_date' , 'receive_date' , 'ht_choices') ,)
        }) ,
        ('上传合同' , {
            'fields': ('contract_file' , 'contract_file_scanning')
        }) ,
        ('资料信息' , {
            'fields': (('project_leader' , 'report_file' , 'payment') ,
                       ('is_status' ,) ,
                       ('note' ,) ,
                       ('historys' ,))
        })

    )

    def get_readonly_fields(self , request , obj=None):
        if request.user.is_superuser:
            self.readonly_fields = (
                'historys' , 'project_amount' , 'make_out_amount' , 'amount_in' , 'amount_date' , 'amount_date')
        else:
            self.readonly_fields = (
                'historys' , 'project_amount' , 'make_out_amount' , 'amount_in' , 'amount_date' , 'amount_date')
        return self.readonly_fields

    def partner_company_modify(self , obj):
        # 抬头的单位名称
        if obj.partner_company == '':
            invoices = Invoice.objects.filter( contract = obj )
            return invoices [0].title.title if invoices else ''
        else:
            return obj.partner_company

    partner_company_modify.short_description = '单位'

    def upload_data(self , request , queryset):
        """
        安排上传资料
        """
        i = 0  # 提交成功的数量
        n = 0  # 提交过的数量
        t = 0  # 选中的总数量
        for obj in queryset:
            t += 1
            if obj.is_status != 9:
                Stuff.objects.get_or_create( contract_number = obj.contract_number )
                i += 1
            else:
                n += 1
        self.message_user( request , '选择%s条信息，完成操作%s条，不操作%s条' % (t , i , n) , level = messages.SUCCESS )

    upload_data.short_description = '1安排上传资料'

    # def make_test(self , request , queryset):
    #     i = 0  # 提交成功的数量
    #     n = 0  # 提交过的数量
    #     t = 0  # 选中的总数量
    #     for obj in queryset:
    #         t += 1
    #         if obj.is_status != 9:
    #             stuffs = Stuff.objects.filter( contract_number = obj.contract_number )
    #             if stuffs.count( ) == 1:  # 一份合同，只有一份资料
    #                 cs = re.split( '[；;]' , stuffs [0].carbon_source_content )
    #                 samples = re.split( '[；;]' , stuffs [0].sample_content )
    #                 for cs_temp in cs:
    #                     cs_temp_id = Carbon.objects.get( cid = cs_temp )
    #                     for sample in samples:
    #                         ExperimentalData.objects.get_or_create( contract_number = obj.contract_number ,
    #                                                                 sample_number = sample ,
    #                                                                 carbon_source = cs_temp_id ,
    #                                                                 carbon_source_zh = cs_temp_id.name )  # 增加样本列表
    #                 i += 1
    #             else:
    #                 n += 1
    #     self.message_user( request , '选择%s条信息，完成操作%s条，不操作%s条' % (t , i , n) , level = messages.SUCCESS )
    #
    # make_test.short_description = '2排班检测'

    def make_contract(self , request , queryset):
        i = 0  # 提交成功的数量
        n = 0  # 提交过的数量
        t = 0  # 选中的总数量
        for obj in queryset:
            t += 1
            if obj.is_status != 9:
                obj.is_status = 2
                obj.save( )
                i += 1
            else:
                n += 1
        self.message_user( request , '选择%s条信息，完成操作%s条，不操作%s条' % (t , i , n) , level = messages.SUCCESS )

    make_contract.short_description = '3合同签署'

    def pre_experiment(self , request , queryset):
        i = 0  # 提交成功的数量
        n = 0  # 提交过的数量
        t = 0  # 选中的总数量
        for obj in queryset:
            t += 1
            if obj.is_status != 9:
                obj.is_status = 3
                obj.save( )
                i += 1
            else:
                n += 1
        self.message_user( request , '选择%s条信息，完成操作%s条，不操作%s条' % (t , i , n) , level = messages.SUCCESS )

    pre_experiment.short_description = '4预实验'

    def make_two(self , request , queryset):
        i = 0  # 提交成功的数量
        n = 0  # 提交过的数量
        t = 0  # 选中的总数量
        for obj in queryset:
            t += 1
            if obj.is_status != 9:
                obj.is_status = 4
                obj.save( )
                i += 1
            else:
                n += 1
        self.message_user( request , '选择%s条信息，完成操作%s条，不操作%s条' % (t , i , n) , level = messages.SUCCESS )

    make_two.short_description = '5项目进度20'

    def make_four(self , request , queryset):
        i = 0  # 提交成功的数量
        n = 0  # 提交过的数量
        t = 0  # 选中的总数量
        for obj in queryset:
            t += 1
            if obj.is_status != 9:
                obj.is_status = 5
                obj.save( )
                i += 1
            else:
                n += 1
        self.message_user( request , '选择%s条信息，完成操作%s条，不操作%s条' % (t , i , n) , level = messages.SUCCESS )

    make_four.short_description = '6项目进度40'

    def make_six(self , request , queryset):
        i = 0  # 提交成功的数量
        n = 0  # 提交过的数量
        t = 0  # 选中的总数量
        for obj in queryset:
            t += 1
            if obj.is_status != 9:
                obj.is_status = 6
                obj.save( )
                i += 1
            else:
                n += 1
        self.message_user( request , '选择%s条信息，完成操作%s条，不操作%s条' % (t , i , n) , level = messages.SUCCESS )

    make_six.short_description = '7项目进度60'

    def make_eight(self , request , queryset):
        i = 0  # 提交成功的数量
        n = 0  # 提交过的数量
        t = 0  # 选中的总数量
        for obj in queryset:
            t += 1
            if obj.is_status != 9:
                obj.is_status = 7
                obj.save( )
                i += 1
            else:
                n += 1
        self.message_user( request , '选择%s条信息，完成操作%s条，不操作%s条' % (t , i , n) , level = messages.SUCCESS )

    make_eight.short_description = '8项目进度80'

    def make_report(self , request , queryset):
        i = 0  # 提交成功的数量
        n = 0  # 提交过的数量
        t = 0  # 选中的总数量
        for obj in queryset:
            t += 1
            if obj.is_status != 9:
                obj.is_status = 8
                obj.save( )
                i += 1
            else:
                n += 1
        self.message_user( request , '选择%s条信息，完成操作%s条，不操作%s条' % (t , i , n) , level = messages.SUCCESS )

    make_report.short_description = '9报告出具'

    def make_finish(self , request , queryset):
        i = 0  # 提交成功的数量
        n = 0  # 提交过的数量
        t = 0  # 选中的总数量
        for obj in queryset:
            t += 1
            if obj.is_status != 9:
                obj.is_status = 9
                obj.save( )
                i += 1
            else:
                n += 1
        self.message_user( request , '选择%s条信息，完成操作%s条，不操作%s条' % (t , i , n) , level = messages.SUCCESS )

    make_finish.short_description = '10标记完成'

    def get_changeform_initial_data(self , request):
        initial = super( ).get_changeform_initial_data( request )
        initial ['project_leader'] = request.user.last_name + ' ' + request.user.first_name
        initial ['writer'] = request.user.last_name + ' ' + request.user.first_name
        return initial

    def save_formset(self , request , form , formset , change):
        instances = formset.save( commit = False )
        total = {'del_amount': 0 , 'acc_del_amount': 0}
        for obj in formset.deleted_objects:
            if obj.fp:
                total ['del_amount'] += obj.amount
            else:
                total ['acc_del_amount'] += obj.amount
            obj.delete( )
        if instances:
            formset.instance.make_out_amount = formset.instance.make_out_amount - total ['del_amount']
            formset.instance.project_amount = formset.instance.project_amount - total ['acc_del_amount']  # 项目费用
            formset.instance.save( )
            for instance in instances:
                if (instance.amount > 0) and (instance.date is None):  # 开票金额大于0 ，开票时间为None，系统自动填写今天时间
                    instance.date = datetime.date.today( )
                instance.save( )
            formset.save_m2m( )

    def save_model(self , request , obj , form , change):
        # 1、新增快递单号时自动记录时间戳
        if obj.tracking_number and not obj.send_date:
            obj.send_date = datetime.date.today( )
        elif not obj.tracking_number:
            obj.send_date = None

        if obj.historys is None:
            obj.historys = ';合同号:' + obj.contract_number + ';时间:' + datetime.date.today( ).__str__( )
        else:
            if obj.amount_date is not None:
                obj.historys = obj.historys + '\n' + ';合同号:' + obj.contract_number + ';最后一笔到款日:' + str(
                    obj.amount_date ) + ';时间:' + datetime.date.today( ).__str__( )
            else:
                obj.historys = obj.historys + '\n' + ';合同号:' + obj.contract_number + ';时间:' + datetime.date.today( ).__str__( )
        obj.save( )


@admin.register( Bill )
class BillAdmin( ExportActionModelAdmin , admin.ModelAdmin ):
    list_display = ('invoice' , 'income' , 'date' ,)
    list_display_links = ('invoice' ,)
    # readonly_fields =
    # ordering = ('-create_date' ,)
    view_on_site = False
    list_max_show_all = 100
    list_per_page = 20
    # list_filter = ['is_status' , ]
    search_fields = ('invoice__title__title' ,)

    # radio_fields = {'ht_choices': admin.HORIZONTAL , }
    # date_hierarchy = 'create_date'
    # resource_class = ContractResource
    # inlines = [InvoiceInline , ]

    # autocomplete_fields = ('project_leader' ,)
    # actions = ('make_receive','export_admin_action')
    # form = ContractForm
    def get_changeform_initial_data(self , request):
        initial = super( ).get_changeform_initial_data( request )
        initial ['date'] = datetime.date.today( )
        return initial


class AccountingResource( resources.ModelResource ):
    """
    按照发票导出
    """

    class Meta:
        model = Accounting
        skip_unchanged = True
        fields = ('id' , 'contract__contract_number' , 'name' , 'amount' , 'date' , 'note')
        export_order = (
            'id' , 'contract__contract_number' , 'name' , 'amount' , 'date' , 'note')

    def get_export_headers(self):
        return ['id' , '合同号' , '账目名称' , '账目金额' , '创建时间' , '备注']


@admin.register( Accounting )
class AccountingAdmin( ExportActionModelAdmin , admin.ModelAdmin ):
    list_display = (
        'contract' , 'name' , 'amount' , 'date' ,)
    list_display_links = ('name' ,)
    # readonly_fields =
    # ordering = ('-create_date' ,)
    view_on_site = False
    list_max_show_all = 100
    list_per_page = 20
    # list_filter = ['is_status' , ]
    search_fields = ('contract__contract_number' , 'name')
    resource_class = AccountingResource

    def get_readonly_fields(self , request , obj=None):
        if not obj is None:
            self.readonly_fields = ('contract' ,)
        return self.readonly_fields


class StuffForm( forms.ModelForm ):
    carbon_source_content = forms.CharField( label = "检测碳源" ,
                                             help_text = "可填写多个碳源模块，碳源之间用;隔开。示例：KYTY0001;KYTY0002;KYTY0003;KYTY0004" ,
                                             required = False , widget = forms.TextInput(
            attrs = {'class': 'vTextField , form-control' , 'placeholder': "示例：KYTY0001;KYTY0002;KYTY0003;KYTY0004"} ) ,
                                             error_messages = {'required': '这个字段是非必填项。'} )

    class Meta:
        model = Stuff
        exclude = ("" ,)

    def clean_carbon_source_content(self , exclude=None):
        if not (self.cleaned_data ["carbon_source_content"].strip( ) == ""):
            numbers = re.split( '[；;]' , self.cleaned_data ["carbon_source_content"].strip( ) )
            if len( numbers ) > 1:
                for number in numbers:
                    if Carbon.objects.filter( cid = number ).count( ) == 0:
                        raise forms.ValidationError( number + "检测碳源编号不存在,请到基础数据管理核查" )
            else:
                if Carbon.objects.filter( cid = numbers [0] ).count( ) == 0:
                    raise forms.ValidationError( numbers [0] + "检测碳源编号不存在" )
            return self.cleaned_data ["carbon_source_content"].strip( )
        else:
            return self.cleaned_data ["carbon_source_content"]


@admin.register( Stuff )
class StuffAdmin( ExportActionModelAdmin , admin.ModelAdmin ):
    list_display = ('id' , 'contract_number' , 'report_file' , 'create_date' , 'is_status')
    list_display_links = ('contract_number' ,)
    readonly_fields = ('historys' ,)
    ordering = ('-create_date' ,)
    view_on_site = False
    list_max_show_all = 100
    list_per_page = 20
    # list_filter =
    search_fields = ('contract_number' ,)
    form = StuffForm

    # resource_class = ProvinceResource
    # form = CheckItemForm
    # list_editable =
    actions = ['make_stuff_submit' , 'export_admin_action']

    def make_stuff_submit(self , request , queryset):
        """
        批量提交资料上传完成
        (1 , '上传中') ,
        (2 , '完成') ,
        """
        i = 0  # 提交成功的数量
        n = 0  # 提交过的数量
        t = 0  # 选中的总数量
        for obj in queryset:
            t += 1
            if obj.is_status == 1:
                cs = re.split( '[；;]' , obj.carbon_source_content )
                samples = re.split( '[；;]' , obj.sample_content )
                for cs_temp in cs:
                    cs_temp_id = Carbon.objects.get( cid = cs_temp )
                    for sample in samples:
                        ExperimentalData.objects.get_or_create( contract_number = obj.contract_number ,
                                                                sample_number = sample ,
                                                                carbon_source = cs_temp_id ,
                                                                carbon_source_zh = cs_temp_id.name )  # 增加样本列表
                obj.is_status = 2
                obj.save( )
                i += 1
            else:
                n += 1
        self.message_user( request , '选择%s条信息，完成操作%s条，不操作%s条' % (t , i , n) , level = messages.SUCCESS )

    make_stuff_submit.short_description = '标记完成'

    def get_changeform_initial_data(self , request):
        initial = super( ).get_changeform_initial_data( request )
        initial ['writer'] = request.user.last_name + ' ' + request.user.first_name
        return initial

    def save_model(self , request , obj , form , change):
        if obj.historys is None:
            obj.historys = "合同号:" + obj.contract_number + ";修改时间:" + datetime.date.today( ).__str__( )
        else:
            obj.historys = obj.historys + "\n" + "合同号:" + obj.contract_number + ";修改时间:" + datetime.date.today( ).__str__( )

        obj.save( )


class ExperimentalDataResource( resources.ModelResource ):
    class Meta:
        model = ExperimentalData
        skip_unchanged = True
        fields = (
            'id' , 'contract_number' , 'sample_number' , 'internal_number' , 'carbon_source' , 'group' ,
            'intervention' , 'carbon_source_zh' , 'recordNo' , 'name' , 'gender' , 'age' , 'age_sgement' , 'province' ,
            'height' , 'weight' , 'fbj' , 'blood_pressure' , 'trioxypurine' , 'triglyceride' , 'anamnesis' , 'staging' ,
            'therapies' ,
            'acetic_acid' , 'propionic' , 'butyric' , 'isobutyric_acid' ,
            'valeric' , 'isovaleric' , 'gas' , 'co2' , 'ch4' , 'h2' , 'h2s' , 'degradation' , 'BIFI' , 'LAC' , 'CS' ,
            'FN' , 'EF' , 'BT' , 'AKK' , 'FAE')
        export_order = (
            'id' , 'contract_number' , 'sample_number' , 'internal_number' , 'carbon_source' , 'group' ,
            'intervention' , 'carbon_source_zh' , 'recordNo' , 'name' , 'gender' , 'age' , 'age_sgement' , 'province' ,
            'height' , 'weight' , 'fbj' , 'blood_pressure' , 'trioxypurine' , 'triglyceride' , 'anamnesis' , 'staging' ,
            'therapies' ,
            'acetic_acid' , 'propionic' , 'butyric' , 'isobutyric_acid' ,
            'valeric' , 'isovaleric' , 'gas' , 'co2' , 'ch4' , 'h2' , 'h2s' , 'degradation' , 'BIFI' , 'LAC' , 'CS' ,
            'FN' , 'EF' , 'BT' , 'AKK' , 'FAE')

    @staticmethod
    def sex_value_display(value):
        SEX_CHOICES = {
            '女': 0 ,
            '男': 1 ,
        }
        if value is not None:
            value = SEX_CHOICES.get( value )
        else:
            value = None  # 缺失值
        return value

    def get_diff_headers(self):
        return ['id' , '合同号' , '样本编号' , '对内编号' , '碳源' , '组别' , '干预前后' , '碳源中文名称' , '病历号' , '姓名' , '性别' , '年龄' , '年龄分段' ,
                '地域' , '身高' , '体重' , '空腹血糖' , '血压' , '尿酸' , '血脂' , '确诊疾病' , '疾病分期' , '治疗方法' , '乙酸' , '丙酸' , '丁酸' ,
                '异丁酸' , '戊酸' ,
                '异戊酸' , '产气量' , 'CO2' , 'CH4' , 'H2' , 'H2S' , '降解率' , '双歧杆菌' , '乳酸菌' , '共生梭菌' , '具核梭杆菌' , '粪肠球菌' ,
                '多形拟杆菌' , '阿克曼氏菌' , '普拉梭菌']

    def get_export_headers(self):
        return ['id' , '合同号' , '样本编号' , '对内编号' , '碳源' , '组别' , '干预前后' , '碳源中文名称' , '病历号' , '姓名' , '性别' , '年龄' , '年龄分段' ,
                '地域' , '身高' , '体重' , '空腹血糖' , '血压' , '尿酸' , '血脂' , '确诊疾病' , '疾病分期' , '治疗方法' , '乙酸' , '丙酸' , '丁酸' ,
                '异丁酸' , '戊酸' ,
                '异戊酸' , '产气量' , 'CO2' , 'CH4' , 'H2' , 'H2S' , '降解率' , '双歧杆菌' , '乳酸菌' , '共生梭菌' , '具核梭杆菌' , '粪肠球菌' ,
                '多形拟杆菌' , '阿克曼氏菌' , '普拉梭菌']

    def before_import_row(self , row , **kwargs):
        """
        Calls :meth:`import_export.fields.Field.save` if ``Field.attribute``
        and ``Field.column_name`` are found in ``data``.
        """
        carbons = Carbon.objects.filter( id = row ['碳源'] )
        if carbons.count( ) == 0:
            raise forms.ValidationError( '碳源名称有误，请到基础数据中核实。' )
        else:
            row ['碳源中文名称'] = Carbon.objects.get( id = row ['碳源'] ).name
        if (row ['id'] is None) and (  # TODO 样本编号已经设置唯一，联合唯一有待删除
                ExperimentalData.objects.filter( contract_number = row ['合同号'] , sample_number = row ['样本编号'] ,
                                                 carbon_source = row ['碳源'] ).count( ) > 0):
            raise forms.ValidationError( '合同编号，样本编号、碳源、记录内容联合唯一，不能有冲突。' )
        if (Age.objects.filter( name = row ["年龄分段"] ).count( ) == 0) and (
                (row ["年龄分段"] is not None) and (row ["年龄分段"] is not "")):
            raise forms.ValidationError( "年龄段在数据库中无法查询到" )

        if (Province.objects.filter( name = row ["地域"] ).count( ) == 0) and (
                (row ["地域"] is not None) and (row ["地域"] is not "")):
            raise forms.ValidationError( "地域在数据库中无法查询到" )

    def get_or_init_instance(self , instance_loader , row):
        """
        Either fetches an already existing instance or initializes a new one.
        """
        instance = self.get_instance( instance_loader , row )
        row ['contract_number'] = row ['合同号']
        row ['sample_number'] = row ['样本编号']
        row ['internal_number'] = row ['对内编号']
        row ['carbon_source'] = row ['碳源']
        row ['group'] = row ['组别']
        row ['intervention'] = row ['干预前后']
        row ['carbon_source_zh'] = row ['碳源中文名称']
        row ['recordNo'] = row ['病历号']
        row ['name'] = row ['姓名']
        row ['gender'] = self.sex_value_display( row ['性别'] )
        row ['age'] = row ['年龄']
        row ['age_sgement'] = row ['年龄分段']
        row ['province'] = row ['地域']
        row ['height'] = row ['身高']
        row ['weight'] = row ['体重']
        row ['fbj'] = row ['空腹血糖']
        row ['blood_pressure'] = row ['血压']
        row ['trioxypurine'] = row ['尿酸']
        row ['triglyceride'] = row ['血脂']
        row ['anamnesis'] = row ['确诊疾病']
        row ['staging'] = row ['疾病分期']
        row ['therapies'] = row ['治疗方法']
        row ['acetic_acid'] = row ['乙酸']
        row ['propionic'] = row ['丙酸']
        row ['butyric'] = row ['丁酸']
        row ['isobutyric_acid'] = row ['异丁酸']
        row ['valeric'] = row ['戊酸']
        row ['isovaleric'] = row ['异戊酸']
        row ['gas'] = row ['产气量']
        row ['co2'] = row ['CO2']
        row ['ch4'] = row ['CH4']
        row ['h2'] = row ['H2']
        row ['h2s'] = row ['H2S']
        row ['degradation'] = row ['降解率']
        row ['BIFI'] = row ['双歧杆菌']
        row ['LAC'] = row ['乳酸菌']
        row ['CS'] = row ['共生梭菌']
        row ['FN'] = row ['具核梭杆菌']
        row ['EF'] = row ['粪肠球菌']
        row ['BT'] = row ['多形拟杆菌']
        row ['AKK'] = row ['阿克曼氏菌']
        row ['FAE'] = row ['普拉梭菌']
        if instance:
            return instance , False
        else:
            return self.init_instance( row ) , True

    def before_save_instance(self , instance , using_transactions , dry_run):
        """
            导入前，对粪便的短链脂肪酸乘以系数10
        """

        if (instance.acetic_acid is not None) and (instance.propionic is not None) and (
                instance.butyric is not None) and (
                instance.isobutyric_acid is not None) and (instance.valeric is not None) and (
                instance.isovaleric is not None):
            instance.total_acid = instance.acetic_acid + instance.propionic + instance.butyric + instance.isobutyric_acid + instance.valeric + \
                                  instance.isovaleric

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


class ContractForm( forms.ModelForm ):
    class Meta:
        model = Contract
        exclude = ("" ,)

    def clean_age_sgement(self):
        if Age.objects.filter( name = self.cleaned_data ["age_sgement"] ).count( ) == 0:
            raise forms.ValidationError( "年龄段在数据库中无法查询到" )
        return self.cleaned_data ["age_sgement"]

    def clean_province(self):
        if Province.objects.filter( name = self.cleaned_data ["province"] ).count( ) == 0:
            raise forms.ValidationError( "地域在数据库中无法查询到" )
        return self.cleaned_data ["province"]


class ContractListFilter( admin.SimpleListFilter ):
    '''实验数据中的合同'''
    title = '合同号'
    parameter_name = 'Contract'

    def lookups(self , request , model_admin):
        contracts = Contract.objects.all( )
        value = [i.contract_number for i in contracts]
        label = ['合同号:' + i.contract_number for i in contracts]
        return tuple( zip( value , label ) )

    def queryset(self , request , queryset):
        if self.value( ) is None:
            return queryset
        else:
            return queryset.filter( contract_number = self.value( ) )


class AgeListFilter( admin.SimpleListFilter ):
    '''实验数据中的合同'''
    title = '年龄段'
    parameter_name = 'Age'

    def lookups(self , request , model_admin):
        contracts = Age.objects.all( )
        value = [i.name for i in contracts]
        label = ['年龄段:' + i.name for i in contracts]
        return tuple( zip( value , label ) )

    def queryset(self , request , queryset):
        if self.value( ) is None:
            return queryset
        else:
            return queryset.filter( age_sgement = self.value( ) )


class ProvinceListFilter( admin.SimpleListFilter ):
    '''实验数据中的合同'''
    title = '地域'
    parameter_name = 'Province'

    def lookups(self , request , model_admin):
        contracts = Province.objects.all( )
        value = [i.name for i in contracts]
        label = ['年龄段:' + i.name for i in contracts]
        return tuple( zip( value , label ) )

    def queryset(self , request , queryset):
        if self.value( ) is None:
            return queryset
        else:
            return queryset.filter( province = self.value( ) )


class AnamnesisListFilter( admin.SimpleListFilter ):
    '''实验数据中的合同'''
    title = '疾病'
    parameter_name = 'Anamnesis'

    def lookups(self , request , model_admin):
        contracts = ExperimentalData.objects.all( )
        value = [i.anamnesis for i in contracts if (i.anamnesis is not None and i.anamnesis is not "")]
        label = ['疾病:' + i.anamnesis for i in contracts if (i.anamnesis is not None and i.anamnesis is not "")]
        return tuple( zip( np.unique( value ) , np.unique( label ) ) )

    def queryset(self , request , queryset):
        if self.value( ) is None:
            return queryset
        else:
            return queryset.filter( anamnesis = self.value( ) )


@admin.register( ExperimentalData )
class ExperimentalDataAdmin( ImportExportActionModelAdmin , admin.ModelAdmin ):
    list_display = ('id' , 'contract_number' , 'sample_number' , 'internal_number' , 'carbon_source' , 'group' ,
                    'intervention' , 'carbon_source_zh' , 'recordNo' , 'name' , 'gender' , 'age' , 'age_sgement' ,
                    'province' , 'height' , 'weight' , 'fbj' , 'blood_pressure' , 'trioxypurine' , 'triglyceride' ,
                    'anamnesis' , 'staging' , 'therapies' , 'is_status')
    list_display_links = ('sample_number' ,)
    ordering = ('-id' ,)
    view_on_site = False
    list_max_show_all = 100
    list_per_page = 20
    list_filter = (
    'is_status' , 'carbon_source' , 'gender' , ContractListFilter , AnamnesisListFilter , ProvinceListFilter ,
    AgeListFilter)
    search_fields = ('note' ,'age')
    import_export_args = {'import_resource_class': ExperimentalDataResource ,
                          'export_resource_class': ExperimentalDataResource}
    resource_class = ExperimentalDataResource
    form = ContractForm
    # list_editable =
    actions = ['make_finish' , 'export_admin_action']
    exclude = (
        'isovaleric1' , 'isovaleric1_status' , 'isovaleric1_reference_range' , 'isovaleric2' , 'isovaleric2_status' ,
        'isovaleric2_reference_range' , 'isovaleric3' , 'isovaleric3_status' , 'isovaleric3_reference_range' ,
        'carbon_source_zh' , 'genus_zh')

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

    def save_model(self , request , obj , form , change):

        if obj.acetic_acid is not None:
            obj.acetic_acid = float( obj.acetic_acid )
        if obj.propionic is not None:
            obj.propionic = float( obj.propionic )
        if obj.butyric is not None:
            obj.butyric = float( obj.butyric )
        if obj.isobutyric_acid is not None:
            obj.isobutyric_acid = float( obj.isobutyric_acid )
        if obj.valeric is not None:
            obj.valeric = float( obj.valeric )
        if obj.isovaleric is not None:
            obj.isovaleric = float( obj.isovaleric )
        if (obj.acetic_acid is not None) and (obj.propionic is not None) and (obj.butyric is not None) and (
                obj.isobutyric_acid is not None) and (obj.valeric is not None) and (obj.isovaleric is not None):
            obj.total_acid = float( obj.acetic_acid ) + float( obj.propionic ) + float( obj.butyric ) + float(
                obj.isobutyric_acid ) + float( obj.valeric ) + \
                             float( obj.isovaleric )
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

        obj.save( )

    def make_finish(self , request , queryset):
        i = 0  # 提交成功的数量
        n = 0  # 提交过的数量
        t = 0  # 选中的总数量
        for obj in queryset:
            t += 1
            if obj.is_status == 0:
                obj.is_status = 1
                obj.save( )
                i += 1
            else:
                n += 1
        self.message_user( request , '选择%s条信息，完成操作%s条，不操作%s条' % (t , i , n) , level = messages.SUCCESS )

    make_finish.short_description = '标记完成'


class MaterialForm( forms.ModelForm ):
    class Meta:
        model = Material
        exclude = ("" ,)

    def clean_carbon_source(self , exclude=None):
        if Carbon.objects.filter( cid = self.cleaned_data ["carbon_source"].strip( ) ).count( ) == 0:
            raise forms.ValidationError( self.cleaned_data ["carbon_source"].strip( ) + "检测碳源编号不存在,请到基础数据管理核查" )
        else:
            return self.cleaned_data ["carbon_source"]


@admin.register( Material )
class MaterialAdmin( ImportExportActionModelAdmin , admin.ModelAdmin ):
    list_display = ('id' , 'carbon_source' , 'carbon_source_zh' , 'name' , 'brand' , 'artNo' , 'batch' ,
                    'create_date')
    list_display_links = ('name' ,)
    readonly_fields = ('carbon_source_zh' ,)
    # ordering = ('-create_date' ,)
    view_on_site = False
    list_max_show_all = 100
    list_per_page = 20
    list_filter = ('carbon_source' ,)
    search_fields = ('name' ,)
    form = MaterialForm

    def get_changeform_initial_data(self , request):
        initial = super( ).get_changeform_initial_data( request )
        initial ['writer'] = request.user.last_name + ' ' + request.user.first_name
        return initial

    def save_model(self , request , obj , form , change):
        if obj.carbon_source_zh is None:
            obj.carbon_source_zh = Carbon.objects.get( cid = obj.carbon_source ).name
        if obj.historys is None:
            obj.historys = ';碳源:' + obj.carbon_source + ';实验:' + datetime.date.today( ).__str__( )
        else:
            obj.historys = obj.historys + '\n' + ';碳源:' + obj.carbon_source + ';时间:' + datetime.date.today( ).__str__( )
        obj.save( )
