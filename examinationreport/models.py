from django.db import models
from examinationsample.models import Sample
from django.utils.html import format_html
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator , MaxValueValidator

# Create your models here.
class Reports( models.Model ):
    STATUS_CHOICES = (
        (0 , '待处理') ,
        (1, '完成同步'),
        (2 , '完成报告') ,
    )
    sample_number = models.CharField( verbose_name = '样本编号' , max_length = 255 , unique = True ) # 可以到样本管理中调整模板
    word_report = models.FileField( verbose_name = 'word报告' , upload_to = "uploads/examinationsample/%Y/%m" ,
                                    null = True , blank = True )
    pdf_report = models.FileField( verbose_name = 'pdf报告' , upload_to = "uploads/examinationsample/%Y/%m" ,
                                   null = True , blank = True )
    point = models.IntegerField( verbose_name = '小数点位数' , default = 2 , null = True , blank = True ,
                                 validators = [MinValueValidator( 0 ) , MaxValueValidator( 100 )] ) # 报告中的小数点位数控制
    report_testing_date = models.DateField( verbose_name = "报告时间" , null = True , blank = True )
    report_user = models.CharField( verbose_name = "出具人" , max_length = 255 , blank = True , null = True )

    note = models.TextField( verbose_name = '备注' , max_length = 255 , null = True , blank = True )
    is_status = models.IntegerField( verbose_name = '状态' , choices = STATUS_CHOICES , default = 0 , null = True ,
                                     blank = True )
    class Meta:
        verbose_name = '检测报告'

        verbose_name_plural = verbose_name

    def __str__(self):
        return '%s' % self.sample_number

    def file_link_word(self):
        if self.word_report:
            return format_html(
                "<a href='{0}'>下载</a>".format( self.word_report.url ) )

        else:
            return '未上传'

    file_link_word.allow_tags = True
    file_link_word.short_description = 'word版'

    def file_link_pdf(self):
        if self.pdf_report:
            return format_html(
                "<a href='{0}'>下载</a>".format( self.pdf_report.url ) )

        else:
            return '未上传'

    file_link_pdf.allow_tags = True
    file_link_pdf.short_description = 'pdf版'


