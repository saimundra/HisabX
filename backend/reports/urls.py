from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ReportViewSet, 
    BalanceSheetView, 
    IncomeStatementView, 
    TrialBalanceView,
    MonthlyReportView,
    QuarterlyReportView,
    YearlyReportView,
    TransactionExportView,
    NRBBalanceSheetView,
    NRBIncomeStatementView,
    NRBCashFlowStatementView,
)

router = DefaultRouter()
router.register(r'audit_reports', ReportViewSet, basename='audit_report')

# Financial Statements URLs
financial_statements_urls = [
    path('balance-sheet/', BalanceSheetView.as_view(), name='balance_sheet'),
    path('balance-sheet', BalanceSheetView.as_view(), name='balance_sheet_no_slash'),  # Support both with and without trailing slash
    path('income-statement/', IncomeStatementView.as_view(), name='income_statement'),
    path('profit-loss/', IncomeStatementView.as_view(), name='profit_loss'),
    path('trial-balance/', TrialBalanceView.as_view(), name='trial_balance'),
    path('monthly/', MonthlyReportView.as_view(), name='monthly_report'),
    path('quarterly/', QuarterlyReportView.as_view(), name='quarterly_report'),
    path('yearly/', YearlyReportView.as_view(), name='yearly_report'),
    path('export-transactions/', TransactionExportView.as_view(), name='export_transactions'),
    
    # NRB Format Financial Statements
    path('nrb/balance-sheet/', NRBBalanceSheetView.as_view(), name='nrb_balance_sheet'),
    path('nrb/income-statement/', NRBIncomeStatementView.as_view(), name='nrb_income_statement'),
    path('nrb/cash-flow/', NRBCashFlowStatementView.as_view(), name='nrb_cash_flow'),
]

urlpatterns = [
    path('reports/', include(router.urls)),
    path('financial/', include(financial_statements_urls)),
]