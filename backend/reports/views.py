from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum, Count, Q
from django.http import HttpResponse
from datetime import datetime, timedelta
from bills.models import Bill, Category
from .models import AuditReport, ReportTemplate, ReportData
from .serializers import AuditReportSerializer
from .utils.excel_generator import export_report_response
from .financial_statements import FinancialStatementsService
from .nrb_financial_statements import NRBFinancialStatements
from .report_export import ReportExporter
from .nepal_balance_sheet_exporter import NepalBalanceSheetExporter
from .nepal_income_statement_exporter import NepalIncomeStatementExporter
from .nepal_cash_flow_exporter import NepalCashFlowExporter
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


class BalanceSheetView(APIView):
    """Balance Sheet API endpoint"""
    # Use default authentication_classes from REST_FRAMEWORK settings (same as MonthlyReportView)
    permission_classes = [permissions.IsAuthenticated]
    
    def dispatch(self, request, *args, **kwargs):
        """Override dispatch to catch any issues"""
        logger.error(f"=== BalanceSheetView.dispatch() START ===")
        logger.error(f"Method: {request.method}, Path: {request.path}")
        try:
            result = super().dispatch(request, *args, **kwargs)
            logger.error(f"=== BalanceSheetView.dispatch() SUCCESS ===")
            return result
        except Exception as e:
            logger.error(f"=== BalanceSheetView.dispatch() EXCEPTION: {e} ===")
            logger.exception("Full traceback:")
            raise
    
    def initial(self, request, *args, **kwargs):
        """Called before the view method is called - after authentication"""
        # Check if format is pdf/excel - if so, skip DRF content negotiation
        # because we handle it ourselves in get()
        format_param = request.query_params.get('format', 'json')
        if format_param in ['pdf', 'excel']:
            # Skip content negotiation for these formats - we handle them manually
            # Just do authentication and permission checks
            self.perform_authentication(request)
            self.check_permissions(request)
            self.check_throttles(request)
            return
        
        # For JSON format, use normal DRF flow
        super().initial(request, *args, **kwargs)
    
    def get(self, request):
        """Get Balance Sheet"""
        # Log at the very beginning to confirm view is being called
        logger.error(f"=== BalanceSheetView.get() CALLED ===")
        logger.error(f"User: {request.user}, Authenticated: {request.user.is_authenticated}")
        logger.error(f"Request path: {request.path}, Full path: {request.get_full_path()}")
        logger.error(f"Query params: {request.query_params}")
        logger.info(f"BalanceSheetView.get() called - user={request.user}, params={request.query_params}")
        logger.info(f"Request path: {request.path}, Method: {request.method}")
        
        try:
            service = FinancialStatementsService(request.user)
            
            # Get as_of_date from query params or use today
            as_of_date_str = request.query_params.get('as_of_date')
            if as_of_date_str:
                try:
                    as_of_date = datetime.strptime(as_of_date_str, '%Y-%m-%d').date()
                except ValueError:
                    logger.error(f"Invalid date format: {as_of_date_str}")
                    return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=400)
            else:
                as_of_date = datetime.now().date()
            
            logger.info(f"Generating balance sheet for user={request.user} as_of_date={as_of_date}")
            
            try:
                balance_sheet = service.get_balance_sheet(as_of_date)
                logger.info(f"Balance sheet generated successfully: {balance_sheet.get('as_of_date')}")
            except Exception as e:
                logger.exception("Failed to generate balance sheet for user=%s as_of_date=%s", request.user, as_of_date_str)
                return Response({'error': 'Failed to generate balance sheet', 'details': str(e)}, status=500)
        except Exception as e:
            logger.exception("Unexpected error in BalanceSheetView.get()")
            return Response({'error': 'Unexpected error', 'details': str(e)}, status=500)
        
        # Export format
        export_format = request.query_params.get('format', 'json')
        comparison_date = request.query_params.get('comparison_date')  # Optional previous year date
        
        if export_format in ['excel', 'pdf']:
            try:
                if export_format == 'pdf':
                    # Use Nepal standard format for PDF
                    nepal_exporter = NepalBalanceSheetExporter(
                        user=request.user,
                        company_name=request.user.get_full_name() or request.user.username
                    )
                    return nepal_exporter.export_to_pdf(as_of_date, comparison_date)
                else:  # excel
                    exporter = ReportExporter(request.user)
                    response = exporter.export_balance_sheet_excel(balance_sheet)
                    logger.info(f"Successfully exported balance sheet for user={request.user} format={export_format}")
                    return response
            except Exception as e:
                logger.exception("Failed to export balance sheet for user=%s format=%s", request.user, export_format)
                # Return error as JSON response (frontend will handle this)
                return Response({
                    'error': 'Failed to export balance sheet',
                    'details': str(e),
                    'format': export_format
                }, status=500)
        
        # Convert Decimal to float for JSON serialization
        return Response(self._serialize_financial_data(balance_sheet))
    
    def _serialize_financial_data(self, data):
        """Convert Decimal values to float for JSON serialization"""
        from decimal import Decimal
        import datetime
        
        if isinstance(data, dict):
            return {k: self._serialize_financial_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._serialize_financial_data(item) for item in data]
        elif isinstance(data, Decimal):
            return float(data)
        elif isinstance(data, (datetime.date, datetime.datetime)):
            return str(data)
        else:
            return data


