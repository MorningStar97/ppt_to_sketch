from rest_framework import serializers
from .models import ConversionTask

class ConversionTaskSerializer(serializers.ModelSerializer):
    ppt_filename = serializers.ReadOnlyField()
    sketch_filename = serializers.ReadOnlyField()
    
    class Meta:
        model = ConversionTask
        fields = [
            'id', 'ppt_file', 'sketch_file', 'status', 
            'created_at', 'updated_at', 'error_message',
            'ppt_filename', 'sketch_filename'
        ]
        read_only_fields = ['id', 'status', 'created_at', 'updated_at', 'sketch_file', 'error_message']

class ConversionTaskCreateSerializer(serializers.ModelSerializer):
    ppt_filename = serializers.ReadOnlyField()
    
    class Meta:
        model = ConversionTask
        fields = ['id', 'ppt_file', 'status', 'created_at', 'ppt_filename']
        read_only_fields = ['id', 'status', 'created_at', 'ppt_filename'] 