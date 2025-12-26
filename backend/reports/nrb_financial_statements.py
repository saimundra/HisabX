"""
Nepal Rastra Bank (NRB) Compliant Financial Statements
Format as per NRB Circular 23 for Commercial Banks (Class A/B/C)
Adapted for general business use
"""

from decimal import Decimal
from django.db.models import Sum, Q
from bills.models import Bill, Category, ChartOfAccounts
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class NRBFinancialStatements:
    """
    Generate NRB-compliant financial statements for businesses
    Following the format prescribed by Nepal Rastra Bank
    """
    
    def __init__(self, user=None, company_name="ABC Company", start_date=None, end_date=None):
        self.user = user
        self.company_name = company_name
        self.start_date = start_date
        self.end_date = end_date
        
        # Get previous year dates for comparison
        if start_date and end_date:
            year_diff = timedelta(days=365)
            self.prev_start_date = start_date - year_diff
            self.prev_end_date = end_date - year_diff
        else:
            self.prev_start_date = None
            self.prev_end_date = None
    
    def get_balance_sheet(self):
        """
        Statement of Financial Position (Balance Sheet)
        As per NRB Format with comparative figures
        """
        current_year = self._calculate_balance_sheet(self.start_date, self.end_date)
        last_year = self._calculate_balance_sheet(self.prev_start_date, self.prev_end_date)
        
        return {
            'company_name': self.company_name,
            'statement_name': 'Statement of Financial Position',
            'as_at': self.end_date.strftime('%d %B %Y') if self.end_date else 'N/A',
            'currency': 'NPR',
            'current_year': current_year,
            'last_year': last_year,
        }
    
    def _calculate_balance_sheet(self, start_date, end_date):
        """Calculate balance sheet figures for a period"""
        if not start_date or not end_date:
            return self._empty_balance_sheet()
        
        # Build query filter
        query_filter = Q(bill_date__lte=end_date)
        if self.user:
            query_filter &= Q(user=self.user)
        
        # ASSETS
        assets = {
            # Cash and Bank
            'cash_and_cash_equivalent': self._get_balance_by_category(
                ['Cash', 'Bank', 'Cash and Bank'], query_filter
            ),
            
            # For banks: Due from NRB, Placement with Banks, etc.
            # For general business: Not applicable
            'due_from_nrb': Decimal('0.00'),
            'placement_with_banks': Decimal('0.00'),
            'derivative_financial_instruments': Decimal('0.00'),
            'other_trading_assets': Decimal('0.00'),
            
            # Loans and Advances
            'loans_to_bfis': Decimal('0.00'),
            'loans_to_customers': self._get_balance_by_category(
                ['Loans and Advances', 'Receivables'], query_filter
            ),
            
            # Investments
            'investment_securities': self._get_balance_by_category(
                ['Investments', 'Securities'], query_filter
            ),
            
            # Tax Assets
            'current_tax_assets': Decimal('0.00'),
            
            # Subsidiaries and Associates
            'investment_in_subsidiaries': Decimal('0.00'),
            'investment_in_associates': Decimal('0.00'),
            
            # Property
            'investment_property': self._get_balance_by_category(
                ['Investment Property'], query_filter
            ),
            'property_and_equipment': self._get_balance_by_category(
                ['Fixed Assets', 'Property and Equipment', 'Equipment', 'Furniture'], query_filter
            ),
            
            # Intangibles
            'goodwill_and_intangible': self._get_balance_by_category(
                ['Intangible Assets', 'Goodwill', 'Software'], query_filter
            ),
            
            # Deferred Tax
            'deferred_tax_assets': Decimal('0.00'),
            
            # Other Assets
            'other_assets': self._get_balance_by_category(
                ['Other Assets', 'Prepaid Expenses'], query_filter
            ),
        }
        
        assets['total_assets'] = sum(assets.values())
        
        # LIABILITIES
        liabilities = {
            # Bank-specific liabilities
            'due_to_banks': Decimal('0.00'),
            'due_to_nrb': Decimal('0.00'),
            'derivative_financial_instruments': Decimal('0.00'),
            'deposits_from_customers': Decimal('0.00'),
            
            # General business liabilities
            'borrowings': self._get_balance_by_category(
                ['Borrowings', 'Loans Payable'], query_filter
            ),
            
            # Tax
            'current_tax_liabilities': self._get_tax_liability(query_filter),
            
            # Provisions and Deferred Tax
            'provisions': Decimal('0.00'),
            'deferred_tax_liabilities': Decimal('0.00'),
            
            # Other Liabilities
            'other_liabilities': self._get_balance_by_category(
                ['Accounts Payable', 'Other Liabilities', 'Accrued Expenses'], query_filter
            ),
            
            # Debt Securities
            'debt_securities_issued': Decimal('0.00'),
            'subordinated_liabilities': Decimal('0.00'),
        }
        
        liabilities['total_liabilities'] = sum(liabilities.values())
        
        # EQUITY
        retained_earnings = self._get_retained_earnings(start_date, end_date)
        
        equity = {
            'share_capital': self._get_balance_by_category(
                ['Share Capital', 'Capital'], query_filter
            ),
            'share_premium': Decimal('0.00'),
            'retained_earnings': retained_earnings,
            'reserves': self._get_balance_by_category(
                ['Reserves', 'General Reserve'], query_filter
            ),
            'other_comprehensive_income': Decimal('0.00'),
        }
        
        equity['total_equity'] = sum(equity.values())
        
        return {
            'assets': assets,
            'liabilities': liabilities,
            'equity': equity,
            'total_liabilities_and_equity': liabilities['total_liabilities'] + equity['total_equity'],
            'is_balanced': abs(assets['total_assets'] - (liabilities['total_liabilities'] + equity['total_equity'])) < Decimal('0.01'),
        }
    
    def get_profit_loss_statement(self):
        """
        Statement of Profit or Loss
        As per NRB Format
        """
        current_year = self._calculate_profit_loss(self.start_date, self.end_date)
        last_year = self._calculate_profit_loss(self.prev_start_date, self.prev_end_date)
        
        return {
            'company_name': self.company_name,
            'statement_name': 'Statement of Profit or Loss',
            'period': f"{self.start_date.strftime('%d %B %Y')} to {self.end_date.strftime('%d %B %Y')}" if self.start_date and self.end_date else 'N/A',
            'currency': 'NPR',
            'current_year': current_year,
            'last_year': last_year,
        }
    
    def _calculate_profit_loss(self, start_date, end_date):
        """Calculate P&L figures for a period"""
        if not start_date or not end_date:
            return self._empty_profit_loss()
        
        # Build query filter
        query_filter = Q(bill_date__range=[start_date, end_date])
        if self.user:
            query_filter &= Q(user=self.user)
        
        # INCOME
        interest_income = self._get_income_by_category(['Interest Income'], query_filter)
        fee_commission = self._get_income_by_category(['Fee Income', 'Commission'], query_filter)
        
        # For general business: Revenue from sales/services
        revenue = Bill.objects.filter(
            query_filter & Q(transaction_type='CREDIT')
        ).exclude(
            category__name__in=['Interest Income', 'Fee Income', 'Commission']
        ).aggregate(total=Sum('amount_npr'))['total'] or Decimal('0.00')
        
        other_operating_income = self._get_income_by_category(['Other Income'], query_filter)
        
        total_operating_income = interest_income + fee_commission + revenue + other_operating_income
        
        # EXPENSES
        interest_expense = self._get_expense_by_category(['Interest Expense'], query_filter)
        net_interest_income = interest_income - interest_expense
        
        # Operating Expenses
        staff_expenses = self._get_expense_by_category(
            ['Salaries', 'Wages', 'Employee Benefits'], query_filter
        )
        
        # Get all other operating expenses
        all_expenses = Bill.objects.filter(
            query_filter & Q(transaction_type='DEBIT')
        ).aggregate(total=Sum('amount_npr'))['total'] or Decimal('0.00')
        
        depreciation = self._get_expense_by_category(['Depreciation', 'Amortization'], query_filter)
        
        other_operating_expenses = all_expenses - staff_expenses - depreciation - interest_expense
        
        total_operating_expenses = staff_expenses + other_operating_expenses + depreciation
        
        # Profit Calculations
        operating_profit = total_operating_income - interest_expense - total_operating_expenses
        
        # Non-operating items
        non_operating_income = self._get_income_by_category(['Non-Operating Income'], query_filter)
        non_operating_expense = self._get_expense_by_category(['Non-Operating Expense'], query_filter)
        
        profit_before_tax = operating_profit + non_operating_income - non_operating_expense
        
        # Tax (25% as per Nepal)
        tax_expense = self._calculate_tax(profit_before_tax)
        
        profit_after_tax = profit_before_tax - tax_expense
        
        return {
            'interest_income': interest_income,
            'interest_expense': interest_expense,
            'net_interest_income': net_interest_income,
            
            'fee_commission_income': fee_commission,
            'fee_commission_expense': Decimal('0.00'),
            'net_fee_commission': fee_commission,
            
            'net_trading_income': Decimal('0.00'),
            'other_operating_income': other_operating_income,
            'revenue': revenue,
            
            'total_operating_income': total_operating_income,
            
            'staff_expenses': staff_expenses,
            'other_operating_expenses': other_operating_expenses,
            'depreciation_amortization': depreciation,
            
            'total_operating_expenses': total_operating_expenses,
            
            'operating_profit': operating_profit,
            
            'non_operating_income': non_operating_income,
            'non_operating_expense': non_operating_expense,
            
            'profit_before_tax': profit_before_tax,
            'tax_expense': tax_expense,
            'profit_after_tax': profit_after_tax,
            
            'profit_margin': (profit_after_tax / total_operating_income * 100) if total_operating_income > 0 else Decimal('0.00'),
        }
    
    def get_cash_flow_statement(self):
        """
        Cash Flow Statement (Indirect Method)
        As per NRB Format
        """
        current_year = self._calculate_cash_flow(self.start_date, self.end_date)
        last_year = self._calculate_cash_flow(self.prev_start_date, self.prev_end_date)
        
        return {
            'company_name': self.company_name,
            'statement_name': 'Cash Flow Statement',
            'period': f"{self.start_date.strftime('%d %B %Y')} to {self.end_date.strftime('%d %B %Y')}" if self.start_date and self.end_date else 'N/A',
            'currency': 'NPR',
            'method': 'Indirect Method',
            'current_year': current_year,
            'last_year': last_year,
        }
    
    def _calculate_cash_flow(self, start_date, end_date):
        """Calculate cash flow for a period"""
        if not start_date or not end_date:
            return self._empty_cash_flow()
        
        profit_loss = self._calculate_profit_loss(start_date, end_date)
        
        # OPERATING ACTIVITIES
        profit_before_tax = profit_loss['profit_before_tax']
        depreciation = profit_loss['depreciation_amortization']
        
        operating_profit_before_changes = profit_before_tax + depreciation
        
        # Simplified changes (in real implementation, calculate from balance sheet changes)
        changes_in_operating_assets = Decimal('0.00')
        changes_in_operating_liabilities = Decimal('0.00')
        
        cash_from_operations = operating_profit_before_changes + changes_in_operating_assets + changes_in_operating_liabilities
        tax_paid = profit_loss['tax_expense']
        
        net_cash_from_operating = cash_from_operations - tax_paid
        
        # INVESTING ACTIVITIES
        query_filter = Q(bill_date__range=[start_date, end_date])
        if self.user:
            query_filter &= Q(user=self.user)
        
        # Try to find fixed asset purchases from actual categories, otherwise use 0
        purchase_of_property = self._get_expense_by_category(
            ['Fixed Assets', 'Property and Equipment', 'Property', 'Equipment', 'Assets'], query_filter
        )
        
        # If no fixed asset categories exist, use a portion of business expenses as proxy
        if purchase_of_property == Decimal('0.00'):
            business_expenses = self._get_expense_by_category(['Business'], query_filter)
            # Assume 10% of business expenses might be capital expenditure
            purchase_of_property = business_expenses * Decimal('0.10')
        
        net_cash_from_investing = -purchase_of_property
        
        # FINANCING ACTIVITIES
        # Try to find loan/financing related transactions
        proceeds_from_borrowing = self._get_income_by_category(['Borrowings', 'Loan', 'Financing'], query_filter)
        repayment_of_borrowing = self._get_expense_by_category(['Loan Repayment', 'Loan Payment', 'Debt Payment'], query_filter)
        dividends_paid = self._get_expense_by_category(['Dividends', 'Distribution'], query_filter)
        
        net_cash_from_financing = proceeds_from_borrowing - repayment_of_borrowing - dividends_paid
        
        # NET CHANGE IN CASH
        # Use total income and expenses as proxy for cash flow if no specific categories exist
        if net_cash_from_operating == Decimal('0.00') and purchase_of_property == Decimal('0.00'):
            # Fall back to simple cash flow: Income - Expenses
            total_income = profit_loss['total_operating_income']
            total_expenses = profit_loss['total_operating_expenses']
            net_change = total_income - total_expenses
            net_cash_from_operating = net_change
        else:
            net_change = net_cash_from_operating + net_cash_from_investing + net_cash_from_financing
        
        # Get cash balances - use total cumulative transactions as proxy
        cash_beginning = self._get_cash_at_date(start_date)
        cash_ending = cash_beginning + net_change
        
        return {
            'operating_activities': {
                'profit_before_tax': profit_before_tax,
                'depreciation': depreciation,
                'operating_profit_before_changes': operating_profit_before_changes,
                'changes_in_assets': changes_in_operating_assets,
                'changes_in_liabilities': changes_in_operating_liabilities,
                'cash_from_operations': cash_from_operations,
                'tax_paid': tax_paid,
                'net_cash_from_operating': net_cash_from_operating,
            },
            'investing_activities': {
                'purchase_of_property': -purchase_of_property,
                'proceeds_from_sale': Decimal('0.00'),
                'net_cash_from_investing': net_cash_from_investing,
            },
            'financing_activities': {
                'proceeds_from_borrowing': proceeds_from_borrowing,
                'repayment_of_borrowing': -repayment_of_borrowing,
                'dividends_paid': -dividends_paid,
                'net_cash_from_financing': net_cash_from_financing,
            },
            'net_change_in_cash': net_change,
            'cash_beginning': cash_beginning,
            'cash_ending': cash_ending,
        }
    
    # Helper Methods
    def _get_balance_by_category(self, category_names, query_filter):
        """Get balance for specific categories"""
        try:
            categories = Category.objects.filter(name__in=category_names)
            if categories.exists():
                total = Bill.objects.filter(
                    query_filter & Q(category__in=categories)
                ).aggregate(total=Sum('amount_npr'))['total'] or Decimal('0.00')
                return total
        except Exception as e:
            logger.error(f"Error getting balance by category: {e}")
        return Decimal('0.00')
    
    def _get_income_by_category(self, category_names, query_filter):
        """Get income for specific categories"""
        try:
            categories = Category.objects.filter(name__in=category_names)
            if categories.exists():
                total = Bill.objects.filter(
                    query_filter & Q(category__in=categories) & Q(transaction_type='CREDIT')
                ).aggregate(total=Sum('amount_npr'))['total'] or Decimal('0.00')
                return total
        except Exception as e:
            logger.error(f"Error getting income by category: {e}")
        return Decimal('0.00')
    
    def _get_expense_by_category(self, category_names, query_filter):
        """Get expense for specific categories"""
        try:
            categories = Category.objects.filter(name__in=category_names)
            if categories.exists():
                total = Bill.objects.filter(
                    query_filter & Q(category__in=categories) & Q(transaction_type='DEBIT')
                ).aggregate(total=Sum('amount_npr'))['total'] or Decimal('0.00')
                return total
        except Exception as e:
            logger.error(f"Error getting expense by category: {e}")
        return Decimal('0.00')
    
    def _get_retained_earnings(self, start_date, end_date):
        """Calculate retained earnings"""
        profit_loss = self._calculate_profit_loss(start_date, end_date)
        return profit_loss['profit_after_tax']
    
    def _get_tax_liability(self, query_filter):
        """Get tax liability"""
        try:
            total_tax = Bill.objects.filter(query_filter).aggregate(
                total=Sum('tax_amount')
            )['total'] or Decimal('0.00')
            return total_tax
        except Exception as e:
            logger.error(f"Error getting tax liability: {e}")
        return Decimal('0.00')
    
    def _calculate_tax(self, profit_before_tax):
        """Calculate tax expense (25% as per Nepal tax rate)"""
        if profit_before_tax > 0:
            return profit_before_tax * Decimal('0.25')
        return Decimal('0.00')
    
    def _get_cash_at_date(self, date):
        """Get cash balance at a specific date"""
        if not date or not self.user:
            return Decimal('0.00')
        
        try:
            # First try to find cash/bank categories
            cash_categories = Category.objects.filter(name__in=['Cash', 'Bank', 'Cash and Bank'])
            if cash_categories.exists():
                total = Bill.objects.filter(
                    Q(user=self.user) & Q(bill_date__lte=date) & Q(category__in=cash_categories)
                ).aggregate(total=Sum('amount_npr'))['total'] or Decimal('0.00')
                return total
            
            # If no cash categories exist, calculate net position from all transactions
            # Income - Expenses = Net Cash Position
            income = Bill.objects.filter(
                Q(user=self.user) & Q(bill_date__lte=date) & Q(transaction_type='CREDIT')
            ).aggregate(total=Sum('amount_npr'))['total'] or Decimal('0.00')
            
            expenses = Bill.objects.filter(
                Q(user=self.user) & Q(bill_date__lte=date) & Q(transaction_type='DEBIT')
            ).aggregate(total=Sum('amount_npr'))['total'] or Decimal('0.00')
            
            return income - expenses
            
        except Exception as e:
            logger.error(f"Error getting cash at date: {e}")
        return Decimal('0.00')
    
    def _empty_balance_sheet(self):
        """Return empty balance sheet structure"""
        return {
            'assets': {
                'cash_and_cash_equivalent': Decimal('0.00'),
                'due_from_nrb': Decimal('0.00'),
                'placement_with_banks': Decimal('0.00'),
                'derivative_financial_instruments': Decimal('0.00'),
                'other_trading_assets': Decimal('0.00'),
                'loans_to_bfis': Decimal('0.00'),
                'loans_to_customers': Decimal('0.00'),
                'investment_securities': Decimal('0.00'),
                'current_tax_assets': Decimal('0.00'),
                'investment_in_subsidiaries': Decimal('0.00'),
                'investment_in_associates': Decimal('0.00'),
                'investment_property': Decimal('0.00'),
                'property_and_equipment': Decimal('0.00'),
                'goodwill_and_intangible': Decimal('0.00'),
                'deferred_tax_assets': Decimal('0.00'),
                'other_assets': Decimal('0.00'),
                'total_assets': Decimal('0.00'),
            },
            'liabilities': {
                'due_to_banks': Decimal('0.00'),
                'due_to_nrb': Decimal('0.00'),
                'derivative_financial_instruments': Decimal('0.00'),
                'deposits_from_customers': Decimal('0.00'),
                'borrowings': Decimal('0.00'),
                'current_tax_liabilities': Decimal('0.00'),
                'provisions': Decimal('0.00'),
                'deferred_tax_liabilities': Decimal('0.00'),
                'other_liabilities': Decimal('0.00'),
                'debt_securities_issued': Decimal('0.00'),
                'subordinated_liabilities': Decimal('0.00'),
                'total_liabilities': Decimal('0.00'),
            },
            'equity': {
                'share_capital': Decimal('0.00'),
                'share_premium': Decimal('0.00'),
                'retained_earnings': Decimal('0.00'),
                'reserves': Decimal('0.00'),
                'other_comprehensive_income': Decimal('0.00'),
                'total_equity': Decimal('0.00'),
            },
            'total_liabilities_and_equity': Decimal('0.00'),
            'is_balanced': True,
        }
    
    def _empty_profit_loss(self):
        """Return empty P&L structure"""
        return {
            'interest_income': Decimal('0.00'),
            'interest_expense': Decimal('0.00'),
            'net_interest_income': Decimal('0.00'),
            'fee_commission_income': Decimal('0.00'),
            'fee_commission_expense': Decimal('0.00'),
            'net_fee_commission': Decimal('0.00'),
            'net_trading_income': Decimal('0.00'),
            'other_operating_income': Decimal('0.00'),
            'revenue': Decimal('0.00'),
            'total_operating_income': Decimal('0.00'),
            'staff_expenses': Decimal('0.00'),
            'other_operating_expenses': Decimal('0.00'),
            'depreciation_amortization': Decimal('0.00'),
            'total_operating_expenses': Decimal('0.00'),
            'operating_profit': Decimal('0.00'),
            'non_operating_income': Decimal('0.00'),
            'non_operating_expense': Decimal('0.00'),
            'profit_before_tax': Decimal('0.00'),
            'tax_expense': Decimal('0.00'),
            'profit_after_tax': Decimal('0.00'),
            'profit_margin': Decimal('0.00'),
        }
    
    def _empty_cash_flow(self):
        """Return empty cash flow structure"""
        return {
            'operating_activities': {
                'profit_before_tax': Decimal('0.00'),
                'depreciation': Decimal('0.00'),
                'operating_profit_before_changes': Decimal('0.00'),
                'changes_in_assets': Decimal('0.00'),
                'changes_in_liabilities': Decimal('0.00'),
                'cash_from_operations': Decimal('0.00'),
                'tax_paid': Decimal('0.00'),
                'net_cash_from_operating': Decimal('0.00'),
            },
            'investing_activities': {
                'purchase_of_property': Decimal('0.00'),
                'proceeds_from_sale': Decimal('0.00'),
                'net_cash_from_investing': Decimal('0.00'),
            },
            'financing_activities': {
                'proceeds_from_borrowing': Decimal('0.00'),
                'repayment_of_borrowing': Decimal('0.00'),
                'dividends_paid': Decimal('0.00'),
                'net_cash_from_financing': Decimal('0.00'),
            },
            'net_change_in_cash': Decimal('0.00'),
            'cash_beginning': Decimal('0.00'),
            'cash_ending': Decimal('0.00'),
        }
