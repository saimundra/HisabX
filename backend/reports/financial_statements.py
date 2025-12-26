"""
Financial Statements Generation Service
Generates Balance Sheet, Income Statement (P&L), and supporting reports
"""
from decimal import Decimal
from datetime import datetime, timedelta
from django.db.models import Sum, Q
from bills.models import Bill, ChartOfAccounts, JournalEntry, JournalEntryLine


class FinancialStatementsService:
    """Service for generating financial statements"""
    
    def __init__(self, user):
        self.user = user
    
    def get_balance_sheet(self, as_of_date=None):
        """
        Generate Balance Sheet: Assets = Liabilities + Equity
        
        Args:
            as_of_date: Date for the balance sheet (defaults to today)
        
        Returns:
            dict: Balance sheet with assets, liabilities, and equity
        """
        if as_of_date is None:
            as_of_date = datetime.now().date()
        
        # Ensure as_of_date is a date object (convert string if needed)
        if isinstance(as_of_date, str):
            as_of_date = datetime.strptime(as_of_date, '%Y-%m-%d').date()
        
        # Get all bills up to the specified date (for logging/debugging)
        bills_count = Bill.objects.filter(user=self.user, bill_date__lte=as_of_date).count()
        
        # Calculate Assets (will return 0.00 if no data)
        try:
            assets = self._calculate_account_type_balance('ASSET', as_of_date)
        except Exception as e:
            assets = Decimal('0.00')
        
        # Calculate Liabilities (will return 0.00 if no data)
        try:
            liabilities = self._calculate_account_type_balance('LIABILITY', as_of_date)
        except Exception as e:
            liabilities = Decimal('0.00')
        
        # Calculate Equity (including retained earnings)
        try:
            equity_base = self._calculate_account_type_balance('EQUITY', as_of_date)
        except Exception as e:
            equity_base = Decimal('0.00')
        
        # Retained Earnings = Revenue - Expenses
        try:
            revenue = self._calculate_account_type_balance('REVENUE', as_of_date)
        except Exception as e:
            revenue = Decimal('0.00')
        
        try:
            expenses = self._calculate_account_type_balance('EXPENSE', as_of_date)
        except Exception as e:
            expenses = Decimal('0.00')
        
        retained_earnings = revenue - expenses
        total_equity = equity_base + retained_earnings
        
        # Ensure all values are Decimal and convert date to string for JSON serialization
        as_of_date_str = as_of_date.strftime('%Y-%m-%d') if hasattr(as_of_date, 'strftime') else str(as_of_date)
        
        return {
            'as_of_date': as_of_date_str,
            'assets': {
                'current_assets': float(assets),
                'total_assets': float(assets)
            },
            'liabilities': {
                'current_liabilities': float(liabilities),
                'total_liabilities': float(liabilities)
            },
            'equity': {
                'retained_earnings': float(retained_earnings),
                'other_equity': float(equity_base),
                'total_equity': float(total_equity)
            },
            'total_liabilities_and_equity': float(liabilities + total_equity),
            'balanced': abs(assets - (liabilities + total_equity)) < Decimal('0.01')
        }
    
    def get_income_statement(self, start_date, end_date):
        """
        Generate Income Statement (Profit & Loss Statement)
        
        Args:
            start_date: Period start date
            end_date: Period end date
        
        Returns:
            dict: Income statement with revenue, expenses, and net income
        """
        # Calculate Revenue
        revenue = self._calculate_account_type_balance_for_period('REVENUE', start_date, end_date)
        
        # Calculate Expenses by category
        expenses_by_category = self._get_expenses_breakdown(start_date, end_date)
        total_expenses = sum(expenses_by_category.values())
        
        # Calculate Net Income
        net_income = revenue - total_expenses
        
        return {
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'revenue': revenue,
            'expenses': {
                'breakdown': expenses_by_category,
                'total_expenses': total_expenses
            },
            'net_income': net_income,
            'profit_margin': (net_income / revenue * 100) if revenue > 0 else Decimal('0.00')
        }
    
    def get_profit_loss_statement(self, start_date, end_date):
        """
        Alias for Income Statement (P&L is the same as Income Statement)
        """
        return self.get_income_statement(start_date, end_date)
    
    def get_trial_balance(self, as_of_date=None):
        """
        Generate Trial Balance to verify debits = credits
        
        Args:
            as_of_date: Date for trial balance
        
        Returns:
            dict: Trial balance with all accounts
        """
        if as_of_date is None:
            as_of_date = datetime.now().date()
        
        accounts = ChartOfAccounts.objects.filter(user=self.user, is_active=True)
        
        trial_balance = []
        total_debits = Decimal('0.00')
        total_credits = Decimal('0.00')
        
        for account in accounts:
            balance = self._get_account_balance(account, as_of_date)
            
            if balance > 0:
                # Asset, Expense accounts have debit balance
                if account.account_category in ['ASSET', 'EXPENSE']:
                    trial_balance.append({
                        'account_code': account.account_code,
                        'account_name': account.account_name,
                        'debit': balance,
                        'credit': Decimal('0.00')
                    })
                    total_debits += balance
                # Liability, Equity, Revenue have credit balance
                else:
                    trial_balance.append({
                        'account_code': account.account_code,
                        'account_name': account.account_name,
                        'debit': Decimal('0.00'),
                        'credit': balance
                    })
                    total_credits += balance
        
        return {
            'as_of_date': as_of_date,
            'accounts': trial_balance,
            'total_debits': total_debits,
            'total_credits': total_credits,
            'balanced': abs(total_debits - total_credits) < Decimal('0.01')
        }
    
    def get_monthly_reports(self, year, month):
        """Generate reports for a specific month"""
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)
        
        return {
            'period_type': 'MONTHLY',
            'year': year,
            'month': month,
            'balance_sheet': self.get_balance_sheet(end_date),
            'income_statement': self.get_income_statement(start_date, end_date)
        }
    
    def get_quarterly_reports(self, year, quarter):
        """Generate reports for a specific quarter (1-4)"""
        quarter_months = {
            1: (1, 3),
            2: (4, 6),
            3: (7, 9),
            4: (10, 12)
        }
        
        start_month, end_month = quarter_months[quarter]
        start_date = datetime(year, start_month, 1).date()
        end_date = datetime(year, end_month + 1, 1).date() - timedelta(days=1) if end_month < 12 else datetime(year, 12, 31).date()
        
        return {
            'period_type': 'QUARTERLY',
            'year': year,
            'quarter': quarter,
            'balance_sheet': self.get_balance_sheet(end_date),
            'income_statement': self.get_income_statement(start_date, end_date)
        }
    
    def get_yearly_reports(self, year):
        """Generate reports for an entire year"""
        start_date = datetime(year, 1, 1).date()
        end_date = datetime(year, 12, 31).date()
        
        return {
            'period_type': 'YEARLY',
            'year': year,
            'balance_sheet': self.get_balance_sheet(end_date),
            'income_statement': self.get_income_statement(start_date, end_date)
        }
    
    # Helper methods
    def _calculate_account_type_balance(self, account_type, as_of_date):
        """Calculate total balance for an account type (in NPR)"""
        # For assets and expenses: debits increase, credits decrease
        # For liabilities, equity, revenue: credits increase, debits decrease
        
        if account_type in ['ASSET', 'EXPENSE']:
            # Sum debits minus credits
            debits = Bill.objects.filter(
                user=self.user,
                account_type=account_type,
                bill_date__lte=as_of_date,
                is_debit=True
            ).aggregate(total=Sum('amount_npr'))['total'] or Decimal('0.00')
            
            credits = Bill.objects.filter(
                user=self.user,
                account_type=account_type,
                bill_date__lte=as_of_date,
                is_debit=False
            ).aggregate(total=Sum('amount_npr'))['total'] or Decimal('0.00')
            
            return debits - credits
        else:
            # For LIABILITY, EQUITY, REVENUE: credits minus debits
            credits = Bill.objects.filter(
                user=self.user,
                account_type=account_type,
                bill_date__lte=as_of_date,
                is_debit=False
            ).aggregate(total=Sum('amount_npr'))['total'] or Decimal('0.00')
            
            debits = Bill.objects.filter(
                user=self.user,
                account_type=account_type,
                bill_date__lte=as_of_date,
                is_debit=True
            ).aggregate(total=Sum('amount_npr'))['total'] or Decimal('0.00')
            
            return credits - debits
    
    def _calculate_account_type_balance_for_period(self, account_type, start_date, end_date):
        """Calculate balance for account type within a period (in NPR)"""
        # For assets and expenses: debits increase, credits decrease
        # For liabilities, equity, revenue: credits increase, debits decrease
        
        if account_type in ['ASSET', 'EXPENSE']:
            # Sum debits minus credits
            debits = Bill.objects.filter(
                user=self.user,
                account_type=account_type,
                bill_date__gte=start_date,
                bill_date__lte=end_date,
                is_debit=True
            ).aggregate(total=Sum('amount_npr'))['total'] or Decimal('0.00')
            
            credits = Bill.objects.filter(
                user=self.user,
                account_type=account_type,
                bill_date__gte=start_date,
                bill_date__lte=end_date,
                is_debit=False
            ).aggregate(total=Sum('amount_npr'))['total'] or Decimal('0.00')
            
            return debits - credits
        else:
            # For LIABILITY, EQUITY, REVENUE: credits minus debits
            credits = Bill.objects.filter(
                user=self.user,
                account_type=account_type,
                bill_date__gte=start_date,
                bill_date__lte=end_date,
                is_debit=False
            ).aggregate(total=Sum('amount_npr'))['total'] or Decimal('0.00')
            
            debits = Bill.objects.filter(
                user=self.user,
                account_type=account_type,
                bill_date__gte=start_date,
                bill_date__lte=end_date,
                is_debit=True
            ).aggregate(total=Sum('amount_npr'))['total'] or Decimal('0.00')
            
            return credits - debits
    
    def _get_expenses_breakdown(self, start_date, end_date):
        """Get expenses broken down by category (in NPR)"""
        from bills.models import Category
        
        expenses = {}
        categories = Category.objects.all()
        
        for category in categories:
            total = Bill.objects.filter(
                user=self.user,
                category=category,
                account_type='EXPENSE',
                bill_date__gte=start_date,
                bill_date__lte=end_date
            ).aggregate(total=Sum('amount_npr'))
            
            amount = total['total'] or Decimal('0.00')
            if amount > 0:
                expenses[category.name] = amount
        
        return expenses
    
    def _get_account_balance(self, account, as_of_date):
        """Get balance for a specific account"""
        # Sum all journal entry lines for this account
        debits = JournalEntryLine.objects.filter(
            account=account,
            journal_entry__user=self.user,
            journal_entry__entry_date__lte=as_of_date,
            entry_type='DEBIT'
        ).aggregate(total=Sum('amount'))
        
        credits = JournalEntryLine.objects.filter(
            account=account,
            journal_entry__user=self.user,
            journal_entry__entry_date__lte=as_of_date,
            entry_type='CREDIT'
        ).aggregate(total=Sum('amount'))
        
        debit_total = debits['total'] or Decimal('0.00')
        credit_total = credits['total'] or Decimal('0.00')
        
        # For Asset and Expense accounts: Debit increases, Credit decreases
        # For Liability, Equity, Revenue: Credit increases, Debit decreases
        if account.account_category in ['ASSET', 'EXPENSE']:
            return debit_total - credit_total
        else:
            return credit_total - debit_total
