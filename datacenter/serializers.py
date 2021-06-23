from rest_framework import serializers
from .models import Book

class PublisherSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField(max_length=32)

class AutherSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(max_length=32)

class BookSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)  # required=False 指明反序时（前端提交数据过来）不做校验
    title = serializers.CharField(max_length=32)
    pub_time = serializers.DateField()
    category = serializers.CharField(source='get_category_display', read_only=True)
    # 外键关系的序列化是嵌套的序列化对象；内部通过外键关系的id找到publisher对象，再使用PublisherSerializer(publisher对象)
    publisher = PublisherSerializer(read_only=True)			# 嵌套序列化器
    authors = AutherSerializer(many=True, read_only=True)  # 多对多关系需要加上参数：many = True
    # read_only:指明该字段只做序列化，反序列化时不走该字段；那么反序列化时就必须重新指定字段名
    # write_only:指明该字段只做反序列化
    post_category = serializers.IntegerField(write_only=True)
    publisher_id = serializers.IntegerField(write_only=True)
    author_list = serializers.ListField(write_only=True)
