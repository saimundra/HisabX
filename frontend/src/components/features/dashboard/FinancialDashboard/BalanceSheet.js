import React from 'react';
import './BalanceSheet.css';

const BalanceSheet = ({ data, onDownload, periodLabel }) => {
  if (!data) {
    return <div className="balance-sheet-loading">Loading balance sheet data...</div>;
  }

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

  // Calculate previous year date for comparison (same as in FinancialDashboard)
  const currentDate = data.as_of_date ? new Date(data.as_of_date) : new Date();
  const previousYearDate = new Date(currentDate);
  previousYearDate.setFullYear(currentDate.getFullYear() - 1);
  
  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
  };

  return (
    <div className="balance-sheet">
      <div className="statement-header">
        <h2>Balance Sheet</h2>
        <p className="statement-date">As of {formatDate(data.as_of_date)}</p>
        <p style={{ fontSize: '13px', color: '#666', marginTop: '8px', fontStyle: 'italic' }}>
          📋 Nepal Standard Accounting Format with Schedule numbers
        </p>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '15px', marginTop: '20px' }}>
          <button 
            onClick={() => onDownload('pdf')} 
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
            title="Download in Nepal Standard format with schedules"
          >
            📄 Download PDF (Nepal Format)
          </button>
          <button 
            onClick={() => onDownload('excel')} 
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

      {/* Nepal Standard Format Table */}
      <div className="financial-table-container">
        <table className="financial-table balance-sheet-table">
          <thead>
            <tr>
              <th style={{textAlign: 'left', width: '45%'}}>Particulars</th>
              <th style={{textAlign: 'center', width: '10%'}}>Schedule</th>
              <th style={{textAlign: 'right', width: '22.5%'}}>
                As on {formatDate(data.as_of_date)}<br/>
                Rs.
              </th>
              <th style={{textAlign: 'right', width: '22.5%'}}>
                As on {formatDate(previousYearDate.toISOString().split('T')[0])}<br/>
                Rs.
              </th>
            </tr>
          </thead>
          <tbody>
            {/* ASSETS SECTION */}
            <tr>
              <td colSpan="4"><strong>ASSETS</strong></td>
            </tr>
            
            {/* Non-Current Assets */}
            <tr>
              <td colSpan="4"><strong>Non Current Assets</strong></td>
            </tr>
            <tr>
              <td style={{paddingLeft: '20px'}}>Property, Plant & Equipment</td>
              <td style={{textAlign: 'center'}}>1</td>
              <td style={{textAlign: 'right'}}>{formatAmount(data.assets?.non_current_assets?.property_plant_equipment)}</td>
              <td style={{textAlign: 'right'}}>-</td>
            </tr>
            <tr>
              <td style={{paddingLeft: '20px'}}>Other Receivables</td>
              <td style={{textAlign: 'center'}}></td>
              <td style={{textAlign: 'right'}}>{formatAmount(data.assets?.non_current_assets?.other_receivables)}</td>
              <td style={{textAlign: 'right'}}>-</td>
            </tr>
            <tr>
              <td style={{paddingLeft: '20px'}}>Investments</td>
              <td style={{textAlign: 'center'}}></td>
              <td style={{textAlign: 'right'}}>{formatAmount(data.assets?.non_current_assets?.investments)}</td>
              <td style={{textAlign: 'right'}}>-</td>
            </tr>
            <tr>
              <td style={{paddingLeft: '20px'}}>Loans And Advances</td>
              <td style={{textAlign: 'center'}}></td>
              <td style={{textAlign: 'right'}}>{formatAmount(data.assets?.non_current_assets?.loans_advances)}</td>
              <td style={{textAlign: 'right'}}>-</td>
            </tr>
            <tr className="subtotal-row">
              <td><strong>Total Non-Current Assets</strong></td>
              <td></td>
              <td style={{textAlign: 'right'}}><strong>{formatAmount(data.assets?.non_current_assets?.total_non_current_assets)}</strong></td>
              <td style={{textAlign: 'right'}}><strong>-</strong></td>
            </tr>
            
            <tr><td colSpan="4"></td></tr>
            
            {/* Current Assets */}
            <tr>
              <td colSpan="4"><strong>Current Assets</strong></td>
            </tr>
            <tr>
              <td style={{paddingLeft: '20px'}}>Inventories</td>
              <td style={{textAlign: 'center'}}>2</td>
              <td style={{textAlign: 'right'}}>{formatAmount(data.assets?.current_assets?.inventories)}</td>
              <td style={{textAlign: 'right'}}>-</td>
            </tr>
            <tr>
              <td style={{paddingLeft: '20px'}}>Advance Income Tax</td>
              <td style={{textAlign: 'center'}}>3</td>
              <td style={{textAlign: 'right'}}>{formatAmount(data.assets?.current_assets?.advance_income_tax)}</td>
              <td style={{textAlign: 'right'}}>-</td>
            </tr>
            <tr>
              <td style={{paddingLeft: '20px'}}>Trade & Other Receivables</td>
              <td style={{textAlign: 'center'}}>4</td>
              <td style={{textAlign: 'right'}}>{formatAmount(data.assets?.current_assets?.trade_receivables)}</td>
              <td style={{textAlign: 'right'}}>-</td>
            </tr>
            <tr>
              <td style={{paddingLeft: '20px'}}>Cash & Cash Equivalents</td>
              <td style={{textAlign: 'center'}}>5</td>
              <td style={{textAlign: 'right'}}>{formatAmount(data.assets?.current_assets?.cash)}</td>
              <td style={{textAlign: 'right'}}>-</td>
            </tr>
            <tr>
              <td style={{paddingLeft: '20px'}}>Vat Receivable</td>
              <td style={{textAlign: 'center'}}></td>
              <td style={{textAlign: 'right'}}>{formatAmount(data.assets?.current_assets?.vat_receivable)}</td>
              <td style={{textAlign: 'right'}}>-</td>
            </tr>
            <tr className="subtotal-row">
              <td><strong>Total Current Assets</strong></td>
              <td></td>
              <td style={{textAlign: 'right'}}><strong>{formatAmount(data.assets?.current_assets?.total_current_assets)}</strong></td>
              <td style={{textAlign: 'right'}}><strong>-</strong></td>
            </tr>
            
            <tr><td colSpan="4"></td></tr>
            
            <tr className="total-row">
              <td><strong>Total Assets</strong></td>
              <td></td>
              <td style={{textAlign: 'right'}}><strong>{formatAmount(data.assets?.total_assets)}</strong></td>
              <td style={{textAlign: 'right'}}><strong>-</strong></td>
            </tr>
            
            {/* EQUITY AND LIABILITIES SECTION */}
            <tr><td colSpan="4"></td></tr>
            
            <tr>
              <td colSpan="4"><strong>EQUITY</strong></td>
            </tr>
            <tr>
              <td style={{paddingLeft: '20px'}}>Share Capital</td>
              <td style={{textAlign: 'center'}}>6</td>
              <td style={{textAlign: 'right'}}>{formatAmount(data.equity?.share_capital)}</td>
              <td style={{textAlign: 'right'}}>-</td>
            </tr>
            <tr>
              <td style={{paddingLeft: '20px'}}>Reserves</td>
              <td style={{textAlign: 'center'}}></td>
              <td style={{textAlign: 'right'}}>{formatNegative(data.equity?.reserves)}</td>
              <td style={{textAlign: 'right'}}>-</td>
            </tr>
            <tr className="subtotal-row">
              <td><strong>Total Equity</strong></td>
              <td></td>
              <td style={{textAlign: 'right'}}><strong>{formatAmount(data.equity?.total_equity)}</strong></td>
              <td style={{textAlign: 'right'}}><strong>-</strong></td>
            </tr>
            
            <tr><td colSpan="4"></td></tr>
            
            {/* LIABILITIES */}
            <tr>
              <td colSpan="4"><strong>LIABILITIES</strong></td>
            </tr>
            
            {/* Non-Current Liabilities */}
            <tr>
              <td colSpan="4"><strong>Non Current Liabilities</strong></td>
            </tr>
            <tr>
              <td style={{paddingLeft: '20px'}}>Loans & Borrowings</td>
              <td style={{textAlign: 'center'}}>7</td>
              <td style={{textAlign: 'right'}}>{formatAmount(data.liabilities?.non_current_liabilities?.loans_borrowings)}</td>
              <td style={{textAlign: 'right'}}>-</td>
            </tr>
            <tr>
              <td style={{paddingLeft: '20px'}}>Provisions</td>
              <td style={{textAlign: 'center'}}></td>
              <td style={{textAlign: 'right'}}>{formatAmount(data.liabilities?.non_current_liabilities?.provisions)}</td>
              <td style={{textAlign: 'right'}}>-</td>
            </tr>
            <tr className="subtotal-row">
              <td><strong>Total Non-Current Liabilities</strong></td>
              <td></td>
              <td style={{textAlign: 'right'}}><strong>{formatAmount(data.liabilities?.non_current_liabilities?.total_non_current_liabilities)}</strong></td>
              <td style={{textAlign: 'right'}}><strong>-</strong></td>
            </tr>
            
            <tr><td colSpan="4"></td></tr>
            
            {/* Current Liabilities */}
            <tr>
              <td colSpan="4"><strong>Current Liabilities</strong></td>
            </tr>
            <tr>
              <td style={{paddingLeft: '20px'}}>Loans & Borrowings</td>
              <td style={{textAlign: 'center'}}>8</td>
              <td style={{textAlign: 'right'}}>{formatAmount(data.liabilities?.current_liabilities?.short_term_loans)}</td>
              <td style={{textAlign: 'right'}}>-</td>
            </tr>
            <tr>
              <td style={{paddingLeft: '20px'}}>Trade & other payables</td>
              <td style={{textAlign: 'center'}}>9</td>
              <td style={{textAlign: 'right'}}>{formatAmount(data.liabilities?.current_liabilities?.trade_payables)}</td>
              <td style={{textAlign: 'right'}}>-</td>
            </tr>
            <tr>
              <td style={{paddingLeft: '20px'}}>Income Tax Liability</td>
              <td style={{textAlign: 'center'}}></td>
              <td style={{textAlign: 'right'}}>{formatAmount(data.liabilities?.current_liabilities?.income_tax_liability)}</td>
              <td style={{textAlign: 'right'}}>-</td>
            </tr>
            <tr>
              <td style={{paddingLeft: '20px'}}>Vat Payable</td>
              <td style={{textAlign: 'center'}}></td>
              <td style={{textAlign: 'right'}}>{formatAmount(data.liabilities?.current_liabilities?.vat_payable)}</td>
              <td style={{textAlign: 'right'}}>-</td>
            </tr>
            <tr className="subtotal-row">
              <td><strong>Total Current Liabilities</strong></td>
              <td></td>
              <td style={{textAlign: 'right'}}><strong>{formatAmount(data.liabilities?.current_liabilities?.total_current_liabilities)}</strong></td>
              <td style={{textAlign: 'right'}}><strong>-</strong></td>
            </tr>
            
            <tr><td colSpan="4"></td></tr>
            
            <tr className="subtotal-row">
              <td><strong>Total Liabilities</strong></td>
              <td></td>
              <td style={{textAlign: 'right'}}><strong>{formatAmount(data.liabilities?.total_liabilities)}</strong></td>
              <td style={{textAlign: 'right'}}><strong>-</strong></td>
            </tr>
            
            <tr><td colSpan="4"></td></tr>
            
            <tr className="total-row">
              <td><strong>Total Equity & Liabilities</strong></td>
              <td></td>
              <td style={{textAlign: 'right'}}><strong>{formatAmount((data.equity?.total_equity || 0) + (data.liabilities?.total_liabilities || 0))}</strong></td>
              <td style={{textAlign: 'right'}}><strong>-</strong></td>
            </tr>
          </tbody>
        </table>
        
        <p style={{
          marginTop: '20px',
          fontSize: '12px',
          fontStyle: 'italic',
          color: '#666',
          textAlign: 'center'
        }}>
          Schedules 1 to 12 form integral part of financial statements.
        </p>
      </div>

      {/* Balance Check */}
      <div className={`balance-check ${data.balanced ? 'balanced' : 'unbalanced'}`}>
        {data.balanced 
          ? '✓ Balance Sheet is Balanced' 
          : '⚠ Balance Sheet is Unbalanced'}
      </div>
    </div>
  );
};

export default BalanceSheet;
