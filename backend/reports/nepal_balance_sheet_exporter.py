"""
Nepal Standard Balance Sheet Exporter
Creates balance sheet in exact format as per Nepal accounting standards
with Schedule numbers, comparative columns, and proper formatting
"""

from io import BytesIO
from datetime import datetime, timedelta
from decimal import Decimal
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from django.http import HttpResponse
from bills.models import Bill
from django.db.models import Sum, Q


class NepalBalanceSheetExporter:
    """
    Export Balance Sheet in Nepal Standard Format
    Matches the format shown in rajendrabalancesheet.jpg
    """
    
    def __init__(self, user, company_name=None):
        self.user = user
        self.company_name = company_name or f"{user.username}'s Business"
    
    def _get_balance_for_period(self, category_names, end_date):
        """Get balance for specific categories up to a date"""
        query = Q(user=self.user, bill_date__lte=end_date)
        
        # Try to find by category name
        balance = Bill.objects.filter(
            query,
            category__name__in=category_names
        ).aggregate(total=Sum('amount_npr'))['total'] or Decimal('0.00')
        
        return balance
    
    def _calculate_total_assets(self, end_date):
        """Calculate total assets"""
        # Get all DEBIT transactions (assets)
        total = Bill.objects.filter(
            user=self.user,
            bill_date__lte=end_date,
            is_debit=True
        ).aggregate(total=Sum('amount_npr'))['total'] or Decimal('0.00')
        
        return total
    
    def _calculate_total_liabilities(self, end_date):
        """Calculate total liabilities (excluding equity)"""
        # Get all CREDIT transactions that are liabilities
        total = Bill.objects.filter(
            user=self.user,
            bill_date__lte=end_date,
            is_debit=False,
            account_type='LIABILITY'
        ).aggregate(total=Sum('amount_npr'))['total'] or Decimal('0.00')
        
        return total
    
    def _calculate_equity(self, end_date):
        """Calculate equity (including retained earnings)"""
        # Share Capital
        share_capital = self._get_balance_for_period(['Share Capital', 'Capital'], end_date)
        
        # Calculate retained earnings (Revenue - Expenses)
        revenue = Bill.objects.filter(
            user=self.user,
            bill_date__lte=end_date,
            account_type='REVENUE'
        ).aggregate(total=Sum('amount_npr'))['total'] or Decimal('0.00')
        
        expenses = Bill.objects.filter(
            user=self.user,
            bill_date__lte=end_date,
            account_type='EXPENSE'
        ).aggregate(total=Sum('amount_npr'))['total'] or Decimal('0.00')
        
        retained_earnings = revenue - expenses
        
        return share_capital, retained_earnings
    
    def export_to_pdf(self, end_date, comparison_date=None):
        """
        Export balance sheet to PDF in Nepal standard format
        
        Args:
            end_date: The "as on" date for the balance sheet
            comparison_date: Optional previous year date for comparison
        
        Returns:
            HttpResponse with PDF file
        """
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # If no comparison date provided, use previous year
        if comparison_date is None:
            comparison_date = end_date.replace(year=end_date.year - 1)
        elif isinstance(comparison_date, str):
            comparison_date = datetime.strptime(comparison_date, '%Y-%m-%d').date()
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                              topMargin=0.5*inch, 
                              bottomMargin=0.5*inch,
                              leftMargin=0.75*inch,
                              rightMargin=0.75*inch)
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Title Style
        title_style = ParagraphStyle(
            'BalanceSheetTitle',
            parent=styles['Heading1'],
            fontSize=14,
            textColor=colors.black,
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'BalanceSheetSubtitle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.black,
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica'
        )
        
        # Title
        elements.append(Paragraph("Balance Sheet", title_style))
        
        # Convert to Nepali date format if needed (for now using Gregorian)
        # In production, you would use nepali_datetime library
        date_str = f"As on Ashadh 32, {end_date.year + 57}"  # Rough BS conversion
        elements.append(Paragraph(date_str, subtitle_style))
        
        # Get current year data
        current_data = self._get_balance_sheet_data(end_date)
        
        # Get previous year data
        previous_data = self._get_balance_sheet_data(comparison_date)
        
        # Format date headers
        current_header = f"As on Ashadh 32, {end_date.year + 57}"
        previous_header = f"As on Ashadh 31, {end_date.year + 56}"
        
        # Build table data
        table_data = []
        
        # Header row
        table_data.append([
            Paragraph('<b>Assets</b>', styles['Normal']),
            Paragraph('<b>Schedule</b>', styles['Normal']),
            Paragraph(f'<b>{current_header}</b><br/><b>Rs.</b>', styles['Normal']),
            Paragraph(f'<b>{previous_header}</b><br/><b>Rs.</b>', styles['Normal'])
        ])
        
        # Non Current Assets
        table_data.append([
            Paragraph('<b>Non Current Assets</b>', styles['Normal']),
            '', '', ''
        ])
        
        table_data.append([
            Paragraph('    Property, Plant & Equipment', styles['Normal']),
            '1',
            self._format_amount(current_data['property_plant_equipment']),
            self._format_amount(previous_data['property_plant_equipment'])
        ])
        
        table_data.append([
            Paragraph('    Other Receivables', styles['Normal']),
            '',
            '-' if current_data['other_receivables'] == 0 else self._format_amount(current_data['other_receivables']),
            '-' if previous_data['other_receivables'] == 0 else self._format_amount(previous_data['other_receivables'])
        ])
        
        table_data.append([
            Paragraph('<b>Total Non-Current Assets</b>', styles['Normal']),
            '',
            self._format_amount(current_data['total_non_current_assets']),
            self._format_amount(previous_data['total_non_current_assets'])
        ])
        
        # Current Assets
        table_data.append([
            Paragraph('<b>Current Assets</b>', styles['Normal']),
            '', '', ''
        ])
        
        table_data.append([
            Paragraph('    Investments', styles['Normal']),
            '',
            '-' if current_data['investments'] == 0 else self._format_amount(current_data['investments']),
            '-' if previous_data['investments'] == 0 else self._format_amount(previous_data['investments'])
        ])
        
        table_data.append([
            Paragraph('    Loans And Advances', styles['Normal']),
            '',
            '-' if current_data['loans_advances'] == 0 else self._format_amount(current_data['loans_advances']),
            '-' if previous_data['loans_advances'] == 0 else self._format_amount(previous_data['loans_advances'])
        ])
        
        table_data.append([
            Paragraph('    Inventories', styles['Normal']),
            '2',
            '-' if current_data['inventories'] == 0 else self._format_amount(current_data['inventories']),
            '-' if previous_data['inventories'] == 0 else self._format_amount(previous_data['inventories'])
        ])
        
        table_data.append([
            Paragraph('    Advance Income Tax', styles['Normal']),
            '3',
            '-' if current_data['advance_income_tax'] == 0 else self._format_amount(current_data['advance_income_tax']),
            '-' if previous_data['advance_income_tax'] == 0 else self._format_amount(previous_data['advance_income_tax'])
        ])
        
        table_data.append([
            Paragraph('    Trade & Other Receivables', styles['Normal']),
            '4',
            self._format_amount(current_data['trade_receivables']),
            self._format_amount(previous_data['trade_receivables'])
        ])
        
        table_data.append([
            Paragraph('    Cash & Cash Equivalents', styles['Normal']),
            '5',
            self._format_amount(current_data['cash']),
            self._format_amount(previous_data['cash'])
        ])
        
        table_data.append([
            Paragraph('    Vat Receivable', styles['Normal']),
            '',
            self._format_amount(current_data['vat_receivable']),
            '-' if previous_data['vat_receivable'] == 0 else self._format_amount(previous_data['vat_receivable'])
        ])
        
        table_data.append([
            Paragraph('<b>Total Current Assets</b>', styles['Normal']),
            '',
            self._format_amount(current_data['total_current_assets']),
            self._format_amount(previous_data['total_current_assets'])
        ])
        
        # Empty row
        table_data.append(['', '', '', ''])
        
        table_data.append([
            Paragraph('<b>Total Assets</b>', styles['Normal']),
            '',
            self._format_amount(current_data['total_assets']),
            self._format_amount(previous_data['total_assets'])
        ])
        
        # EQUITY AND LIABILITIES
        table_data.append([
            Paragraph('<b>Equity</b>', styles['Normal']),
            '', '', ''
        ])
        
        table_data.append([
            Paragraph('    Share Capital', styles['Normal']),
            '6',
            self._format_amount(current_data['share_capital']),
            self._format_amount(previous_data['share_capital'])
        ])
        
        # Format reserves with parentheses if negative
        current_reserves_str = self._format_amount_with_negative(current_data['reserves'])
        previous_reserves_str = self._format_amount_with_negative(previous_data['reserves'])
        
        table_data.append([
            Paragraph('    Reserves', styles['Normal']),
            '',
            current_reserves_str,
            previous_reserves_str
        ])
        
        table_data.append([
            Paragraph('<b>Total Equity</b>', styles['Normal']),
            '',
            self._format_amount(current_data['total_equity']),
            self._format_amount(previous_data['total_equity'])
        ])
        
        # LIABILITIES
        table_data.append([
            Paragraph('<b>Liabilities</b>', styles['Normal']),
            '', '', ''
        ])
        
        table_data.append([
            Paragraph('<b>Non Current Liabilities</b>', styles['Normal']),
            '', '', ''
        ])
        
        table_data.append([
            Paragraph('    Loans & Borrowings', styles['Normal']),
            '7',
            '-' if current_data['non_current_loans'] == 0 else self._format_amount(current_data['non_current_loans']),
            '-' if previous_data['non_current_loans'] == 0 else self._format_amount(previous_data['non_current_loans'])
        ])
        
        table_data.append([
            Paragraph('    Provisions', styles['Normal']),
            '',
            '-' if current_data['provisions'] == 0 else self._format_amount(current_data['provisions']),
            '-' if previous_data['provisions'] == 0 else self._format_amount(previous_data['provisions'])
        ])
        
        table_data.append([
            Paragraph('<b>Total Non Current-Liabilities</b>', styles['Normal']),
            '',
            '-' if current_data['total_non_current_liabilities'] == 0 else self._format_amount(current_data['total_non_current_liabilities']),
            '-' if previous_data['total_non_current_liabilities'] == 0 else self._format_amount(previous_data['total_non_current_liabilities'])
        ])
        
        table_data.append([
            Paragraph('<b>Current Liabilities</b>', styles['Normal']),
            '', '', ''
        ])
        
        table_data.append([
            Paragraph('    Loans & Borrowings', styles['Normal']),
            '8',
            '-' if current_data['current_loans'] == 0 else self._format_amount(current_data['current_loans']),
            '-' if previous_data['current_loans'] == 0 else self._format_amount(previous_data['current_loans'])
        ])
        
        table_data.append([
            Paragraph('    Trade & other payables', styles['Normal']),
            '9',
            self._format_amount(current_data['trade_payables']),
            self._format_amount(previous_data['trade_payables'])
        ])
        
        table_data.append([
            Paragraph('    Income Tax Liability', styles['Normal']),
            '',
            '-' if current_data['income_tax_liability'] == 0 else self._format_amount(current_data['income_tax_liability']),
            '-' if previous_data['income_tax_liability'] == 0 else self._format_amount(previous_data['income_tax_liability'])
        ])
        
        table_data.append([
            Paragraph('    Vat Payable', styles['Normal']),
            '',
            '-' if current_data['vat_payable'] == 0 else self._format_amount(current_data['vat_payable']),
            self._format_amount(previous_data['vat_payable']) if previous_data['vat_payable'] > 0 else '-'
        ])
        
        table_data.append([
            Paragraph('<b>Total Current Liabilities</b>', styles['Normal']),
            '',
            self._format_amount(current_data['total_current_liabilities']),
            self._format_amount(previous_data['total_current_liabilities'])
        ])
        
        # Empty row
        table_data.append(['', '', '', ''])
        
        table_data.append([
            Paragraph('<b>Total Liabilities</b>', styles['Normal']),
            '',
            self._format_amount(current_data['total_liabilities']),
            self._format_amount(previous_data['total_liabilities'])
        ])
        
        # Empty row
        table_data.append(['', '', '', ''])
        
        table_data.append([
            Paragraph('<b>Total Equity & Liabilities</b>', styles['Normal']),
            '',
            self._format_amount(current_data['total_equity_and_liabilities']),
            self._format_amount(previous_data['total_equity_and_liabilities'])
        ])
        
        # Contingent Liabilities
        table_data.append([
            Paragraph('<b>Contingent Liabilities</b>', styles['Normal']),
            '', '-', '-'
        ])
        
        # Create table with specific column widths
        col_widths = [3.5*inch, 0.8*inch, 1.2*inch, 1.2*inch]
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        
        # Table styling
        table_style = TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            
            # Grid lines
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            
            # Valign
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ])
        
        table.setStyle(table_style)
        elements.append(table)
        
        # Footer note
        elements.append(Spacer(1, 0.2*inch))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.black,
            alignment=TA_LEFT
        )
        elements.append(Paragraph("Schedules 1 to 12 form integral part of financial statements.", footer_style))
        
        # Build PDF
        doc.build(elements)
        
        buffer.seek(0)
        pdf_content = buffer.read()
        buffer.close()
        
        # Create response
        response = HttpResponse(pdf_content, content_type='application/pdf')
        filename = f"balance_sheet_{end_date.strftime('%Y-%m-%d')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Content-Length'] = len(pdf_content)
        
        return response
    
    def _get_balance_sheet_data(self, end_date):
        """Calculate all balance sheet line items for a given date"""
        data = {}
        
        # NON-CURRENT ASSETS
        data['property_plant_equipment'] = self._get_balance_for_period(
            ['Fixed Assets', 'Property and Equipment', 'Equipment', 'Furniture', 'Property, Plant & Equipment'],
            end_date
        )
        data['other_receivables'] = Decimal('0.00')  # Can be calculated if needed
        data['total_non_current_assets'] = data['property_plant_equipment'] + data['other_receivables']
        
        # CURRENT ASSETS
        data['investments'] = self._get_balance_for_period(['Investments'], end_date)
        data['loans_advances'] = self._get_balance_for_period(['Loans and Advances'], end_date)
        data['inventories'] = self._get_balance_for_period(['Inventory', 'Stock'], end_date)
        data['advance_income_tax'] = self._get_balance_for_period(['Advance Tax', 'Tax Receivable'], end_date)
        data['trade_receivables'] = self._get_balance_for_period(
            ['Accounts Receivable', 'Trade Receivables', 'Receivables'],
            end_date
        )
        data['cash'] = self._get_balance_for_period(['Cash', 'Bank', 'Cash and Bank'], end_date)
        data['vat_receivable'] = self._get_balance_for_period(['VAT Receivable', 'Input VAT'], end_date)
        
        data['total_current_assets'] = (
            data['investments'] + data['loans_advances'] + data['inventories'] +
            data['advance_income_tax'] + data['trade_receivables'] + 
            data['cash'] + data['vat_receivable']
        )
        
        data['total_assets'] = data['total_non_current_assets'] + data['total_current_assets']
        
        # EQUITY
        data['share_capital'] = self._get_balance_for_period(['Share Capital', 'Capital'], end_date)
        
        # Reserves = Retained Earnings (Revenue - Expenses)
        revenue = Bill.objects.filter(
            user=self.user,
            bill_date__lte=end_date,
            account_type='REVENUE'
        ).aggregate(total=Sum('amount_npr'))['total'] or Decimal('0.00')
        
        expenses = Bill.objects.filter(
            user=self.user,
            bill_date__lte=end_date,
            account_type='EXPENSE'
        ).aggregate(total=Sum('amount_npr'))['total'] or Decimal('0.00')
        
        data['reserves'] = revenue - expenses
        data['total_equity'] = data['share_capital'] + data['reserves']
        
        # LIABILITIES - NON-CURRENT
        data['non_current_loans'] = self._get_balance_for_period(
            ['Long-term Loans', 'Long-term Borrowings'],
            end_date
        )
        data['provisions'] = self._get_balance_for_period(['Provisions'], end_date)
        data['total_non_current_liabilities'] = data['non_current_loans'] + data['provisions']
        
        # LIABILITIES - CURRENT
        data['current_loans'] = self._get_balance_for_period(
            ['Short-term Loans', 'Short-term Borrowings'],
            end_date
        )
        data['trade_payables'] = self._get_balance_for_period(
            ['Accounts Payable', 'Trade Payables', 'Payables'],
            end_date
        )
        data['income_tax_liability'] = self._get_balance_for_period(
            ['Income Tax Payable', 'Tax Liability'],
            end_date
        )
        data['vat_payable'] = self._get_balance_for_period(
            ['VAT Payable', 'Output VAT'],
            end_date
        )
        
        data['total_current_liabilities'] = (
            data['current_loans'] + data['trade_payables'] +
            data['income_tax_liability'] + data['vat_payable']
        )
        
        data['total_liabilities'] = data['total_non_current_liabilities'] + data['total_current_liabilities']
        data['total_equity_and_liabilities'] = data['total_equity'] + data['total_liabilities']
        
        return data
    
    def _format_amount(self, amount):
        """Format amount as string with comma separators"""
        if amount == 0:
            return '-'
        return f"{float(amount):,.2f}"
    
    def _format_amount_with_negative(self, amount):
        """Format amount with parentheses if negative"""
        if amount < 0:
            return f"({float(abs(amount)):,.2f})"
        elif amount == 0:
            return '-'
        return f"{float(amount):,.2f}"
