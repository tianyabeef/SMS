from django.contrib import admin
from django import forms
from import_export.admin import ImportExportActionModelAdmin

from datacenter.models import DataInformation


# from datacenter.models import Book,Author,Publisher


@admin.register( DataInformation )
class DataInformationAdmin( ImportExportActionModelAdmin , admin.ModelAdmin ):
    pass