class IncomeStatementView(APIView):
    """Income Statement (Profit & Loss) API endpoint"""
    permission_classes = [permissions.IsAuthenticated]
    
    def initial(self, request, *args, **kwargs):
        """Called before the view method is called - after authentication"""
        # Check if format is pdf/excel - if so, skip DRF content negotiation
        # because we handle it ourselves in get()
        format_param = request.query_params.get('format', 'json')
        if format_param in ['pdf', 'excel']:
            # Skip content negotiation for these formats - we handle them manually
            # Just do authentication and permission checks
            self.perform_authentication(request)
            self.check_permissions(request)
            self.check_throttles(request)
            return
        
        # For JSON format, use normal DRF flow
        super().initial(request, *args, **kwargs)
    
    def get(self, request):
        """Get Income Statement"""
        service = FinancialStatementsService(request.user)

        # Get date range from query params
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')

        if not start_date_str or not end_date_str:
            return Response({
                'error': 'start_date and end_date required (format: YYYY-MM-DD)'
            }, status=400)

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=400)

        # Get comparison period dates (for previous year)
        comparison_start_str = request.query_params.get('comparison_start_date')
        comparison_end_str = request.query_params.get('comparison_end_date')
        
        previous_period_data = None
        if comparison_start_str and comparison_end_str:
            try:
                comparison_start = datetime.strptime(comparison_start_str, '%Y-%m-%d').date()
                comparison_end = datetime.strptime(comparison_end_str, '%Y-%m-%d').date()
                previous_period_data = service.get_income_statement(comparison_start, comparison_end)
            except ValueError:
                logger.warning("Invalid comparison date format for user=%s", request.user)
            except Exception as e:
                logger.exception("Failed to generate comparison period income statement for user=%s", request.user)

        try:
            income_statement = service.get_income_statement(start_date, end_date)
        except Exception as e:
            logger.exception("Failed to generate income statement for user=%s start=%s end=%s", request.user, start_date_str, end_date_str)
            return Response({'error': 'Failed to generate income statement', 'details': str(e)}, status=500)

        # Export format
        export_format = request.query_params.get('format', 'json')
        try:
            if export_format == 'excel':
                exporter = ReportExporter(request.user)
                return exporter.export_income_statement_excel(income_statement)
            elif export_format == 'pdf':
                # Use Nepal Standard format for PDF
                nepal_exporter = NepalIncomeStatementExporter(request.user)
                return nepal_exporter.export_to_pdf(income_statement, previous_period_data)
        except Exception as e:
            logger.exception("Failed to export income statement for user=%s format=%s", request.user, export_format)
            return Response({'error': 'Failed to export income statement', 'details': str(e)}, status=500)

        return Response(self._serialize_financial_data(income_statement))
    
    def _serialize_financial_data(self, data):
        """Convert Decimal values to float for JSON serialization"""
        from decimal import Decimal
        import datetime
        
        if isinstance(data, dict):
            return {k: self._serialize_financial_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._serialize_financial_data(item) for item in data]
        elif isinstance(data, Decimal):
            return float(data)
        elif isinstance(data, (datetime.date, datetime.datetime)):
            return str(data)
        else:
            return data


