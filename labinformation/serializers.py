from rest_framework import serializers



class CarbonSerializer(serializers.Serializer):
    cid = serializers.CharField(  )
    name = serializers.CharField(  )
    english_name = serializers.CharField(  )  # 在渲染word报告时使用
    ratio = serializers.CharField(  )
    create_date = serializers.DateField(  )
    historys = serializers.CharField(  )
    writer = serializers.CharField(  )
    note = serializers.CharField(  )

class GenusSerializer(serializers.Serializer):
    taxid = serializers.IntegerField(  )
    china_name = serializers.CharField(  )
    english_name = serializers.CharField(  )
    create_date = serializers.DateField(  )
    historys = serializers.CharField(  )
    writer = serializers.CharField( )
    note = serializers.CharField(  )


class QpcrIndexesSerializer(serializers.Serializer):
    sample_number = serializers.CharField(read_only = True)
    carbon_source = CarbonSerializer(read_only=True)			# 嵌套序列化器
    genus = GenusSerializer(read_only = True)# 嵌套序列化器
    STATUS_CHOICES = (
        (0 , '偏高') ,
        (1 , '正常') ,
        (2 , '偏低') ,
    )
    TEST_CHOICES = (
        (0 , '待检测') ,
        (1 , '完成') ,
        (2 , '完成并判读') ,
    )
    ct = serializers.DecimalField( max_digits = 12 , decimal_places = 4 ) 
    concentration = serializers.DecimalField( max_digits = 12 , decimal_places = 4 ) 
    concentration_reference_range = serializers.CharField(  )
    concentration_status = serializers.IntegerField(  )
    formula_number = serializers.CharField(  )


class ScfasIndexesSerializer(serializers.Serializer):
    STATUS_CHOICES = (
        (0 , '偏高') ,
        (1 , '正常') ,
        (2 , '偏低') ,
    )
    TEST_CHOICES = (
        (0 , '待检测') ,
        (1 , '完成') ,
        (2 , '完成并判读') ,
    )
    sample_number = serializers.CharField( )
    carbon_source = CarbonSerializer(read_only = True )
    genus = GenusSerializer( read_only = True )
    total_acid = serializers.DecimalField( max_digits = 12 , decimal_places = 4 ) 
    total_acid_status = serializers.IntegerField(  )
    total_acid_reference_range = serializers.CharField(  )

    acetic_acid = serializers.DecimalField( max_digits = 12 , decimal_places = 4 ) 
    acetic_acid_status = serializers.IntegerField(  )
    acetic_acid_reference_range = serializers.CharField(  )
    propionic = serializers.DecimalField( max_digits = 12 , decimal_places = 4 ) 
    propionic_status = serializers.IntegerField(  )
    propionic_reference_range = serializers.CharField(  )
    butyric = serializers.DecimalField( max_digits = 12 , decimal_places = 4 ) 
    butyric_status = serializers.IntegerField(  )
    butyric_reference_range = serializers.CharField(  )
    isobutyric_acid = serializers.DecimalField( max_digits = 12 , decimal_places = 4 ) 
    isobutyric_acid_status = serializers.IntegerField(  )
    isobutyric_acid_reference_range = serializers.CharField(  )
    valeric = serializers.DecimalField( max_digits = 12 , decimal_places = 4 ) 
    valeric_status = serializers.IntegerField(  )
    valeric_reference_range = serializers.CharField(  )
    isovaleric = serializers.DecimalField( max_digits = 12 , decimal_places = 4 ) 
    isovaleric_status = serializers.IntegerField(  )
    isovaleric_reference_range = serializers.CharField(  )
    isovaleric1 = serializers.DecimalField( max_digits = 12 , decimal_places = 4 ) 
    isovaleric1_status = serializers.IntegerField(  )
    isovaleric1_reference_range = serializers.CharField(  )
    isovaleric2 = serializers.DecimalField( max_digits = 12 , decimal_places = 4 ) 
    isovaleric2_status = serializers.IntegerField( )
    isovaleric2_reference_range = serializers.CharField(  )
    isovaleric3 = serializers.DecimalField( max_digits = 12 , decimal_places = 4 ) 
    isovaleric3_status = serializers.IntegerField(  )
    isovaleric3_reference_range = serializers.CharField(  )
    acid_first = serializers.DecimalField( max_digits = 12 , decimal_places = 4 ) 
    acid_first_status = serializers.IntegerField(  )
    acid_first_reference_range = serializers.CharField(  )
    acid_second = serializers.DecimalField( max_digits = 12 , decimal_places = 4 ) 
    acid_second_status = serializers.IntegerField(  )
    acid_second_reference_range = serializers.CharField(  )



class DegradationIndexesSerializer(serializers.Serializer):
    STATUS_CHOICES = (
        (0 , '偏高') ,
        (1 , '正常') ,
        (2 , '偏低') ,
    )
    TEST_CHOICES = (
        (0 , '待检测') ,
        (1 , '完成') ,
        (2 , '完成并判读') ,
    )
    sample_number = serializers.CharField(  )
    carbon_source = CarbonSerializer( read_only = True)
    genus = GenusSerializer( read_only = True )

    degradation = serializers.DecimalField( max_digits = 12 , decimal_places = 4 ) 
    degradation_status = serializers.IntegerField(  )
    degradation_reference_range = serializers.CharField(  )
    gas = serializers.DecimalField( max_digits = 12 , decimal_places = 4 ) 
    gas_status = serializers.IntegerField(  )
    gas_reference_range = serializers.CharField(  )

