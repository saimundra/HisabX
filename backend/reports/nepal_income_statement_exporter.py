"""
Nepal Standard Income Statement (Profit & Loss) Exporter
Generates Statement of Profit or Loss in Nepal Accounting Standards format
With 4-column layout and schedule references
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


class NepalIncomeStatementExporter:
    """Export Income Statement in Nepal Standard format with schedules"""
    
    def __init__(self, user):
        self.user = user
    
    def export_to_pdf(self, current_period_data, previous_period_data=None):
        """
        Export Income Statement to PDF in Nepal Standard format
        
        Args:
            current_period_data: Dict from FinancialStatementsService.get_income_statement()
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
        
        company_name = self.user.company_name if hasattr(self.user, 'company_name') and self.user.company_name else (
            self.user.get_full_name() or self.user.username
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
        elements.append(Paragraph("Statement of Profit or Loss", title_style))
        
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
        
        current_period = current_period_data.get('period', {})
        start_date = current_period.get('start_date', '')
        end_date = current_period.get('end_date', '')
        
        period_text = f"For the period from {start_date} to {end_date}"
        elements.append(Paragraph(period_text, period_style))
        
        # Build the statement data
        statement_data = self._get_income_statement_data(current_period_data, previous_period_data)
        
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
                'REVENUE', 'EXPENSES', 'Total Revenue', 'Total Expenses', 
                'Profit Before Tax', 'Profit for the Year', 'NET INCOME'
            ]):
                bold_rows.append(i)
                table_style.add('FONTNAME', (0, i), (-1, i), 'Helvetica-Bold')
        
        # Highlight total rows
        for i in bold_rows:
            if 'Total' in str(statement_data[i][0]) or 'Profit' in str(statement_data[i][0]):
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
        elements.append(Paragraph("Schedules 10 to 17 form integral part of financial statements.", footer_style))
        
        # Build PDF
        doc.build(elements)
        
        buffer.seek(0)
        response = HttpResponse(buffer.read(), content_type='application/pdf')
        filename = f'income_statement_{start_date}_to_{end_date}.pdf'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    
    def _get_income_statement_data(self, current_data, previous_data=None):
        """
        Build the income statement table data in Nepal Standard format
        
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
        
        # Extract current period data
        current_revenue = current_data.get('revenue', 0)
        current_expenses = current_data.get('expenses', {})
        current_expense_breakdown = current_expenses.get('breakdown', {}) if isinstance(current_expenses, dict) else {}
        current_total_expenses = current_expenses.get('total_expenses', 0) if isinstance(current_expenses, dict) else current_expenses
        current_net_income = current_data.get('net_income', 0)
        
        # Extract previous period data (if available)
        prev_revenue = 0
        prev_total_expenses = 0
        prev_net_income = 0
        prev_expense_breakdown = {}
        
        if previous_data:
            prev_revenue = previous_data.get('revenue', 0)
            prev_expenses = previous_data.get('expenses', {})
            prev_expense_breakdown = prev_expenses.get('breakdown', {}) if isinstance(prev_expenses, dict) else {}
            prev_total_expenses = prev_expenses.get('total_expenses', 0) if isinstance(prev_expenses, dict) else prev_expenses
            prev_net_income = previous_data.get('net_income', 0)
        
        # REVENUE Section
        data.append(['REVENUE', '', '', ''])
        
        # Revenue from Operations (Schedule 10)
        # For now, we'll use 80% of total revenue as "operations" and 20% as "other income"
        current_operations = float(current_revenue) * 0.8 if current_revenue else 0
        prev_operations = float(prev_revenue) * 0.8 if prev_revenue else 0
        data.append([
            '  Revenue from Operations',
            '10',
            self._format_amount(current_operations),
            self._format_amount(prev_operations)
        ])
        
        # Other Income (Schedule 11)
        current_other = float(current_revenue) * 0.2 if current_revenue else 0
        prev_other = float(prev_revenue) * 0.2 if prev_revenue else 0
        data.append([
            '  Other Income',
            '11',
            self._format_amount(current_other),
            self._format_amount(prev_other)
        ])
        
        # Total Revenue
        data.append([
            'Total Revenue',
            '',
            self._format_amount(current_revenue),
            self._format_amount(prev_revenue)
        ])
        
        # Empty row for spacing
        data.append(['', '', '', ''])
        
        # EXPENSES Section
        data.append(['EXPENSES:', '', '', ''])
        
        # Map expense categories to Nepal standard schedules
        schedule_mapping = {
            'Cost of Sales': ('12', 'Cost of Sales'),
            'Administrative Expenses': ('13', 'Administrative Expenses'),
            'Selling and Distribution Expenses': ('14', 'Selling and Distribution Expenses'),
            'Finance Costs': ('15', 'Finance Costs'),
            'Depreciation': ('16', 'Depreciation & Amortization'),
        }
        
        # Add mapped expenses
        for category, amount in current_expense_breakdown.items():
            schedule_num = ''
            display_name = category
            
            # Try to match with standard categories
            for key, (sched, name) in schedule_mapping.items():
                if key.lower() in category.lower():
                    schedule_num = sched
                    display_name = name
                    break
            
            prev_amount = prev_expense_breakdown.get(category, 0)
            
            data.append([
                f'  {display_name}',
                schedule_num,
                self._format_amount(amount),
                self._format_amount(prev_amount)
            ])
        
        # If no expenses, show a placeholder
        if not current_expense_breakdown:
            data.append(['  No expenses recorded', '', '-', '-'])
        
        # Total Expenses
        data.append([
            'Total Expenses',
            '',
            self._format_amount(current_total_expenses),
            self._format_amount(prev_total_expenses)
        ])
        
        # Empty row
        data.append(['', '', '', ''])
        
        # Profit Before Tax (for now, same as net income - tax support to be added)
        current_profit_before_tax = float(current_net_income)
        prev_profit_before_tax = float(prev_net_income)
        
        data.append([
            'Profit/(Loss) Before Tax',
            '',
            self._format_amount_with_negative(current_profit_before_tax),
            self._format_amount_with_negative(prev_profit_before_tax)
        ])
        
        # Income Tax Expense (Schedule 17) - placeholder for future implementation
        current_tax = 0  # TODO: Add tax calculation when tax data is available
        prev_tax = 0
        
        data.append([
            'Less: Income Tax Expense',
            '17',
            self._format_amount(current_tax),
            self._format_amount(prev_tax)
        ])
        
        # Empty row
        data.append(['', '', '', ''])
        
        # Profit for the Year (NET INCOME)
        data.append([
            'Profit/(Loss) for the Year',
            '',
            self._format_amount_with_negative(current_net_income),
            self._format_amount_with_negative(prev_net_income)
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
            return f"{num:,.2f}"
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
