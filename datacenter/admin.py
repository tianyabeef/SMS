from django.contrib import admin
from django import forms
from import_export.admin import ImportExportActionModelAdmin

from datacenter.models import DataInformation
# from datacenter.models import Book,Author,Publisher



@admin.register( DataInformation )
class DataInformationAdmin( ImportExportActionModelAdmin , admin.ModelAdmin ):
    pass
# @admin.register( Book )
# class BookAdmin( ImportExportActionModelAdmin , admin.ModelAdmin ):
#     def save_model(self, request, obj, form, change):
#         tm = Book.objects.all()
#         raise forms.ValidationError( tm )
# @admin.register( Author )
# class AuthorAdmin( ImportExportActionModelAdmin , admin.ModelAdmin ):
#     pass
# @admin.register( Publisher )
# class PublisherAdmin( ImportExportActionModelAdmin , admin.ModelAdmin ):
#     pass