import React, { useState, useEffect } from 'react';
import { useAuth } from '../../../../context/AuthContext';
import api from '../../../../services/api';
import './FinancialDashboard.css';
import BalanceSheet from './BalanceSheet';
import IncomeStatement from './IncomeStatement';
import TransactionLedger from './TransactionLedger';
import CashFlow from './CashFlow';
import ReportGenerator from '../../reports/ReportGenerator';

const FinancialDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('summary');
  
  // Period selection
  const [periodType, setPeriodType] = useState('monthly');
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth() + 1);
  const [selectedQuarter, setSelectedQuarter] = useState(1);
  
  // Financial data
  const [balanceSheet, setBalanceSheet] = useState(null);
  const [incomeStatement, setIncomeStatement] = useState(null);
  const [summary, setSummary] = useState(null);

  const fetchFinancialData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      let endpoint = '';
      let params = { year: selectedYear };
      
      if (periodType === 'monthly') {
        endpoint = '/financial/monthly/';
        params.month = selectedMonth;
      } else if (periodType === 'quarterly') {
        endpoint = '/financial/quarterly/';
        params.quarter = selectedQuarter;
      } else if (periodType === 'yearly') {
        endpoint = '/financial/yearly/';
      }
      
      const response = await api.get(endpoint, { params });
      
      setBalanceSheet(response.data.balance_sheet);
      setIncomeStatement(response.data.income_statement);
      
      // Create summary from the data
      setSummary({
        totalAssets: response.data.balance_sheet.assets.total_assets,
        totalLiabilities: response.data.balance_sheet.liabilities.total_liabilities,
        totalEquity: response.data.balance_sheet.equity.total_equity,
        netIncome: response.data.income_statement.net_income,
        revenue: response.data.income_statement.revenue,
        expenses: response.data.income_statement.expenses.total_expenses,
        profitMargin: response.data.income_statement.profit_margin,
        balanced: response.data.balance_sheet.balanced
      });
      
    } catch (err) {
      console.error('Error fetching financial data:', err);
      setError('Failed to load financial data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFinancialData();
  }, [periodType, selectedYear, selectedMonth, selectedQuarter]);

  const downloadBalanceSheet = async (format) => {
    try {
      const asOfDate = getAsOfDate();
      
      // Calculate comparison date (previous year)
      const currentDate = new Date(asOfDate);
      const comparisonDate = new Date(currentDate);
      comparisonDate.setFullYear(currentDate.getFullYear() - 1);
      const comparisonDateStr = comparisonDate.toISOString().split('T')[0];
      
      console.log('Downloading balance sheet:', { asOfDate, comparisonDate: comparisonDateStr, format });
      
      // Ensure format is valid
      if (!['pdf', 'excel'].includes(format)) {
        alert(`Invalid format: ${format}. Please use 'pdf' or 'excel'.`);
        return;
      }
      
      // Note: Axios with responseType: 'blob' doesn't follow redirects properly,
      // so we must include the trailing slash to avoid Django's APPEND_SLASH redirect
      // Ensure Authorization header is explicitly set for blob requests
      const token = localStorage.getItem('access_token');
      const headers = {};
      if (token) {
        headers.Authorization = `Bearer ${token}`;
      }
      
      const response = await api.get('/financial/balance-sheet/', {
        params: { 
          as_of_date: asOfDate, 
          comparison_date: comparisonDateStr,
          format 
        },
        responseType: 'blob',
        timeout: 30000, // 30 second timeout
        headers: headers // Explicitly set headers
      });
      
      // Check if response is actually a blob
      if (!(response.data instanceof Blob)) {
        throw new Error('Response is not a blob. Server may have returned an error.');
      }
      
      // Check content type to verify it's the expected file type
      const contentType = response.headers['content-type'] || '';
      const expectedType = format === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
      
      if (!contentType.includes(expectedType.split('/')[1])) {
        // Might be an error response, try to parse as text
        const text = await response.data.text();
        try {
          const errorData = JSON.parse(text);
          throw new Error(errorData.error || errorData.detail || 'Unknown error from server');
        } catch (parseError) {
          throw new Error(text || 'Invalid response from server');
        }
      }
      
      // Create download link
      const url = window.URL.createObjectURL(response.data);
      const link = document.createElement('a');
      link.href = url;
      const fileExtension = format === 'pdf' ? 'pdf' : 'xlsx';
      link.setAttribute('download', `balance_sheet_${asOfDate}.${fileExtension}`);
      document.body.appendChild(link);
      link.click();
      
      // Cleanup
      setTimeout(() => {
        window.URL.revokeObjectURL(url);
        link.remove();
      }, 100);
      
      console.log('Balance sheet downloaded successfully');
    } catch (err) {
      console.error('Error downloading balance sheet:', err);
      console.error('Error response:', err.response);
      
      let errorMessage = 'Failed to download balance sheet';
      
      // When responseType is 'blob', error responses are also blobs, so we need to parse them
      if (err.response?.data instanceof Blob) {
        try {
          const text = await err.response.data.text();
          try {
            const errorData = JSON.parse(text);
            errorMessage = errorData.error || errorData.detail || errorData.message || text;
          } catch {
            errorMessage = text || err.message;
          }
        } catch (parseError) {
          errorMessage = err.message || 'Failed to parse error response';
        }
      } else if (err.response?.data) {
        errorMessage = err.response.data.error || err.response.data.detail || err.response.statusText || err.message;
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      alert(`${errorMessage}\n\nPlease check the console for more details.`);
    }
  };

  const downloadIncomeStatement = async (format) => {
    try {
      const { startDate, endDate } = getDateRange();
      
      // Calculate comparison period (1 year prior)
      const startDateObj = new Date(startDate);
      const endDateObj = new Date(endDate);
      
      const comparisonStartObj = new Date(startDateObj);
      comparisonStartObj.setFullYear(startDateObj.getFullYear() - 1);
      const comparison_start_date = comparisonStartObj.toISOString().split('T')[0];
      
      const comparisonEndObj = new Date(endDateObj);
      comparisonEndObj.setFullYear(endDateObj.getFullYear() - 1);
      const comparison_end_date = comparisonEndObj.toISOString().split('T')[0];
      
      const response = await api.get('/financial/income-statement/', {
        params: { 
          start_date: startDate, 
          end_date: endDate, 
          comparison_start_date,
          comparison_end_date,
          format 
        },
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `income_statement_${startDate}_to_${endDate}.${format === 'pdf' ? 'pdf' : 'xlsx'}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Error downloading income statement:', err);
      alert('Failed to download income statement');
    }
  };

  const downloadTransactions = async () => {
    try {
      const { startDate, endDate } = getDateRange();
      const response = await api.get('/financial/export-transactions/', {
        params: { start_date: startDate, end_date: endDate },
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `transactions_${startDate}_to_${endDate}.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Error downloading transactions:', err);
      alert('Failed to download transactions');
    }
  };

  const getAsOfDate = () => {
    if (periodType === 'monthly') {
      const lastDay = new Date(selectedYear, selectedMonth, 0).getDate();
      return `${selectedYear}-${String(selectedMonth).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`;
    } else if (periodType === 'quarterly') {
      const quarterEndMonths = { 1: 3, 2: 6, 3: 9, 4: 12 };
      const month = quarterEndMonths[selectedQuarter];
      const lastDay = new Date(selectedYear, month, 0).getDate();
      return `${selectedYear}-${String(month).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`;
    } else {
      return `${selectedYear}-12-31`;
    }
  };

  const getDateRange = () => {
    if (periodType === 'monthly') {
      const lastDay = new Date(selectedYear, selectedMonth, 0).getDate();
      return {
        startDate: `${selectedYear}-${String(selectedMonth).padStart(2, '0')}-01`,
        endDate: `${selectedYear}-${String(selectedMonth).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`
      };
    } else if (periodType === 'quarterly') {
      const quarterRanges = {
        1: { start: '01-01', end: '03-31' },
        2: { start: '04-01', end: '06-30' },
        3: { start: '07-01', end: '09-30' },
        4: { start: '10-01', end: '12-31' }
      };
      const range = quarterRanges[selectedQuarter];
      return {
        startDate: `${selectedYear}-${range.start}`,
        endDate: `${selectedYear}-${range.end}`
      };
    } else {
      return {
        startDate: `${selectedYear}-01-01`,
        endDate: `${selectedYear}-12-31`
      };
    }
  };

  const getPeriodLabel = () => {
    if (periodType === 'monthly') {
      const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      return `${monthNames[selectedMonth - 1]} ${selectedYear}`;
    } else if (periodType === 'quarterly') {
      return `Q${selectedQuarter} ${selectedYear}`;
    } else {
      return `${selectedYear}`;
    }
  };

  if (loading) {
    return (
      <div className="financial-dashboard">
        <div className="loading-spinner">Loading financial data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="financial-dashboard">
        <div className="error-message">{error}</div>
      </div>
    );
  }

  return (
    <div className="financial-dashboard">
      <div className="dashboard-header">
        <h1>📊 Financial Dashboard</h1>
        <div className="period-selector">
          <select 
            value={periodType} 
            onChange={(e) => setPeriodType(e.target.value)}
            className="period-type-select"
          >
            <option value="monthly">Monthly</option>
            <option value="quarterly">Quarterly</option>
            <option value="yearly">Yearly</option>
          </select>
          
          <select 
            value={selectedYear} 
            onChange={(e) => setSelectedYear(Number(e.target.value))}
            className="year-select"
          >
            {[...Array(5)].map((_, i) => {
              const year = new Date().getFullYear() - 2 + i;
              return <option key={year} value={year}>{year}</option>;
            })}
          </select>
          
          {periodType === 'monthly' && (
            <select 
              value={selectedMonth} 
              onChange={(e) => setSelectedMonth(Number(e.target.value))}
              className="month-select"
            >
              {['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'].map((month, i) => (
                <option key={i + 1} value={i + 1}>{month}</option>
              ))}
            </select>
          )}
          
          {periodType === 'quarterly' && (
            <select 
              value={selectedQuarter} 
              onChange={(e) => setSelectedQuarter(Number(e.target.value))}
              className="quarter-select"
            >
              <option value={1}>Q1</option>
              <option value={2}>Q2</option>
              <option value={3}>Q3</option>
              <option value={4}>Q4</option>
            </select>
          )}
          
          <span className="period-label">{getPeriodLabel()}</span>
        </div>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="summary-cards">
          <div className="summary-card assets">
            <div className="card-icon">💰</div>
            <div className="card-content">
              <h3>Total Assets</h3>
              <p className="amount">${summary.totalAssets.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
            </div>
          </div>
          
          <div className="summary-card liabilities">
            <div className="card-icon">📉</div>
            <div className="card-content">
              <h3>Total Liabilities</h3>
              <p className="amount">${summary.totalLiabilities.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
            </div>
          </div>
          
          <div className="summary-card equity">
            <div className="card-icon">🏦</div>
            <div className="card-content">
              <h3>Total Equity</h3>
              <p className="amount">${summary.totalEquity.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
            </div>
          </div>
          
          <div className={`summary-card net-income ${summary.netIncome >= 0 ? 'positive' : 'negative'}`}>
            <div className="card-icon">{summary.netIncome >= 0 ? '📈' : '📉'}</div>
            <div className="card-content">
              <h3>Net Income</h3>
              <p className="amount">${summary.netIncome.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
              <span className="profit-margin">{summary.profitMargin.toFixed(2)}% margin</span>
            </div>
          </div>
          
          <div className="summary-card revenue">
            <div className="card-icon">💵</div>
            <div className="card-content">
              <h3>Revenue</h3>
              <p className="amount">${summary.revenue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
            </div>
          </div>
          
          <div className="summary-card expenses">
            <div className="card-icon">💳</div>
            <div className="card-content">
              <h3>Expenses</h3>
              <p className="amount">${summary.expenses.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="dashboard-tabs">
        <button 
          className={`tab ${activeTab === 'summary' ? 'active' : ''}`}
          onClick={() => setActiveTab('summary')}
        >
          Summary
        </button>
        <button 
          className={`tab ${activeTab === 'balance-sheet' ? 'active' : ''}`}
          onClick={() => setActiveTab('balance-sheet')}
        >
          Balance Sheet
        </button>
        <button 
          className={`tab ${activeTab === 'income-statement' ? 'active' : ''}`}
          onClick={() => setActiveTab('income-statement')}
        >
          Income Statement
        </button>
        <button 
          className={`tab ${activeTab === 'cash-flow' ? 'active' : ''}`}
          onClick={() => setActiveTab('cash-flow')}
        >
          Cash Flow
        </button>
        <button 
          className={`tab ${activeTab === 'transactions' ? 'active' : ''}`}
          onClick={() => setActiveTab('transactions')}
        >
          Transaction Ledger
        </button>
        <button 
          className={`tab ${activeTab === 'reports' ? 'active' : ''}`}
          onClick={() => setActiveTab('reports')}
        >
          Custom Reports
        </button>
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {activeTab === 'summary' && (
          <div className="summary-view">
            <h2>Financial Summary - {getPeriodLabel()}</h2>
            <div className="summary-info">
              <p className={`balance-status ${summary.balanced ? 'balanced' : 'unbalanced'}`}>
                {summary.balanced ? '✅ Balance Sheet is Balanced' : '⚠️ Balance Sheet is Not Balanced'}
              </p>
              <p className="accounting-equation">
                Assets (${summary.totalAssets.toFixed(2)}) = 
                Liabilities (${summary.totalLiabilities.toFixed(2)}) + 
                Equity (${summary.totalEquity.toFixed(2)})
              </p>
            </div>
          </div>
        )}
        
        {activeTab === 'balance-sheet' && balanceSheet && (
          <BalanceSheet 
            data={balanceSheet} 
            onDownload={downloadBalanceSheet}
            periodLabel={getPeriodLabel()}
          />
        )}
        
        {activeTab === 'income-statement' && incomeStatement && (
          <IncomeStatement 
            data={incomeStatement} 
            onDownload={downloadIncomeStatement}
            periodLabel={getPeriodLabel()}
          />
        )}
        
        {activeTab === 'cash-flow' && (
          <CashFlow 
            period={periodType}
            startDate={getDateRange().startDate}
            endDate={getDateRange().endDate}
          />
        )}
        
        {activeTab === 'transactions' && (
          <TransactionLedger 
            dateRange={getDateRange()}
            onDownload={downloadTransactions}
          />
        )}
        
        {activeTab === 'reports' && (
          <ReportGenerator />
        )}
      </div>
    </div>
  );
};

export default FinancialDashboard;
