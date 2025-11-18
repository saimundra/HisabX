from rest_framework import serializers
from .models import AuditReport, ReportTemplate, ReportData
from bills.models import Category

class ReportTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportTemplate
        fields = '__all__'

class ReportDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportData
        fields = '__all__'

class AuditReportSerializer(serializers.ModelSerializer):
    data = ReportDataSerializer(many=True, read_only=True)
    categories = serializers.PrimaryKeyRelatedField(many=True, queryset=Category.objects.all(), required=False)
    generated_date = serializers.DateTimeField(source='created_at', read_only=True)
    template = serializers.PrimaryKeyRelatedField(queryset=ReportTemplate.objects.all(), required=False, allow_null=True)
    
    class Meta:
        model = AuditReport
        fields = [
            'id', 'title', 'description', 'start_date', 'end_date', 
            'categories', 'vendors', 'min_amount', 'max_amount',
            'status', 'export_format', 'file_path', 'total_bills', 
            'total_amount', 'created_at', 'completed_at', 'data',
            'generated_date', 'template'
        ]
        read_only_fields = ['user', 'created_at', 'completed_at']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)