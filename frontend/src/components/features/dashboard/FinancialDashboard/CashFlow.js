import React, { useState, useEffect } from 'react';
import api from '../../../../services/api';
import './CashFlow.css';

const CashFlow = ({ period, startDate, endDate }) => {
  const [cashFlowData, setCashFlowData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchCashFlow();
  }, [period, startDate, endDate]);

  const fetchCashFlow = async () => {
    try {
      setLoading(true);
      
      const params = {};
      if (startDate && endDate) {
        params.start_date = startDate;
        params.end_date = endDate;
      }

      const response = await api.get('/financial/nrb/cash-flow/', { params });
      setCashFlowData(response.data);
      setError(null);
    } catch (err) {
      console.error('Error fetching cash flow:', err);
      setError('Failed to load cash flow statement');
    } finally {
      setLoading(false);
    }
  };

  const downloadPDF = async () => {
    try {
      const params = { format: 'pdf' };
      if (startDate && endDate) {
        params.start_date = startDate;
        params.end_date = endDate;
        
        const startDateObj = new Date(startDate);
        const endDateObj = new Date(endDate);
        const comparisonStartObj = new Date(startDateObj);
        comparisonStartObj.setFullYear(startDateObj.getFullYear() - 1);
        const comparison_start_date = comparisonStartObj.toISOString().split('T')[0];
        const comparisonEndObj = new Date(endDateObj);
        comparisonEndObj.setFullYear(endDateObj.getFullYear() - 1);
        const comparison_end_date = comparisonEndObj.toISOString().split('T')[0];
        
        params.comparison_start_date = comparison_start_date;
        params.comparison_end_date = comparison_end_date;
      }

      const response = await api.get('/financial/nrb/cash-flow/', {
        params,
        responseType: 'blob'
      });

      const blob = new Blob([response.data], { type: 'application/pdf' });
      const link = document.createElement('a');
      link.href = window.URL.createObjectURL(blob);
      link.download = `cash_flow_${startDate}_${endDate}.pdf`;
      link.click();
    } catch (err) {
      console.error('Error downloading PDF:', err);
      alert('Failed to download PDF');
    }
  };

  const downloadExcel = async () => {
    try {
      const params = { format: 'excel' };
      if (startDate && endDate) {
        params.start_date = startDate;
        params.end_date = endDate;
      }

      const response = await api.get('/financial/nrb/cash-flow/', {
        params,
        responseType: 'blob'
      });

      const blob = new Blob([response.data], { 
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
      });
      const link = document.createElement('a');
      link.href = window.URL.createObjectURL(blob);
      link.download = `cash_flow_${startDate}_${endDate}.xlsx`;
      link.click();
    } catch (err) {
      console.error('Error downloading Excel:', err);
      alert('Failed to download Excel');
    }
  };

  const formatAmount = (value) => {
    if (!value || value === 0) return '-';
    return parseFloat(value).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };

  const formatNegative = (value) => {
    if (!value || value === 0) return '-';
    const num = parseFloat(value);
    if (num < 0) {
      return `(${Math.abs(num).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })})`;
    }
    return num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };

  if (loading) {
    return <div className="loading-message">Loading cash flow statement...</div>;
  }

  if (error) {
    return <div className="error-message">{error}</div>;
  }

  if (!cashFlowData) {
    return <div className="no-data-message">No data available</div>;
  }

  const currentYear = cashFlowData.current_year || {};
  const lastYear = cashFlowData.last_year || {};

  return (
    <div className="cash-flow-container">
      <div className="cash-flow-header">
        <h2>Cash Flow Statement</h2>
        <p className="method">(Indirect Method)</p>
        <p className="statement-date">Period: {cashFlowData.period}</p>
        <p style={{ fontSize: '13px', color: '#666', marginTop: '8px', fontStyle: 'italic' }}>
          📋 Nepal Standard Accounting Format (Schedule-based)
        </p>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '15px', marginTop: '20px' }}>
          <button 
            onClick={downloadPDF} 
            className="download-btn pdf"
            style={{
              background: '#4CAF50',
              color: 'white',
              padding: '12px 24px',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '16px'
            }}
          >
            📄 Download PDF
          </button>
          <button 
            onClick={downloadExcel} 
            className="download-btn excel"
            style={{
              background: '#2196F3',
              color: 'white',
              padding: '12px 24px',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '16px'
            }}
          >
            📊 Download Excel
          </button>
        </div>
      </div>

      <div className="financial-table-container">
        <table className="financial-table cash-flow-table">
          <thead>
            <tr>
              <th style={{textAlign: 'left', width: '45%'}}>Particulars</th>
              <th style={{textAlign: 'center', width: '10%'}}>Schedule</th>
              <th style={{textAlign: 'right', width: '22.5%'}}>Current Year Rs.</th>
              <th style={{textAlign: 'right', width: '22.5%'}}>Previous Year Rs.</th>
            </tr>
          </thead>
          <tbody>
            <tr><td colSpan="4"><strong>A. Cash Flow from Operating Activities</strong></td></tr>
            <tr>
              <td style={{paddingLeft: '20px'}}>Profit/(Loss) Before Tax</td>
              <td style={{textAlign: 'center'}}>18</td>
              <td style={{textAlign: 'right'}}>{formatNegative(currentYear.operating_activities?.profit_before_tax)}</td>
              <td style={{textAlign: 'right'}}>{formatNegative(lastYear.operating_activities?.profit_before_tax)}</td>
            </tr>
            <tr><td style={{paddingLeft: '20px'}} colSpan="4"><em>Adjustments for:</em></td></tr>
            <tr>
              <td style={{paddingLeft: '40px'}}>Depreciation and Amortization</td>
              <td style={{textAlign: 'center'}}>19</td>
              <td style={{textAlign: 'right'}}>{formatAmount(currentYear.operating_activities?.depreciation)}</td>
              <td style={{textAlign: 'right'}}>{formatAmount(lastYear.operating_activities?.depreciation)}</td>
            </tr>
            <tr>
              <td style={{paddingLeft: '20px'}}>Operating Profit Before Working Capital Changes</td>
              <td></td>
              <td style={{textAlign: 'right'}}>{formatAmount(currentYear.operating_activities?.operating_profit_before_changes)}</td>
              <td style={{textAlign: 'right'}}>{formatAmount(lastYear.operating_activities?.operating_profit_before_changes)}</td>
            </tr>
            <tr><td style={{paddingLeft: '20px'}} colSpan="4"><em>Working Capital Changes:</em></td></tr>
            <tr>
              <td style={{paddingLeft: '40px'}}>Changes in Operating Assets</td>
              <td></td>
              <td style={{textAlign: 'right'}}>{formatNegative(currentYear.operating_activities?.changes_in_assets)}</td>
              <td style={{textAlign: 'right'}}>{formatNegative(lastYear.operating_activities?.changes_in_assets)}</td>
            </tr>
            <tr>
              <td style={{paddingLeft: '40px'}}>Changes in Operating Liabilities</td>
              <td></td>
              <td style={{textAlign: 'right'}}>{formatNegative(currentYear.operating_activities?.changes_in_liabilities)}</td>
              <td style={{textAlign: 'right'}}>{formatNegative(lastYear.operating_activities?.changes_in_liabilities)}</td>
            </tr>
            <tr>
              <td style={{paddingLeft: '20px'}}>Cash Generated from Operations</td>
              <td></td>
              <td style={{textAlign: 'right'}}>{formatAmount(currentYear.operating_activities?.cash_from_operations)}</td>
              <td style={{textAlign: 'right'}}>{formatAmount(lastYear.operating_activities?.cash_from_operations)}</td>
            </tr>
            <tr>
              <td style={{paddingLeft: '20px'}}>Less: Income Tax Paid</td>
              <td style={{textAlign: 'center'}}>20</td>
              <td style={{textAlign: 'right'}}>{formatNegative(-Math.abs(parseFloat(currentYear.operating_activities?.tax_paid || 0)))}</td>
              <td style={{textAlign: 'right'}}>{formatNegative(-Math.abs(parseFloat(lastYear.operating_activities?.tax_paid || 0)))}</td>
            </tr>
            <tr>
              <td><strong>Net Cash from Operating Activities</strong></td>
              <td></td>
              <td style={{textAlign: 'right'}}><strong>{formatNegative(currentYear.operating_activities?.net_cash_from_operating)}</strong></td>
              <td style={{textAlign: 'right'}}><strong>{formatNegative(lastYear.operating_activities?.net_cash_from_operating)}</strong></td>
            </tr>
            
            <tr><td colSpan="4"></td></tr>
            
            <tr><td colSpan="4"><strong>B. Cash Flow from Investing Activities</strong></td></tr>
            <tr>
              <td style={{paddingLeft: '20px'}}>Purchase of Property, Plant & Equipment</td>
              <td style={{textAlign: 'center'}}>21</td>
              <td style={{textAlign: 'right'}}>{formatNegative(currentYear.investing_activities?.purchase_of_property)}</td>
              <td style={{textAlign: 'right'}}>{formatNegative(lastYear.investing_activities?.purchase_of_property)}</td>
            </tr>
            <tr>
              <td style={{paddingLeft: '20px'}}>Proceeds from Sale of Assets</td>
              <td></td>
              <td style={{textAlign: 'right'}}>{formatAmount(currentYear.investing_activities?.proceeds_from_sale)}</td>
              <td style={{textAlign: 'right'}}>{formatAmount(lastYear.investing_activities?.proceeds_from_sale)}</td>
            </tr>
            <tr>
              <td><strong>Net Cash from Investing Activities</strong></td>
              <td></td>
              <td style={{textAlign: 'right'}}><strong>{formatNegative(currentYear.investing_activities?.net_cash_from_investing)}</strong></td>
              <td style={{textAlign: 'right'}}><strong>{formatNegative(lastYear.investing_activities?.net_cash_from_investing)}</strong></td>
            </tr>
            
            <tr><td colSpan="4"></td></tr>
            
            <tr><td colSpan="4"><strong>C. Cash Flow from Financing Activities</strong></td></tr>
            <tr>
              <td style={{paddingLeft: '20px'}}>Proceeds from Borrowings</td>
              <td style={{textAlign: 'center'}}>22</td>
              <td style={{textAlign: 'right'}}>{formatAmount(currentYear.financing_activities?.proceeds_from_borrowing)}</td>
              <td style={{textAlign: 'right'}}>{formatAmount(lastYear.financing_activities?.proceeds_from_borrowing)}</td>
            </tr>
            <tr>
              <td style={{paddingLeft: '20px'}}>Repayment of Borrowings</td>
              <td></td>
              <td style={{textAlign: 'right'}}>{formatNegative(currentYear.financing_activities?.repayment_of_borrowing)}</td>
              <td style={{textAlign: 'right'}}>{formatNegative(lastYear.financing_activities?.repayment_of_borrowing)}</td>
            </tr>
            <tr>
              <td style={{paddingLeft: '20px'}}>Dividends Paid</td>
              <td style={{textAlign: 'center'}}>23</td>
              <td style={{textAlign: 'right'}}>{formatNegative(currentYear.financing_activities?.dividends_paid)}</td>
              <td style={{textAlign: 'right'}}>{formatNegative(lastYear.financing_activities?.dividends_paid)}</td>
            </tr>
            <tr>
              <td><strong>Net Cash from Financing Activities</strong></td>
              <td></td>
              <td style={{textAlign: 'right'}}><strong>{formatNegative(currentYear.financing_activities?.net_cash_from_financing)}</strong></td>
              <td style={{textAlign: 'right'}}><strong>{formatNegative(lastYear.financing_activities?.net_cash_from_financing)}</strong></td>
            </tr>
            
            <tr><td colSpan="4"></td></tr>
            
            <tr>
              <td><strong>Net Increase/(Decrease) in Cash and Cash Equivalents</strong></td>
              <td></td>
              <td style={{textAlign: 'right'}}><strong>{formatNegative(currentYear.net_change_in_cash)}</strong></td>
              <td style={{textAlign: 'right'}}><strong>{formatNegative(lastYear.net_change_in_cash)}</strong></td>
            </tr>
            <tr>
              <td>Cash and Cash Equivalents at Beginning of Period</td>
              <td></td>
              <td style={{textAlign: 'right'}}>{formatAmount(currentYear.cash_beginning)}</td>
              <td style={{textAlign: 'right'}}>{formatAmount(lastYear.cash_beginning)}</td>
            </tr>
            <tr>
              <td><strong>Cash and Cash Equivalents at End of Period</strong></td>
              <td></td>
              <td style={{textAlign: 'right'}}><strong>{formatAmount(currentYear.cash_ending)}</strong></td>
              <td style={{textAlign: 'right'}}><strong>{formatAmount(lastYear.cash_ending)}</strong></td>
            </tr>
          </tbody>
        </table>
        <p style={{ marginTop: '15px', fontSize: '12px', color: '#666', fontStyle: 'italic' }}>
          Schedules 18 to 23 form integral part of financial statements.
        </p>
      </div>
    </div>
  );
};

export default CashFlow;