class TrialBalanceView(APIView):
    """Trial Balance API endpoint"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get Trial Balance"""
        service = FinancialStatementsService(request.user)
        
        as_of_date_str = request.query_params.get('as_of_date')
        if as_of_date_str:
            try:
                as_of_date = datetime.strptime(as_of_date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=400)
        else:
            as_of_date = datetime.now().date()
        
        trial_balance = service.get_trial_balance(as_of_date)
        return Response(self._serialize_financial_data(trial_balance))
    
    def _serialize_financial_data(self, data):
        """Convert Decimal values to float for JSON serialization"""
        from decimal import Decimal
        import datetime
        
        if isinstance(data, dict):
            return {k: self._serialize_financial_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._serialize_financial_data(item) for item in data]
        elif isinstance(data, Decimal):
            return float(data)
        elif isinstance(data, (datetime.date, datetime.datetime)):
            return str(data)
        else:
            return data


class MonthlyReportView(APIView):
    """Monthly Report API endpoint"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get monthly financial reports"""
        service = FinancialStatementsService(request.user)
        
        year = int(request.query_params.get('year', datetime.now().year))
        month = int(request.query_params.get('month', datetime.now().month))
        
        if not (1 <= month <= 12):
            return Response({'error': 'Month must be between 1 and 12'}, status=400)
        
        monthly_data = service.get_monthly_reports(year, month)
        return Response(self._serialize_financial_data(monthly_data))
    
    def _serialize_financial_data(self, data):
        """Convert Decimal values to float for JSON serialization"""
        from decimal import Decimal
        import datetime
        
        if isinstance(data, dict):
            return {k: self._serialize_financial_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._serialize_financial_data(item) for item in data]
        elif isinstance(data, Decimal):
            return float(data)
        elif isinstance(data, (datetime.date, datetime.datetime)):
            return str(data)
        else:
            return data


class QuarterlyReportView(APIView):
    """Quarterly Report API endpoint"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get quarterly financial reports"""
        service = FinancialStatementsService(request.user)
        
        year = int(request.query_params.get('year', datetime.now().year))
        quarter = int(request.query_params.get('quarter', 1))
        
        if not (1 <= quarter <= 4):
            return Response({'error': 'Quarter must be between 1 and 4'}, status=400)
        
        quarterly_data = service.get_quarterly_reports(year, quarter)
        return Response(self._serialize_financial_data(quarterly_data))
    
    def _serialize_financial_data(self, data):
        """Convert Decimal values to float for JSON serialization"""
        from decimal import Decimal
        import datetime
        
        if isinstance(data, dict):
            return {k: self._serialize_financial_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._serialize_financial_data(item) for item in data]
        elif isinstance(data, Decimal):
            return float(data)
        elif isinstance(data, (datetime.date, datetime.datetime)):
            return str(data)
        else:
            return data


class YearlyReportView(APIView):
    """Yearly Report API endpoint"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get yearly financial reports"""
        service = FinancialStatementsService(request.user)
        
        year = int(request.query_params.get('year', datetime.now().year))
        yearly_data = service.get_yearly_reports(year)
        return Response(self._serialize_financial_data(yearly_data))
    
    def _serialize_financial_data(self, data):
        """Convert Decimal values to float for JSON serialization"""
        from decimal import Decimal
        import datetime
        
        if isinstance(data, dict):
            return {k: self._serialize_financial_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._serialize_financial_data(item) for item in data]
        elif isinstance(data, Decimal):
            return float(data)
        elif isinstance(data, (datetime.date, datetime.datetime)):
            return str(data)
        else:
            return data


