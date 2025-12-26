import React, { useState, useEffect } from 'react';
import { useAuth } from '../../../../context/AuthContext';
import api from '../../../../services/api';
import './TransactionLedger.css';

const TransactionLedger = ({ dateRange, onDownload }) => {
  const { user } = useAuth();
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all'); // all, debit, credit
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchTransactions();
  }, [dateRange]);

  const fetchTransactions = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.get('/bills/', {
        params: {
          start_date: dateRange.startDate,
          end_date: dateRange.endDate,
          ordering: 'bill_date'
        }
      });
      
      setTransactions(response.data.results || response.data);
    } catch (err) {
      console.error('Error fetching transactions:', err);
      setError('Failed to load transactions');
    } finally {
      setLoading(false);
    }
  };

  const filteredTransactions = transactions.filter(t => {
    // Filter by type
    if (filter === 'debit' && !t.is_debit) return false;
    if (filter === 'credit' && t.is_debit) return false;
    
    // Filter by search term
    if (searchTerm) {
      const search = searchTerm.toLowerCase();
      return (
        (t.vendor && t.vendor.toLowerCase().includes(search)) ||
        (t.invoice_number && t.invoice_number.toLowerCase().includes(search)) ||
        (t.category_name && t.category_name.toLowerCase().includes(search)) ||
        (t.notes && t.notes.toLowerCase().includes(search))
      );
    }
    
    return true;
  });

  const calculateRunningBalance = () => {
    let balance = 0;
    return filteredTransactions.map(t => {
      if (t.is_debit) {
        balance -= parseFloat(t.amount || 0);
      } else {
        balance += parseFloat(t.amount || 0);
      }
      return { ...t, running_balance: balance };
    });
  };

  const transactionsWithBalance = calculateRunningBalance();

  const totals = filteredTransactions.reduce((acc, t) => {
    const amount = parseFloat(t.amount || 0);
    if (t.is_debit) {
      acc.totalDebits += amount;
    } else {
      acc.totalCredits += amount;
    }
    return acc;
  }, { totalDebits: 0, totalCredits: 0 });

  if (loading) {
    return <div className="loading">Loading transactions...</div>;
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  return (
    <div className="transaction-ledger">
      <div className="ledger-header">
        <h2>Transaction Ledger</h2>
        <p className="date-range">
          {dateRange.startDate} to {dateRange.endDate}
        </p>
        <button 
          onClick={onDownload} 
          className="download-btn excel"
          style={{
            background: '#2196F3',
            color: 'white',
            padding: '12px 24px',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '16px',
            fontWeight: '500',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            transition: 'all 0.3s ease'
          }}
          onMouseEnter={(e) => e.target.style.background = '#1976D2'}
          onMouseLeave={(e) => e.target.style.background = '#2196F3'}
        >
          📊 Export to Excel
        </button>
      </div>

      <div className="ledger-controls">
        <div className="search-box">
          <input
            type="text"
            placeholder="🔍 Search vendor, invoice, category..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
        </div>
        
        <div className="filter-buttons">
          <button
            className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
            onClick={() => setFilter('all')}
          >
            All ({transactions.length})
          </button>
          <button
            className={`filter-btn debit ${filter === 'debit' ? 'active' : ''}`}
            onClick={() => setFilter('debit')}
          >
            Debits ({transactions.filter(t => t.is_debit).length})
          </button>
          <button
            className={`filter-btn credit ${filter === 'credit' ? 'active' : ''}`}
            onClick={() => setFilter('credit')}
          >
            Credits ({transactions.filter(t => !t.is_debit).length})
          </button>
        </div>
      </div>

      <div className="totals-summary">
        <div className="total-item debit">
          <span className="label">Total Debits:</span>
          <span className="value">${totals.totalDebits.toFixed(2)}</span>
        </div>
        <div className="total-item credit">
          <span className="label">Total Credits:</span>
          <span className="value">${totals.totalCredits.toFixed(2)}</span>
        </div>
        <div className="total-item balance">
          <span className="label">Net Balance:</span>
          <span className={`value ${(totals.totalCredits - totals.totalDebits) >= 0 ? 'positive' : 'negative'}`}>
            ${(totals.totalCredits - totals.totalDebits).toFixed(2)}
          </span>
        </div>
      </div>

      <div className="ledger-table-container">
        <table className="ledger-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Invoice #</th>
              <th>Vendor</th>
              <th>Category</th>
              <th>Type</th>
              <th className="amount-col">Debit</th>
              <th className="amount-col">Credit</th>
              <th className="amount-col">Balance</th>
              <th>Notes</th>
            </tr>
          </thead>
          <tbody>
            {transactionsWithBalance.length === 0 ? (
              <tr>
                <td colSpan="9" className="no-data">
                  No transactions found for this period
                </td>
              </tr>
            ) : (
              transactionsWithBalance.map((transaction) => (
                <tr key={transaction.id} className={transaction.is_debit ? 'debit-row' : 'credit-row'}>
                  <td className="date-cell">
                    {transaction.bill_date ? new Date(transaction.bill_date).toLocaleDateString() : 'N/A'}
                  </td>
                  <td className="invoice-cell">{transaction.invoice_number || '-'}</td>
                  <td className="vendor-cell">{transaction.vendor || 'Unknown'}</td>
                  <td className="category-cell">
                    {transaction.category_name ? (
                      <span 
                        className="category-badge" 
                        style={{ backgroundColor: transaction.category_color || '#gray' }}
                      >
                        {transaction.category_name}
                      </span>
                    ) : (
                      <span className="uncategorized">Uncategorized</span>
                    )}
                  </td>
                  <td className="type-cell">
                    <span className={`type-badge ${transaction.is_debit ? 'debit' : 'credit'}`}>
                      {transaction.is_debit ? 'DR' : 'CR'}
                    </span>
                  </td>
                  <td className="amount-col debit">
                    {transaction.is_debit ? `$${parseFloat(transaction.amount || 0).toFixed(2)}` : '-'}
                  </td>
                  <td className="amount-col credit">
                    {!transaction.is_debit ? `$${parseFloat(transaction.amount || 0).toFixed(2)}` : '-'}
                  </td>
                  <td className={`amount-col balance ${transaction.running_balance >= 0 ? 'positive' : 'negative'}`}>
                    ${Math.abs(transaction.running_balance).toFixed(2)}
                    {transaction.running_balance < 0 && ' DR'}
                  </td>
                  <td className="notes-cell">{transaction.notes || '-'}</td>
                </tr>
              ))
            )}
          </tbody>
          <tfoot>
            <tr className="totals-row">
              <td colSpan="5"><strong>TOTALS</strong></td>
              <td className="amount-col"><strong>${totals.totalDebits.toFixed(2)}</strong></td>
              <td className="amount-col"><strong>${totals.totalCredits.toFixed(2)}</strong></td>
              <td className="amount-col">
                <strong>${Math.abs(totals.totalCredits - totals.totalDebits).toFixed(2)}</strong>
              </td>
              <td></td>
            </tr>
          </tfoot>
        </table>
      </div>

      <div className="ledger-info">
        <p>
          <strong>DR</strong> = Debit (Expense/Asset) | <strong>CR</strong> = Credit (Income/Revenue)
        </p>
        <p>
          Showing {filteredTransactions.length} of {transactions.length} transactions
        </p>
      </div>
    </div>
  );
};

export default TransactionLedger;
