import React, { useState, useEffect } from 'react';
import { FaTrash, FaEye } from 'react-icons/fa';
import { FaPenToSquare } from 'react-icons/fa6';
import { useNavigate } from 'react-router-dom';
import api from '../../../services/api';
import './BillManager.css';

const BillManager = () => {
  const [bills, setBills] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filterCategory, setFilterCategory] = useState('');
  const [filterMonth, setFilterMonth] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedBills, setSelectedBills] = useState([]);
  const [showBulkActions, setShowBulkActions] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError('');
      
      const [billsResponse, categoriesResponse] = await Promise.all([
        api.get('/bills/'),
        api.get('/bills/categories/')
      ]);
      
      // Handle different response structures
      const billsData = billsResponse.data.results || billsResponse.data || [];
      const categoriesData = categoriesResponse.data.results || categoriesResponse.data || [];
      
      setBills(Array.isArray(billsData) ? billsData : []);
      setCategories(Array.isArray(categoriesData) ? categoriesData : []);
    } catch (err) {
      console.error('Error loading data:', err);
      setError('Failed to load bills data');
      setBills([]); // Ensure bills is always an array
      setCategories([]); // Ensure categories is always an array
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteBill = async (billId) => {
    if (window.confirm('Are you sure you want to delete this bill?')) {
      try {
        await api.delete(`/bills/${billId}/`);
        setBills(bills.filter(bill => bill.id !== billId));
      } catch (err) {
        console.error('Error deleting bill:', err);
        alert('Failed to delete bill');
      }
    }
  };

  const handleBulkCategorize = async (categoryId) => {
    if (selectedBills.length === 0) return;
    
    try {
      await api.post('/bills/bulk_categorize/', {
        bill_ids: selectedBills,
        category_id: categoryId
      });
      
      loadData(); // Reload data to reflect changes
      setSelectedBills([]);
      setShowBulkActions(false);
      alert('Bills categorized successfully');
    } catch (err) {
      console.error('Error bulk categorizing:', err);
      alert('Failed to categorize bills');
    }
  };

  const handleBulkDelete = async () => {
    if (selectedBills.length === 0) {
      alert('No bills selected for deletion');
      return;
    }
    
    if (window.confirm(`Are you sure you want to delete ${selectedBills.length} bills?`)) {
      try {
        const response = await api.post('/bills/bulk_delete/', {
          bill_ids: selectedBills
        });
        
        loadData(); // Reload data to reflect changes
        setSelectedBills([]);
        setShowBulkActions(false);
        alert(`${response.data.deleted_count || selectedBills.length} bills deleted successfully`);
      } catch (err) {
        console.error('Error bulk deleting:', err);
        alert(`Failed to delete bills: ${err.response?.data?.error || err.message}`);
      }
    }
  };

  const toggleBillSelection = (billId) => {
    if (selectedBills.includes(billId)) {
      setSelectedBills(selectedBills.filter(id => id !== billId));
    } else {
      setSelectedBills([...selectedBills, billId]);
    }
  };

  const handleSelectAll = () => {
    if (selectedBills.length === filteredBills.length) {
      // Deselect all
      setSelectedBills([]);
    } else {
      // Select all filtered bills
      setSelectedBills(filteredBills.map(bill => bill.id));
    }
  };

  const filteredBills = (bills || []).filter(bill => {
    const matchesCategory = !filterCategory || (bill.category && bill.category.toString() === filterCategory);
    // Use bill_date for filtering by month, fall back to created_at
    const dateToFilter = bill.bill_date || bill.created_at;
    const matchesMonth = !filterMonth || dateToFilter?.startsWith(filterMonth);
    
    const matchesSearch = !searchTerm || 
      bill.vendor?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      bill.ocr_text?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      bill.amount?.toString().includes(searchTerm);
    
    return matchesCategory && matchesMonth && matchesSearch;
  });

  const formatCurrency = (amount, currencyCode = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currencyCode
    }).format(amount);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getCategoryName = (categoryId) => {
    const category = categories.find(cat => cat.id === categoryId);
    return category ? category.name : 'Uncategorized';
  };

  const getCategoryColor = (categoryId) => {
    const category = categories.find(cat => cat.id === categoryId);
    return category ? category.color : '#95a5a6';
  };

  if (loading) {
    return (
      <div className="bill-manager-loading">
        <div className="spinner"></div>
        <p>Loading bills...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bill-manager-error">
        <h3>Error</h3>
        <p>{error}</p>
        <button onClick={loadData} className="retry-btn">Retry</button>
      </div>
    );
  }

  return (
    <div className="bill-manager">
      <div className="bill-manager-header">
        <h1>Bill Management</h1>
        <button 
          className="add-bill-btn"
          onClick={() => navigate('/upload')}
        >
          Add New Bill
        </button>
      </div>

      {/* Filters and Search */}
      <div className="filters-section">
        <div className="filter-group">
          <label htmlFor="search">Search:</label>
          <input
            type="text"
            id="search"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by vendor, description, or amount..."
            className="search-input"
          />
        </div>
        
        <div className="filter-group">
          <label htmlFor="category-filter">Category:</label>
          <select
            id="category-filter"
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
            className="filter-select"
          >
            <option value="">All Categories</option>
            {categories.map(category => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </select>
        </div>
        
        <div className="filter-group">
          <label htmlFor="month-filter">Month:</label>
          <input
            type="month"
            id="month-filter"
            value={filterMonth}
            onChange={(e) => setFilterMonth(e.target.value)}
            className="filter-select"
            min="2020-01"
            max="2030-12"
          />
        </div>
        
        <div className="filter-group">
          <button
            onClick={() => {
              setFilterCategory('');
              setFilterMonth('');
              setSearchTerm('');
            }}
            className="clear-filters-btn"
          >
            Clear Filters
          </button>
        </div>

        <div className="filter-group">
          <button
            onClick={handleSelectAll}
            className="select-all-btn"
            disabled={filteredBills.length === 0}
          >
            {selectedBills.length === filteredBills.length && filteredBills.length > 0
              ? `Deselect All (${filteredBills.length})`
              : `Select All (${filteredBills.length})`}
          </button>
        </div>
      </div>

      {/* Bulk Actions */}
      {selectedBills.length > 0 && (
        <div className="bulk-actions">
          <div className="bulk-actions-header">
            <span>{selectedBills.length} bill(s) selected</span>
            <button
              onClick={() => setShowBulkActions(!showBulkActions)}
              className="bulk-toggle-btn"
            >
              {showBulkActions ? 'Hide Actions' : 'Show Actions'}
            </button>
          </div>
          
          {showBulkActions && (
            <div className="bulk-actions-menu">
              <div className="bulk-categorize">
                <label>Re-categorize as:</label>
                <select 
                  onChange={(e) => e.target.value && handleBulkCategorize(e.target.value)}
                  className="bulk-select"
                >
                  <option value="">Select category...</option>
                  {categories.map(category => (
                    <option key={category.id} value={category.id}>
                      {category.name}
                    </option>
                  ))}
                </select>
              </div>
              <button onClick={handleBulkDelete} className="bulk-delete-btn">
                <FaTrash /> Delete Selected
              </button>
            </div>
          )}
        </div>
      )}

      {/* Bills List */}
      <div className="bills-container">
        <div className="bills-header">
          <div className="bills-count">
            {filteredBills.length} of {bills.length} bills
          </div>
        </div>

        {filteredBills.length === 0 ? (
          <div className="no-bills">
            <p>No bills found matching your criteria.</p>
            {searchTerm || filterCategory || filterMonth ? (
              <button onClick={() => {
                setFilterCategory('');
                setFilterMonth('');
                setSearchTerm('');
              }} className="clear-filters-btn">
                Clear filters to see all bills
              </button>
            ) : (
              <button onClick={() => navigate('/upload')} className="add-bill-btn">
                Upload your first bill
              </button>
            )}
          </div>
        ) : (
          <div className="bills-grid">
            {filteredBills.map(bill => (
              <div key={bill.id} className="bill-card">
                <div className="bill-card-header">
                  <input
                    type="checkbox"
                    checked={selectedBills.includes(bill.id)}
                    onChange={() => toggleBillSelection(bill.id)}
                    className="bill-checkbox"
                  />
                  <span className="bill-date">{formatDate(bill.bill_date || bill.created_at)}</span>
                  <div className="bill-actions">
                    <button 
                      onClick={() => navigate(`/bills/${bill.id}`)}
                      className="edit-btn"
                      title="View Bill Details"
                    >
                      <FaEye />
                    </button>
                    <button 
                      onClick={() => handleDeleteBill(bill.id)}
                      className="delete-btn"
                      title="Delete Bill"
                    >
                      <FaTrash />
                    </button>
                  </div>
                </div>
                
                <div className="bill-card-body">
                  {bill.image_url && (
                    <div className="bill-image-preview">
                      <img 
                        src={bill.image_url} 
                        alt={`Bill from ${bill.vendor || 'Unknown'}`}
                        onClick={() => window.open(bill.image_url, '_blank')}
                        title="Click to view full size"
                      />
                    </div>
                  )}
                  <div className="bill-vendor">
                    {bill.vendor || 'Unknown Vendor'}
                  </div>
                  <div className="bill-amount">
                    {formatCurrency(bill.amount, bill.currency)}
                  </div>
                  {bill.line_items && bill.line_items.length > 0 && (
                    <div className="bill-items-count">
                      📦 {bill.line_items.length} item{bill.line_items.length !== 1 ? 's' : ''}
                    </div>
                  )}
                </div>
                
                <div className="bill-card-footer">
                  <div 
                    className="bill-category-tag"
                    style={{ backgroundColor: getCategoryColor(bill.category) }}
                  >
                    {getCategoryName(bill.category)}
                  </div>
                  {bill.confidence_score && (
                    <div className="confidence-score">
                      Confidence: {Math.round(bill.confidence_score * 100)}%
                    </div>
                  )}
                  {bill.tags && bill.tags.length > 0 && (
                    <div className="bill-tags">
                      {(typeof bill.tags === 'string' 
                        ? bill.tags.split(',').map(tag => tag.trim()).filter(tag => tag)
                        : bill.tags
                      ).map(tag => (
                        <span key={tag} className="tag">{tag}</span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default BillManager;