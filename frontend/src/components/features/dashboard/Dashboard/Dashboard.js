import React, { useState, useEffect } from 'react';
import { 
  PieChart, 
  Pie, 
  Cell, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend,
  ResponsiveContainer 
} from 'recharts';
import api from '../../../../services/api';
import './Dashboard.css';

const Dashboard = () => {
  const [bills, setBills] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const formatCurrency = (amount, currencyCode = 'USD') => {
    const numAmount = parseFloat(amount) || 0;
    
    const currencySymbols = {
      'USD': '$',
      'EUR': '€',
      'GBP': '£',
      'INR': '₹',
      'NPR': 'Rs.',
      'CAD': 'CA$',
      'AUD': 'A$'
    };

    const symbol = currencySymbols[currencyCode] || currencyCode;
    
    try {
      const formatted = new Intl.NumberFormat('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(numAmount);
      
      return `${symbol}${formatted}`;
    } catch (error) {
      return `${symbol}${numAmount.toFixed(2)}`;
    }
  };

  // Get the most common currency from bills
  const getPrimaryCurrency = () => {
    if (!bills || bills.length === 0) return 'USD';
    
    const currencyCounts = {};
    bills.forEach(bill => {
      const currency = bill.currency || 'USD';
      currencyCounts[currency] = (currencyCounts[currency] || 0) + 1;
    });
    
    return Object.keys(currencyCounts).reduce((a, b) => 
      currencyCounts[a] > currencyCounts[b] ? a : b
    );
  };

  const fetchDashboardData = async () => {
    try {
      // Fetch bills and categories using our api service
      const [billsResponse, categoriesResponse] = await Promise.all([
        api.get('/bills/'),
        api.get('/bills/categories/')
      ]);
      
      const billsData = billsResponse.data.results || billsResponse.data;
      const categoriesData = categoriesResponse.data.results || categoriesResponse.data;

      setBills(billsData);
      setCategories(categoriesData);
    } catch (err) {
      console.error('Dashboard fetch error:', err);
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const getCategoryBreakdown = () => {
    if (!bills || bills.length === 0) {
      return [];
    }
    
    const categoryTotals = {};
    
    bills.forEach(bill => {
      const categoryName = bill.category_name || 'Uncategorized';
      const amount = parseFloat(bill.amount) || 0;
      
      if (categoryTotals[categoryName]) {
        categoryTotals[categoryName] += amount;
      } else {
        categoryTotals[categoryName] = amount;
      }
    });
    
    const result = Object.entries(categoryTotals)
      .filter(([name, value]) => value > 0) // Only include categories with amounts > 0
      .map(([name, value]) => ({
        name,
        value: parseFloat(value.toFixed(2)),
        count: bills.filter(bill => 
          (bill.category_name || 'Uncategorized') === name
        ).length
      }));
    
    return result;
  };

  const getMonthlySpending = () => {
    const monthlyTotals = {};
    
    bills.forEach(bill => {
      // Use the actual bill date instead of created_at
      const billDate = bill.bill_date || bill.created_at;
      const date = new Date(billDate);
      const monthKey = `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}`;
      const amount = parseFloat(bill.amount) || 0;
      
      if (monthlyTotals[monthKey]) {
        monthlyTotals[monthKey] += amount;
      } else {
        monthlyTotals[monthKey] = amount;
      }
    });

    // Sort by date and take only the last 6 months
    return Object.entries(monthlyTotals)
      .sort(([a], [b]) => b.localeCompare(a)) // Sort descending (newest first)
      .slice(0, 6) // Take only the last 6 months
      .reverse() // Reverse to show oldest to newest on chart
      .map(([month, amount]) => ({
        month,
        amount: amount.toFixed(2)
      }));
  };

  const getTotalSpending = () => {
    return bills.reduce((total, bill) => total + (parseFloat(bill.amount) || 0), 0);
  };

  const getAutoCategorizedCount = () => {
    return bills.filter(bill => bill.is_auto_categorized).length;
  };

  const COLORS = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD'];

  if (loading) {
    return <div className="dashboard-loading">Loading dashboard...</div>;
  }

  if (error) {
    return <div className="dashboard-error">{error}</div>;
  }

  const categoryData = getCategoryBreakdown();
  const monthlyData = getMonthlySpending();
  const totalSpending = getTotalSpending();
  const autoCategorizedCount = getAutoCategorizedCount();
  const primaryCurrency = getPrimaryCurrency();

  return (
    <div className="dashboard">
      <h1>Expense Dashboard</h1>
      
      {/* Summary Stats */}
      <div className="stats-grid">
        <div className="stat-card">
          <h3>Total Spending</h3>
          <div className="stat-value">{formatCurrency(totalSpending, primaryCurrency)}</div>
        </div>
        <div className="stat-card">
          <h3>Total Bills</h3>
          <div className="stat-value">{bills.length}</div>
        </div>
        <div className="stat-card">
          <h3>Auto-Categorized</h3>
          <div className="stat-value">{autoCategorizedCount}/{bills.length}</div>
        </div>
        <div className="stat-card">
          <h3>Categories</h3>
          <div className="stat-value">{categoryData.length}</div>
        </div>
      </div>

      {/* Charts */}
      <div className="charts-grid">
        {/* Category Breakdown Pie Chart */}
                <div className="chart-container">
          <h3>Spending by Category</h3>
          {categoryData.length > 0 ? (
            <ResponsiveContainer width="100%" height={450}>
              <PieChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                <Pie
                  data={categoryData}
                  cx="35%"
                  cy="50%"
                  labelLine={false}
                  outerRadius={85}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {categoryData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => [formatCurrency(value, primaryCurrency), 'Amount']} />
                <Legend 
                  layout="vertical" 
                  align="right" 
                  verticalAlign="middle"
                  formatter={(value, entry) => {
                    const total = categoryData.reduce((sum, item) => sum + item.value, 0);
                    const percent = ((entry.payload.value / total) * 100).toFixed(0);
                    return `${value} - ${percent}% (${formatCurrency(entry.payload.value, primaryCurrency)})`;
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="no-data">
              <p>No spending data available</p>
              <p>Upload some bills to see your spending breakdown</p>
            </div>
          )}
        </div>

        {/* Monthly Spending Bar Chart */}
        <div className="chart-container">
          <h3>Monthly Spending</h3>
          {monthlyData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={monthlyData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip formatter={(value) => [formatCurrency(value, primaryCurrency), 'Amount']} />
                <Bar dataKey="amount" fill="#4ECDC4" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="no-data">No monthly data available</div>
          )}
        </div>
      </div>

      {/* Recent Bills */}
      <div className="recent-bills">
        <h3>Recent Bills</h3>
        <div className="bills-list">
          {bills.slice(0, 5).map(bill => (
            <div key={bill.id} className="bill-item">
              <div className="bill-vendor">{bill.vendor || 'Unknown Vendor'}</div>
              <div className="bill-amount">{formatCurrency(bill.amount, bill.currency)}</div>
              <div className="bill-category">
                {bill.category_name ? (
                  <span className={`category-tag ${bill.is_auto_categorized ? 'auto' : 'manual'}`}>
                    {bill.category_name}
                    {bill.is_auto_categorized && ' (Auto)'}
                  </span>
                ) : (
                  <span className="category-tag uncategorized">Uncategorized</span>
                )}
              </div>
              <div className="bill-date">
                {new Date(bill.bill_date || bill.created_at).toLocaleDateString()}
              </div>
            </div>
          ))}
          {bills.length === 0 && (
            <div className="no-data">No bills uploaded yet</div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;