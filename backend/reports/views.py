from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count, Q
from datetime import datetime, timedelta
from bills.models import Bill, Category
from .models import AuditReport, ReportTemplate, ReportData
from .serializers import AuditReportSerializer
from .utils.excel_generator import export_report_response
import logging

logger = logging.getLogger(__name__)

class ReportViewSet(viewsets.ModelViewSet):
    serializer_class = AuditReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return AuditReport.objects.filter(user=self.request.user)
    
    def list(self, request):
        """List all reports for the user"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def generate_report(self, request):
        """Generate a new report"""
        data = request.data
        
        # Parse dates
        try:
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        except (KeyError, ValueError):
            return Response({'error': 'Valid start_date and end_date required'}, status=400)
        
        # Get bills within date range
        bills_query = Bill.objects.filter(
            user=request.user,
            created_at__date__range=[start_date, end_date]
        )
        
        # Apply filters
        if data.get('categories'):
            bills_query = bills_query.filter(category__id__in=data['categories'])
        
        if data.get('vendors'):
            vendor_list = [v.strip() for v in data['vendors'].split(',')]
            bills_query = bills_query.filter(vendor__icontains=vendor_list[0])  # Simplified for demo
        
        if data.get('min_amount'):
            bills_query = bills_query.filter(amount__gte=data['min_amount'])
        
        if data.get('max_amount'):
            bills_query = bills_query.filter(amount__lte=data['max_amount'])
        
        # Generate report data
        report_data = bills_query.values(
            'category__name', 'category__type', 'category__color'
        ).annotate(
            total_amount=Sum('amount'),
            bill_count=Count('id')
        ).order_by('-total_amount')
        
        # Calculate totals
        total_bills = bills_query.count()
        total_amount = bills_query.aggregate(total=Sum('amount'))['total'] or 0
        
        report_summary = {
            'total_bills': total_bills,
            'total_amount': float(total_amount),
            'date_range': f"{start_date} to {end_date}",
            'categories': list(report_data),
            'uncategorized_bills': bills_query.filter(category__isnull=True).count()
        }
        
        return Response(report_summary)
    
    @action(detail=False, methods=['post'])
    def export_report(self, request):
        """Export report in specified format"""
        data = request.data
        
        # Parse dates and generate data (similar to above)
        try:
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        except (KeyError, ValueError):
            return Response({'error': 'Valid start_date and end_date required'}, status=400)
        
        bills_query = Bill.objects.filter(
            user=request.user,
            created_at__date__range=[start_date, end_date]
        )
        
        report_data = list(bills_query.values(
            'category__name', 'category__type'
        ).annotate(
            total_amount=Sum('amount'),
            bill_count=Count('id')
        ).order_by('-total_amount'))
        
        # Export settings
        export_format = data.get('format', 'EXCEL')
        filename = f"expense_report_{start_date}_{end_date}"
        report_title = f"Expense Report: {start_date} to {end_date}"
        
        return export_report_response(
            report_data=report_data,
            format_type=export_format,
            filename=filename,
            report_title=report_title,
            user_name=request.user.username
        )
    
    @action(detail=False, methods=['get'])
    def monthly_summary(self, request):
        """Get monthly spending summary for the current year"""
        current_year = datetime.now().year
        monthly_data = []
        
        for month in range(1, 13):
            month_start = datetime(current_year, month, 1).date()
            if month == 12:
                month_end = datetime(current_year + 1, 1, 1).date() - timedelta(days=1)
            else:
                month_end = datetime(current_year, month + 1, 1).date() - timedelta(days=1)
            
            monthly_total = Bill.objects.filter(
                user=request.user,
                created_at__date__range=[month_start, month_end],
                amount__isnull=False
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            monthly_bills = Bill.objects.filter(
                user=request.user,
                created_at__date__range=[month_start, month_end]
            ).count()
            
            monthly_data.append({
                'month': month,
                'month_name': month_start.strftime('%B'),
                'total_amount': float(monthly_total),
                'bill_count': monthly_bills
            })
        
        return Response(monthly_data)
