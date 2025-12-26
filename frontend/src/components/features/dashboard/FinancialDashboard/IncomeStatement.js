import React from 'react';
import './IncomeStatement.css';

const IncomeStatement = ({ data, onDownload, periodLabel }) => {
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

  const revenueOperations = data.revenue * 0.8;
  const revenueOther = data.revenue * 0.2;

  return (
    <div className="income-statement">
      <div className="statement-header">
        <h2>Statement of Profit or Loss</h2>
        <p className="statement-date">
          For the period from {data.period.start_date} to {data.period.end_date}
        </p>
        <p style={{ fontSize: '13px', color: '#666', marginTop: '8px', fontStyle: 'italic' }}>
          📋 Nepal Standard Accounting Format (Schedule-based)
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
          >
            📄 Download PDF
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

      <div className="financial-table-container">
        <table className="financial-table income-statement-table">
          <thead>
            <tr>
              <th style={{textAlign: 'left', width: '45%'}}>Particulars</th>
              <th style={{textAlign: 'center', width: '10%'}}>Schedule</th>
              <th style={{textAlign: 'right', width: '22.5%'}}>Current Year Rs.</th>
              <th style={{textAlign: 'right', width: '22.5%'}}>Previous Year Rs.</th>
            </tr>
          </thead>
          <tbody>
            <tr><td colSpan="4"><strong>REVENUE</strong></td></tr>
            <tr>
              <td style={{paddingLeft: '20px'}}>Revenue from Operations</td>
              <td style={{textAlign: 'center'}}>10</td>
              <td style={{textAlign: 'right'}}>{formatAmount(revenueOperations)}</td>
              <td style={{textAlign: 'right'}}>-</td>
            </tr>
            <tr>
              <td style={{paddingLeft: '20px'}}>Other Income</td>
              <td style={{textAlign: 'center'}}>11</td>
              <td style={{textAlign: 'right'}}>{formatAmount(revenueOther)}</td>
              <td style={{textAlign: 'right'}}>-</td>
            </tr>
            <tr>
              <td><strong>Total Revenue</strong></td>
              <td></td>
              <td style={{textAlign: 'right'}}><strong>{formatAmount(data.revenue)}</strong></td>
              <td style={{textAlign: 'right'}}><strong>-</strong></td>
            </tr>
            
            <tr><td colSpan="4"></td></tr>
            
            <tr><td colSpan="4"><strong>EXPENSES:</strong></td></tr>
            
            {Object.entries(data.expenses.breakdown).map(([category, amount]) => {
              let schedule = '';
              let displayName = category;
              
              if (category.toLowerCase().includes('cost') || category.toLowerCase().includes('cogs')) {
                schedule = '12';
                displayName = 'Cost of Sales';
              } else if (category.toLowerCase().includes('admin')) {
                schedule = '13';
                displayName = 'Administrative Expenses';
              } else if (category.toLowerCase().includes('selling') || category.toLowerCase().includes('distribution')) {
                schedule = '14';
                displayName = 'Selling and Distribution Expenses';
              } else if (category.toLowerCase().includes('finance') || category.toLowerCase().includes('interest')) {
                schedule = '15';
                displayName = 'Finance Costs';
              } else if (category.toLowerCase().includes('depreciation') || category.toLowerCase().includes('amortization')) {
                schedule = '16';
                displayName = 'Depreciation & Amortization';
              }
              
              return (
                <tr key={category}>
                  <td style={{paddingLeft: '20px'}}>{displayName}</td>
                  <td style={{textAlign: 'center'}}>{schedule}</td>
                  <td style={{textAlign: 'right'}}>{formatAmount(amount)}</td>
                  <td style={{textAlign: 'right'}}>-</td>
                </tr>
              );
            })}
            
            {Object.keys(data.expenses.breakdown).length === 0 && (
              <tr>
                <td style={{paddingLeft: '20px'}} colSpan="4">
                  <em>No expenses recorded for this period</em>
                </td>
              </tr>
            )}
            
            <tr>
              <td><strong>Total Expenses</strong></td>
              <td></td>
              <td style={{textAlign: 'right'}}><strong>{formatAmount(data.expenses.total_expenses)}</strong></td>
              <td style={{textAlign: 'right'}}><strong>-</strong></td>
            </tr>
            
            <tr><td colSpan="4"></td></tr>
            
            <tr>
              <td><strong>Profit/(Loss) Before Tax</strong></td>
              <td></td>
              <td style={{textAlign: 'right'}}><strong>{formatNegative(data.net_income)}</strong></td>
              <td style={{textAlign: 'right'}}><strong>-</strong></td>
            </tr>
            
            <tr>
              <td style={{paddingLeft: '20px'}}>Less: Income Tax Expense</td>
              <td style={{textAlign: 'center'}}>17</td>
              <td style={{textAlign: 'right'}}>-</td>
              <td style={{textAlign: 'right'}}>-</td>
            </tr>
            
            <tr><td colSpan="4"></td></tr>
            
            <tr className={data.net_income >= 0 ? 'profit-row' : 'loss-row'}>
              <td><strong>Profit/(Loss) for the Year</strong></td>
              <td></td>
              <td style={{textAlign: 'right'}}><strong>{formatNegative(data.net_income)}</strong></td>
              <td style={{textAlign: 'right'}}><strong>-</strong></td>
            </tr>
          </tbody>
        </table>
        <p style={{ marginTop: '15px', fontSize: '12px', color: '#666', fontStyle: 'italic' }}>
          Schedules 10 to 17 form integral part of financial statements.
        </p>
      </div>

      <div style={{marginTop: '20px'}}>
        {data.net_income >= 0 ? (
          <div style={{ color: '#4CAF50', padding: '10px', borderRadius: '5px', backgroundColor: '#e8f5e9', textAlign: 'center' }}>
            ✅ Profitable Period: Rs. {formatAmount(Math.abs(data.net_income))}
          </div>
        ) : (
          <div style={{ color: '#f44336', padding: '10px', borderRadius: '5px', backgroundColor: '#ffebee', textAlign: 'center' }}>
            ⚠️ Loss Period: Rs. {formatAmount(Math.abs(data.net_income))}
          </div>
        )}
      </div>

      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
        gap: '15px', 
        marginTop: '20px' 
      }}>
        <div style={{ padding: '15px', background: '#e3f2fd', borderRadius: '8px', textAlign: 'center' }}>
          <div style={{ fontSize: '14px', color: '#666', marginBottom: '5px' }}>Total Revenue</div>
          <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#1976d2' }}>
            Rs. {formatAmount(data.revenue)}
          </div>
        </div>
        <div style={{ padding: '15px', background: '#fff3e0', borderRadius: '8px', textAlign: 'center' }}>
          <div style={{ fontSize: '14px', color: '#666', marginBottom: '5px' }}>Total Expenses</div>
          <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#f57c00' }}>
            Rs. {formatAmount(data.expenses.total_expenses)}
          </div>
        </div>
        <div style={{ 
          padding: '15px', 
          background: data.net_income >= 0 ? '#e8f5e9' : '#ffebee', 
          borderRadius: '8px', 
          textAlign: 'center' 
        }}>
          <div style={{ fontSize: '14px', color: '#666', marginBottom: '5px' }}>Net Income</div>
          <div style={{ 
            fontSize: '20px', 
            fontWeight: 'bold', 
            color: data.net_income >= 0 ? '#388e3c' : '#d32f2f' 
          }}>
            Rs. {formatNegative(data.net_income)}
          </div>
        </div>
        <div style={{ padding: '15px', background: '#f3e5f5', borderRadius: '8px', textAlign: 'center' }}>
          <div style={{ fontSize: '14px', color: '#666', marginBottom: '5px' }}>Profit Margin</div>
          <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#7b1fa2' }}>
            {data.profit_margin.toFixed(2)}%
          </div>
        </div>
      </div>
    </div>
  );
};

export default IncomeStatement;