class TransactionExportView(APIView):
    """Transaction Export API endpoint"""
    permission_classes = [permissions.IsAuthenticated]
    
    def initial(self, request, *args, **kwargs):
        """Called before the view method is called - after authentication"""
        # This view always exports Excel, so skip DRF content negotiation
        self.perform_authentication(request)
        self.check_permissions(request)
        self.check_throttles(request)
        return
    
    def get(self, request):
        """Export transaction ledger for auditing"""
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        
        bills = Bill.objects.filter(user=request.user).order_by('bill_date')
        
        if start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                bills = bills.filter(bill_date__gte=start_date, bill_date__lte=end_date)
            except ValueError:
                return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=400)
        
        # Log bill count for debugging
        bill_count = bills.count()
        logger.info(f"Exporting {bill_count} transactions for user {request.user.username}")
        
        exporter = ReportExporter(request.user)
        return exporter.export_transactions_excel(bills)


# NRB Format Financial Statements Views
class NRBBalanceSheetView(APIView):
    """Nepal Rastra Bank format Balance Sheet"""
    permission_classes = [permissions.IsAuthenticated]
    
    def initial(self, request, *args, **kwargs):
        """Called before the view method is called - after authentication"""
        # Check if format is pdf/excel - if so, skip DRF content negotiation
        format_param = request.query_params.get('format', 'json')
        if format_param in ['pdf', 'excel']:
            self.perform_authentication(request)
            self.check_permissions(request)
            self.check_throttles(request)
            return
        super().initial(request, *args, **kwargs)
    
    def get(self, request):
        try:
            as_of_date = request.query_params.get('as_of_date')
            export_format = request.query_params.get('format', 'json')
            comparison_date = request.query_params.get('comparison_date')  # Optional previous year date
            
            if as_of_date:
                end_date = datetime.strptime(as_of_date, '%Y-%m-%d').date()
                start_date = end_date.replace(month=1, day=1)
            else:
                end_date = datetime.now().date()
                start_date = end_date.replace(month=1, day=1)
            
            # Use new Nepal format exporter for PDF
            if export_format == 'pdf':
                nepal_exporter = NepalBalanceSheetExporter(
                    user=request.user,
                    company_name=f"{request.user.username}'s Business"
                )
                return nepal_exporter.export_to_pdf(end_date, comparison_date)
            
            # For JSON and Excel, use existing NRB format
            nrb_statements = NRBFinancialStatements(
                user=request.user,
                company_name=f"{request.user.username}'s Business",
                start_date=start_date,
                end_date=end_date
            )
            
            balance_sheet = nrb_statements.get_balance_sheet()
            
            if export_format == 'excel':
                exporter = ReportExporter(request.user)
                excel_file = exporter.export_balance_sheet_excel(balance_sheet)
                response = HttpResponse(
                    excel_file,
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = f'attachment; filename="balance_sheet_nrb_{as_of_date}.xlsx"'
                return response
            
            return Response(balance_sheet)
            
        except Exception as e:
            logger.error(f"Error generating NRB balance sheet: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NRBIncomeStatementView(APIView):
    """Nepal Rastra Bank format Income Statement"""
    permission_classes = [permissions.IsAuthenticated]
    
    def initial(self, request, *args, **kwargs):
        """Called before the view method is called - after authentication"""
        # Check if format is pdf/excel - if so, skip DRF content negotiation
        format_param = request.query_params.get('format', 'json')
        if format_param in ['pdf', 'excel']:
            self.perform_authentication(request)
            self.check_permissions(request)
            self.check_throttles(request)
            return
        super().initial(request, *args, **kwargs)
    
    def get(self, request):
        try:
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            export_format = request.query_params.get('format', 'json')
            
            if start_date and end_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            else:
                end_date = datetime.now().date()
                start_date = end_date.replace(month=1, day=1)
            
            nrb_statements = NRBFinancialStatements(
                user=request.user,
                company_name=f"{request.user.username}'s Business",
                start_date=start_date,
                end_date=end_date
            )
            
            income_statement = nrb_statements.get_profit_loss_statement()
            
            if export_format == 'pdf':
                exporter = ReportExporter(request.user)
                pdf_file = exporter.export_income_statement_pdf(income_statement)
                response = HttpResponse(pdf_file, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="income_statement_nrb_{start_date}_{end_date}.pdf"'
                return response
            
            elif export_format == 'excel':
                exporter = ReportExporter(request.user)
                excel_file = exporter.export_income_statement_excel(income_statement)
                response = HttpResponse(
                    excel_file,
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = f'attachment; filename="income_statement_nrb_{start_date}_{end_date}.xlsx"'
                return response
            
            return Response(income_statement)
            
        except Exception as e:
            logger.error(f"Error generating NRB income statement: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NRBCashFlowStatementView(APIView):
    """Nepal Rastra Bank format Cash Flow Statement"""
    permission_classes = [permissions.IsAuthenticated]
    
    def initial(self, request, *args, **kwargs):
        """Called before the view method is called - after authentication"""
        # Check if format is pdf/excel - if so, skip DRF content negotiation
        format_param = request.query_params.get('format', 'json')
        if format_param in ['pdf', 'excel']:
            self.perform_authentication(request)
            self.check_permissions(request)
            self.check_throttles(request)
            return
        super().initial(request, *args, **kwargs)
    
    def get(self, request):
        try:
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            export_format = request.query_params.get('format', 'json')
            
            # Get comparison period dates (for previous year)
            comparison_start_str = request.query_params.get('comparison_start_date')
            comparison_end_str = request.query_params.get('comparison_end_date')
            
            if start_date and end_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            else:
                end_date = datetime.now().date()
                start_date = end_date.replace(month=1, day=1)
            
            # Generate current period cash flow
            nrb_statements = NRBFinancialStatements(
                user=request.user,
                company_name=f"{request.user.username}'s Business",
                start_date=start_date,
                end_date=end_date
            )
            
            cash_flow = nrb_statements.get_cash_flow_statement()
            
            # Generate previous period cash flow (if comparison dates provided)
            previous_cash_flow = None
            if comparison_start_str and comparison_end_str:
                try:
                    comparison_start = datetime.strptime(comparison_start_str, '%Y-%m-%d').date()
                    comparison_end = datetime.strptime(comparison_end_str, '%Y-%m-%d').date()
                    
                    prev_nrb_statements = NRBFinancialStatements(
                        user=request.user,
                        company_name=f"{request.user.username}'s Business",
                        start_date=comparison_start,
                        end_date=comparison_end
                    )
                    previous_cash_flow = prev_nrb_statements.get_cash_flow_statement()
                except ValueError:
                    logger.warning("Invalid comparison date format for user=%s", request.user)
                except Exception as e:
                    logger.exception("Failed to generate comparison period cash flow for user=%s", request.user)
            
            if export_format == 'pdf':
                # Use Nepal Standard format for PDF
                nepal_exporter = NepalCashFlowExporter(request.user)
                return nepal_exporter.export_to_pdf(cash_flow, previous_cash_flow)
            
            elif export_format == 'excel':
                exporter = ReportExporter(request.user)
                excel_file = exporter.export_cash_flow_excel(cash_flow)
                response = HttpResponse(
                    excel_file,
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = f'attachment; filename="cash_flow_nrb_{start_date}_{end_date}.xlsx"'
                return response
            
            return Response(cash_flow)
            
        except Exception as e:
            logger.error(f"Error generating NRB cash flow statement: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
