import React, { useState, useEffect } from 'react';
import { FaTrash } from 'react-icons/fa';
import { FaPenToSquare } from 'react-icons/fa6';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../../../services/api';
import './BillDetails.css';

const BillDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [bill, setBill] = useState(null);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [editMode, setEditMode] = useState(false);
  const [formData, setFormData] = useState({});

  useEffect(() => {
    loadBillDetails();
    loadCategories();
  }, [id]);

  const loadBillDetails = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/bills/${id}/`);
      setBill(response.data);
      
      // Convert string tags to array for formData
      const billData = response.data;
      const formDataWithArrayTags = {
        ...billData,
        tags: billData.tags ? billData.tags.split(',').map(tag => tag.trim()).filter(tag => tag) : []
      };
      
      setFormData(formDataWithArrayTags);
    } catch (err) {
      console.error('Error loading bill details:', err);
      setError('Failed to load bill details');
    } finally {
      setLoading(false);
    }
  };

  const loadCategories = async () => {
    try {
      const response = await api.get('/bills/categories/');
      setCategories(response.data);
    } catch (err) {
      console.error('Error loading categories:', err);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      
      // Prepare data for update - exclude image and format tags properly
      const updateData = {
        vendor: formData.vendor || '',
        amount: parseFloat(formData.amount) || 0,
        tax_amount: parseFloat(formData.tax_amount) || 0,
        bill_date: formData.bill_date || formData.date,
        notes: formData.notes || '',
        category: formData.category || null,
        is_business_expense: formData.is_business || false,
        is_reimbursable: formData.is_reimbursable || false,
        // Convert tags array back to comma-separated string
        tags: Array.isArray(formData.tags) 
          ? formData.tags.join(', ') 
          : (formData.tags || '')
      };
      
      // Remove any null or undefined values
      Object.keys(updateData).forEach(key => {
        if (updateData[key] === null || updateData[key] === undefined) {
          delete updateData[key];
        }
      });
      
      const response = await api.put(`/bills/${id}/`, updateData);
      setBill(response.data);
      setFormData(response.data);
      setEditMode(false);
      alert('Bill updated successfully!');
    } catch (err) {
      console.error('Error saving bill:', err);
      alert(`Failed to save bill changes: ${JSON.stringify(err.response?.data) || err.message}`);
    } finally {
      setSaving(false);
    }
  };

  const handleRecategorize = async () => {
    try {
      setSaving(true);
      const response = await api.post('/bills/recategorize/', {
        bill_ids: [parseInt(id)]
      });
      
      // Reload bill details to get updated category
      await loadBillDetails();
      alert('Bill recategorized successfully!');
    } catch (err) {
      console.error('Error recategorizing bill:', err);
      alert('Failed to recategorize bill');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this bill? This action cannot be undone.')) {
      try {
        await api.delete(`/bills/${id}/`);
        navigate('/bills');
        alert('Bill deleted successfully');
      } catch (err) {
        console.error('Error deleting bill:', err);
        alert('Failed to delete bill');
      }
    }
  };

  const formatCurrency = (amount) => {
    const currencyCode = bill?.currency || 'USD';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currencyCode
    }).format(amount);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
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

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleTagsChange = (value) => {
    const tags = value.split(',').map(tag => tag.trim()).filter(tag => tag);
    setFormData(prev => ({
      ...prev,
      tags: tags
    }));
  };

  if (loading) {
    return (
      <div className="bill-details-loading">
        <div className="spinner"></div>
        <p>Loading bill details...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bill-details-error">
        <h3>Error</h3>
        <p>{error}</p>
        <div className="error-actions">
          <button onClick={loadBillDetails} className="retry-btn">Retry</button>
          <button onClick={() => navigate('/bills')} className="back-btn">Back to Bills</button>
        </div>
      </div>
    );
  }

  if (!bill) {
    return (
      <div className="bill-details-error">
        <h3>Bill Not Found</h3>
        <p>The requested bill could not be found.</p>
        <button onClick={() => navigate('/bills')} className="back-btn">Back to Bills</button>
      </div>
    );
  }

  return (
    <div className="bill-details">
      <div className="bill-details-header">
        <div className="header-left">
          <button onClick={() => navigate('/bills')} className="back-button">
            ← Back to Bills
          </button>
          <h1>Bill Details</h1>
        </div>
        <div className="header-actions">
          {editMode ? (
            <>
              <button 
                onClick={() => setEditMode(false)} 
                className="cancel-btn"
                disabled={saving}
              >
                Cancel
              </button>
              <button 
                onClick={handleSave} 
                className="save-btn"
                disabled={saving}
              >
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
            </>
          ) : (
            <>
              <button onClick={() => setEditMode(true)} className="edit-btn">
                <FaPenToSquare /> Edit
              </button>
              <button 
                onClick={handleRecategorize} 
                className="recategorize-btn"
                disabled={saving}
              >
                🔄 Recategorize
              </button>
              <button onClick={handleDelete} className="delete-btn">
                <FaTrash /> Delete
              </button>
            </>
          )}
        </div>
      </div>

      <div className="bill-details-content">
        {/* Bill Image Display */}
        {bill.image_url && (
          <div className="card-section">
            <h2 className="card-title">Bill Image</h2>
            <div className="info-card bill-image-card">
              <div className="bill-image-container">
              <img 
                src={bill.image_url} 
                alt="Bill" 
                onClick={() => window.open(bill.image_url, '_blank')}
                className="bill-detail-image"
              />
              <div className="image-actions">
                <button 
                  onClick={() => window.open(bill.image_url, '_blank')}
                  className="view-fullsize-btn"
                >
                  View Full Size
                </button>
              </div>
            </div>
            </div>
          </div>
        )}

        {/* Main Information Card */}
        <div className="card-section">
          <h2 className="card-title">Basic Information</h2>
          <div className="info-card main-info">
            <div className="info-grid">
            <div className="info-field">
              <label>Vendor:</label>
              {editMode ? (
                <input
                  type="text"
                  value={formData.vendor || ''}
                  onChange={(e) => handleInputChange('vendor', e.target.value)}
                  className="edit-input"
                />
              ) : (
                <span className="vendor-name">{bill.vendor || 'Unknown Vendor'}</span>
              )}
            </div>

            <div className="info-field">
              <label>Invoice Number:</label>
              <span>{bill.invoice_number || 'N/A'}</span>
            </div>

            <div className="info-field">
              <label>Amount:</label>
              {editMode ? (
                <input
                  type="number"
                  step="0.01"
                  value={formData.amount || ''}
                  onChange={(e) => handleInputChange('amount', parseFloat(e.target.value))}
                  className="edit-input"
                />
              ) : (
                <span className="amount">{formatCurrency(bill.amount)}</span>
              )}
            </div>

            <div className="info-field">
              <label>Tax Amount:</label>
              {editMode ? (
                <input
                  type="number"
                  step="0.01"
                  value={formData.tax_amount || ''}
                  onChange={(e) => handleInputChange('tax_amount', parseFloat(e.target.value))}
                  className="edit-input"
                />
              ) : (
                <span>{bill.tax_amount ? formatCurrency(bill.tax_amount) : 'N/A'}</span>
              )}
            </div>

            <div className="info-field">
              <label>Date:</label>
              {editMode ? (
                <input
                  type="date"
                  value={formData.bill_date || ''}
                  onChange={(e) => handleInputChange('bill_date', e.target.value)}
                  className="edit-input"
                />
              ) : (
                <span>{bill.bill_date ? formatDate(bill.bill_date) : 'N/A'}</span>
              )}
            </div>

            <div className="info-field full-width">
              <label>Notes:</label>
              {editMode ? (
                <textarea
                  value={formData.notes || ''}
                  onChange={(e) => handleInputChange('notes', e.target.value)}
                  className="edit-textarea"
                  rows="3"
                  placeholder="Add any additional notes..."
                />
              ) : (
                <span>{bill.notes || 'No notes'}</span>
              )}
            </div>
          </div>
          </div>
        </div>

        {/* Categorization Card */}
        <div className="card-section">
          <h2 className="card-title">Categorization</h2>
          <div className="info-card categorization-info">
          <div className="categorization-content">
            <div className="category-display">
              <label>Category:</label>
              {editMode ? (
                <select
                  value={formData.category || ''}
                  onChange={(e) => handleInputChange('category', e.target.value ? parseInt(e.target.value) : null)}
                  className="edit-select"
                >
                  <option value="">Uncategorized</option>
                  {categories.map(category => (
                    <option key={category.id} value={category.id}>
                      {category.name}
                    </option>
                  ))}
                </select>
              ) : (
                <div 
                  className="category-tag"
                  style={{ backgroundColor: getCategoryColor(bill.category) }}
                >
                  {getCategoryName(bill.category)}
                </div>
              )}
            </div>

            {bill.confidence_score && (
              <div className="confidence-display">
                <label>Confidence Score:</label>
                <div className="confidence-bar">
                  <div 
                    className="confidence-fill"
                    style={{ width: `${bill.confidence_score * 100}%` }}
                  ></div>
                  <span className="confidence-text">
                    {Math.round(bill.confidence_score * 100)}%
                  </span>
                </div>
              </div>
            )}

            <div className="tags-section">
              <label>Tags:</label>
              {editMode ? (
                <input
                  type="text"
                  value={formData.tags ? formData.tags.join(', ') : ''}
                  onChange={(e) => handleTagsChange(e.target.value)}
                  className="edit-input"
                  placeholder="Enter tags separated by commas"
                />
              ) : (
                <div className="tags-display">
                  {bill.tags && bill.tags.length > 0 ? (
                    bill.tags.split(',').map(tag => tag.trim()).filter(tag => tag).map(tag => (
                      <span key={tag} className="tag">{tag}</span>
                    ))
                  ) : (
                    <span className="no-tags">No tags</span>
                  )}
                </div>
              )}
            </div>
          </div>
          </div>
        </div>

        {/* Business Information Card */}
        <div className="card-section">
          <h2 className="card-title">Business Information</h2>
          <div className="info-card business-info">
          <div className="business-content">
            <div className="business-field">
              <label>Business Expense:</label>
              {editMode ? (
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={formData.is_business || false}
                    onChange={(e) => handleInputChange('is_business', e.target.checked)}
                  />
                  <span>This is a business expense</span>
                </label>
              ) : (
                <span className={`business-status ${bill.is_business ? 'business' : 'personal'}`}>
                  {bill.is_business ? 'Business' : 'Personal'}
                </span>
              )}
            </div>

            <div className="business-field">
              <label>Reimbursable:</label>
              {editMode ? (
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={formData.is_reimbursable || false}
                    onChange={(e) => handleInputChange('is_reimbursable', e.target.checked)}
                  />
                  <span>This is reimbursable</span>
                </label>
              ) : (
                <span className={`reimbursable-status ${bill.is_reimbursable ? 'yes' : 'no'}`}>
                  {bill.is_reimbursable ? 'Yes' : 'No'}
                </span>
              )}
            </div>
          </div>
        </div>
        </div>

        {/* Line Items Card */}
        {bill.line_items && bill.line_items.length > 0 && (
          <div className="card-section">
            <h2 className="card-title">Items/Goods ({bill.line_items.length})</h2>
            <div className="info-card line-items-info">
              <div className="line-items-table">
              <table>
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Description</th>
                    <th>Quantity</th>
                    <th>Rate</th>
                    <th>Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {bill.line_items.map((item, index) => (
                    <tr key={index}>
                      <td>{index + 1}</td>
                      <td className="item-description">{item.description || 'N/A'}</td>
                      <td className="item-quantity">{item.quantity || '-'}</td>
                      <td className="item-rate">
                        {item.rate ? formatCurrency(parseFloat(item.rate)) : '-'}
                      </td>
                      <td className="item-amount">
                        {item.amount ? formatCurrency(parseFloat(item.amount)) : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            </div>
          </div>
        )}

        {/* File Information Card */}
        <div className="card-section">
          <h2 className="card-title">File Information</h2>
          <div className="info-card file-info">
            <div className="file-content">
            <div className="file-field">
              <label>Original File:</label>
              {bill.image ? (
                <div className="file-display">
                  <a 
                    href={bill.image} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="file-link"
                  >
                    📄 View Original File
                  </a>
                </div>
              ) : (
                <span>No file attached</span>
              )}
            </div>

            <div className="file-field">
              <label>Upload Date:</label>
              <span>{formatDate(bill.created_at)}</span>
            </div>

            {bill.updated_at !== bill.created_at && (
              <div className="file-field">
                <label>Last Updated:</label>
                <span>{formatDate(bill.updated_at)}</span>
              </div>
            )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BillDetails;