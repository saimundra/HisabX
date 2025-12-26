"""
Nepal Standard Cash Flow Statement Exporter
Generates Cash Flow Statement in Nepal Accounting Standards format
With 4-column layout and schedule references (Indirect Method)
"""
from io import BytesIO
from decimal import Decimal
from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


class NepalCashFlowExporter:
    """Export Cash Flow Statement in Nepal Standard format with schedules"""
    
    def __init__(self, user):
        self.user = user
    
    def export_to_pdf(self, current_period_data, previous_period_data=None):
        """
        Export Cash Flow Statement to PDF in Nepal Standard format
        
        Args:
            current_period_data: Dict from NRBFinancialStatements.get_cash_flow_statement()
            previous_period_data: Optional dict for previous period comparison
        
        Returns:
            HttpResponse with PDF file
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Company/User Name
        company_style = ParagraphStyle(
            'CompanyName',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.black,
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        company_name = current_period_data.get('company_name', 
            self.user.company_name if hasattr(self.user, 'company_name') and self.user.company_name 
            else (self.user.get_full_name() or self.user.username)
        )
        elements.append(Paragraph(company_name, company_style))
        
        # Statement Title
        title_style = ParagraphStyle(
            'StatementTitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.black,
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        elements.append(Paragraph("Cash Flow Statement", title_style))
        
        # Method subtitle
        method_style = ParagraphStyle(
            'Method',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.grey,
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName='Helvetica-Oblique'
        )
        elements.append(Paragraph("(Indirect Method)", method_style))
        
        # Period
        period_style = ParagraphStyle(
            'Period',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.black,
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica'
        )
        
        period_text = current_period_data.get('period', 'N/A')
        elements.append(Paragraph(f"For the period: {period_text}", period_style))
        
        # Build the statement data
        statement_data = self._get_cash_flow_data(current_period_data, previous_period_data)
        
        # Create the table
        table = Table(
            statement_data,
            colWidths=[4.5*inch, 0.8*inch, 1.4*inch, 1.4*inch]
        )
        
        # Table styling
        table_style = TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            
            # All cells
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('LEFTPADDING', (0, 1), (-1, -1), 8),
            ('RIGHTPADDING', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            
            # Borders
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('LINEABOVE', (0, 0), (-1, 0), 1, colors.black),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
            
            # Column alignments
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),      # Particulars - left
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),    # Schedule - center
            ('ALIGN', (2, 1), (2, -1), 'RIGHT'),     # Current Year - right
            ('ALIGN', (3, 1), (3, -1), 'RIGHT'),     # Previous Year - right
        ])
        
        # Apply bold styling to specific rows (section headers, totals)
        bold_rows = []
        for i, row in enumerate(statement_data[1:], start=1):  # Skip header
            if row[0] and any(keyword in str(row[0]) for keyword in [
                'Operating Activities', 'Investing Activities', 'Financing Activities',
                'Net Cash', 'Cash and Cash Equivalents'
            ]):
                bold_rows.append(i)
                table_style.add('FONTNAME', (0, i), (-1, i), 'Helvetica-Bold')
        
        # Highlight total rows
        for i in bold_rows:
            if 'Net' in str(statement_data[i][0]) or 'Cash and Cash Equivalents' in str(statement_data[i][0]):
                table_style.add('BACKGROUND', (0, i), (-1, i), colors.HexColor('#E7E6E6'))
        
        table.setStyle(table_style)
        elements.append(table)
        
        # Schedule footer note
        elements.append(Spacer(1, 0.3*inch))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.black,
            fontName='Helvetica-Oblique',
            alignment=TA_CENTER
        )
        elements.append(Paragraph("Schedules 18 to 23 form integral part of financial statements.", footer_style))
        
        # Build PDF
        doc.build(elements)
        
        buffer.seek(0)
        response = HttpResponse(buffer.read(), content_type='application/pdf')
        filename = f'cash_flow_statement_{current_period_data.get("period", "").replace(" ", "_")}.pdf'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    
    def _get_cash_flow_data(self, current_data, previous_data=None):
        """
        Build the cash flow statement table data in Nepal Standard format
        
        Returns:
            List of lists for table rows
        """
        data = []
        
        # Header row
        data.append([
            'Particulars',
            'Schedule',
            'Current Year Rs.',
            'Previous Year Rs.'
        ])
        
        # Extract current year data
        current_year = current_data.get('current_year', {})
        current_operating = current_year.get('operating_activities', {})
        current_investing = current_year.get('investing_activities', {})
        current_financing = current_year.get('financing_activities', {})
        
        # Extract previous year data (if available)
        prev_operating = {}
        prev_investing = {}
        prev_financing = {}
        prev_year = {}
        
        if previous_data:
            prev_year = previous_data.get('current_year', {})  # Previous data's current year
            prev_operating = prev_year.get('operating_activities', {})
            prev_investing = prev_year.get('investing_activities', {})
            prev_financing = prev_year.get('financing_activities', {})
        else:
            # Try to get last_year from current data
            prev_year = current_data.get('last_year', {})
            prev_operating = prev_year.get('operating_activities', {})
            prev_investing = prev_year.get('investing_activities', {})
            prev_financing = prev_year.get('financing_activities', {})
        
        # A. CASH FLOW FROM OPERATING ACTIVITIES
        data.append(['A. Cash Flow from Operating Activities', '', '', ''])
        
        # Profit Before Tax
        data.append([
            '  Profit/(Loss) Before Tax',
            '18',
            self._format_amount_with_negative(current_operating.get('profit_before_tax', 0)),
            self._format_amount_with_negative(prev_operating.get('profit_before_tax', 0))
        ])
        
        # Adjustments section
        data.append(['  Adjustments for:', '', '', ''])
        
        # Depreciation
        data.append([
            '    Depreciation and Amortization',
            '19',
            self._format_amount(current_operating.get('depreciation', 0)),
            self._format_amount(prev_operating.get('depreciation', 0))
        ])
        
        # Operating profit before working capital changes
        data.append([
            '  Operating Profit Before Working Capital Changes',
            '',
            self._format_amount(current_operating.get('operating_profit_before_changes', 0)),
            self._format_amount(prev_operating.get('operating_profit_before_changes', 0))
        ])
        
        # Working capital changes
        data.append(['  Working Capital Changes:', '', '', ''])
        data.append([
            '    Changes in Operating Assets',
            '',
            self._format_amount_with_negative(current_operating.get('changes_in_assets', 0)),
            self._format_amount_with_negative(prev_operating.get('changes_in_assets', 0))
        ])
        data.append([
            '    Changes in Operating Liabilities',
            '',
            self._format_amount_with_negative(current_operating.get('changes_in_liabilities', 0)),
            self._format_amount_with_negative(prev_operating.get('changes_in_liabilities', 0))
        ])
        
        # Cash generated from operations
        data.append([
            '  Cash Generated from Operations',
            '',
            self._format_amount(current_operating.get('cash_from_operations', 0)),
            self._format_amount(prev_operating.get('cash_from_operations', 0))
        ])
        
        # Tax paid
        data.append([
            '  Less: Income Tax Paid',
            '20',
            self._format_amount_with_negative(-abs(float(current_operating.get('tax_paid', 0)))),
            self._format_amount_with_negative(-abs(float(prev_operating.get('tax_paid', 0))))
        ])
        
        # Net cash from operating
        data.append([
            'Net Cash from Operating Activities',
            '',
            self._format_amount_with_negative(current_operating.get('net_cash_from_operating', 0)),
            self._format_amount_with_negative(prev_operating.get('net_cash_from_operating', 0))
        ])
        
        # Empty row
        data.append(['', '', '', ''])
        
        # B. CASH FLOW FROM INVESTING ACTIVITIES
        data.append(['B. Cash Flow from Investing Activities', '', '', ''])
        
        # Purchase of property
        data.append([
            '  Purchase of Property, Plant & Equipment',
            '21',
            self._format_amount_with_negative(current_investing.get('purchase_of_property', 0)),
            self._format_amount_with_negative(prev_investing.get('purchase_of_property', 0))
        ])
        
        # Proceeds from sale
        data.append([
            '  Proceeds from Sale of Assets',
            '',
            self._format_amount(current_investing.get('proceeds_from_sale', 0)),
            self._format_amount(prev_investing.get('proceeds_from_sale', 0))
        ])
        
        # Net cash from investing
        data.append([
            'Net Cash from Investing Activities',
            '',
            self._format_amount_with_negative(current_investing.get('net_cash_from_investing', 0)),
            self._format_amount_with_negative(prev_investing.get('net_cash_from_investing', 0))
        ])
        
        # Empty row
        data.append(['', '', '', ''])
        
        # C. CASH FLOW FROM FINANCING ACTIVITIES
        data.append(['C. Cash Flow from Financing Activities', '', '', ''])
        
        # Proceeds from borrowing
        data.append([
            '  Proceeds from Borrowings',
            '22',
            self._format_amount(current_financing.get('proceeds_from_borrowing', 0)),
            self._format_amount(prev_financing.get('proceeds_from_borrowing', 0))
        ])
        
        # Repayment
        data.append([
            '  Repayment of Borrowings',
            '',
            self._format_amount_with_negative(current_financing.get('repayment_of_borrowing', 0)),
            self._format_amount_with_negative(prev_financing.get('repayment_of_borrowing', 0))
        ])
        
        # Dividends
        data.append([
            '  Dividends Paid',
            '23',
            self._format_amount_with_negative(current_financing.get('dividends_paid', 0)),
            self._format_amount_with_negative(prev_financing.get('dividends_paid', 0))
        ])
        
        # Net cash from financing
        data.append([
            'Net Cash from Financing Activities',
            '',
            self._format_amount_with_negative(current_financing.get('net_cash_from_financing', 0)),
            self._format_amount_with_negative(prev_financing.get('net_cash_from_financing', 0))
        ])
        
        # Empty row
        data.append(['', '', '', ''])
        
        # NET CHANGE IN CASH
        data.append([
            'Net Increase/(Decrease) in Cash and Cash Equivalents',
            '',
            self._format_amount_with_negative(current_year.get('net_change_in_cash', 0)),
            self._format_amount_with_negative(prev_year.get('net_change_in_cash', 0))
        ])
        
        # Cash at beginning
        data.append([
            'Cash and Cash Equivalents at Beginning of Period',
            '',
            self._format_amount(current_year.get('cash_beginning', 0)),
            self._format_amount(prev_year.get('cash_beginning', 0))
        ])
        
        # Cash at end
        data.append([
            'Cash and Cash Equivalents at End of Period',
            '',
            self._format_amount(current_year.get('cash_ending', 0)),
            self._format_amount(prev_year.get('cash_ending', 0))
        ])
        
        return data
    
    def _format_amount(self, value):
        """Format amount with comma separators (for positive values)"""
        if value is None or value == 0:
            return '-'
        
        try:
            num = float(value)
            if num == 0:
                return '-'
            return f"{abs(num):,.2f}"
        except (ValueError, TypeError):
            return '-'
    
    def _format_amount_with_negative(self, value):
        """Format amount with comma separators, show negatives in parentheses"""
        if value is None or value == 0:
            return '-'
        
        try:
            num = float(value)
            if num == 0:
                return '-'
            if num < 0:
                return f"({abs(num):,.2f})"
            return f"{num:,.2f}"
        except (ValueError, TypeError):
            return '-'
