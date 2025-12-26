import React, { useState, useEffect } from 'react';
import { FaTrash } from 'react-icons/fa';
import { FaPenToSquare } from 'react-icons/fa6';
import api from '../../../services/api';
import './CategoryManager.css';

const CategoryManager = () => {
  const [categories, setCategories] = useState([]);
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showAddCategory, setShowAddCategory] = useState(false);
  const [showAddRule, setShowAddRule] = useState(false);
  const [editingCategory, setEditingCategory] = useState(null);
  const [editingRule, setEditingRule] = useState(null);

  const [categoryForm, setCategoryForm] = useState({
    name: '',
    type: 'expense',
    description: '',
    color: '#3498db',
    keywords: ''
  });

  const [ruleForm, setRuleForm] = useState({
    name: '',
    category: '',
    keywords: '',
    vendor_patterns: '',
    amount_min: '',
    amount_max: '',
    is_active: true
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError('');
      
      // Load categories from the proper endpoint that includes IDs
      const categoriesResponse = await api.get('/categories/');
      // Handle both paginated and non-paginated responses
      const categoriesData = categoriesResponse.data.results || categoriesResponse.data || [];
      setCategories(Array.isArray(categoriesData) ? categoriesData : []);
      
      // Try to load rules, but don't fail if endpoint doesn't exist
      try {
        const rulesResponse = await api.get('/categories/rules/');
        setRules(rulesResponse.data || []);
      } catch (ruleError) {

        setRules([]); // Set empty array if rules endpoint doesn't exist
      }
      
    } catch (err) {
      console.error('Error loading category data:', err);
      setError(`Failed to load category data: ${err.response?.data?.detail || err.message}`);
      setCategories([]);
      setRules([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCategorySubmit = async (e) => {
    e.preventDefault();
    try {
      const formData = {
        ...categoryForm,
        keywords: categoryForm.keywords.split(',').map(k => k.trim()).filter(k => k).join(', ')
      };

      if (editingCategory) {
        await api.put(`/categories/${editingCategory.id}/`, formData);
      } else {
        await api.post('/categories/', formData);
      }
      
      await loadData();
      resetCategoryForm();
      alert(editingCategory ? 'Category updated successfully!' : 'Category created successfully!');
    } catch (err) {
      console.error('Error saving category:', err);
      alert(`Failed to save category: ${err.response?.data?.detail || err.message}`);
    }
  };

  const handleRuleSubmit = async (e) => {
    e.preventDefault();
    try {
      const formData = {
        ...ruleForm,
        keywords: ruleForm.keywords.split(',').map(k => k.trim()).filter(k => k),
        vendor_patterns: ruleForm.vendor_patterns.split(',').map(v => v.trim()).filter(v => v),
        amount_min: ruleForm.amount_min ? parseFloat(ruleForm.amount_min) : null,
        amount_max: ruleForm.amount_max ? parseFloat(ruleForm.amount_max) : null
      };

      if (editingRule) {
        await api.put(`/categories/rules/${editingRule.id}/`, formData);
      } else {
        await api.post('/categories/rules/', formData);
      }
      
      await loadData();
      resetRuleForm();
      alert(editingRule ? 'Rule updated successfully!' : 'Rule created successfully!');
    } catch (err) {
      console.error('Error saving rule:', err);
      alert('Failed to save rule');
    }
  };

  const handleDeleteCategory = async (categoryId) => {
    if (window.confirm('Are you sure you want to delete this category? Bills using this category will become uncategorized.')) {
      try {
        await api.delete(`/categories/${categoryId}/`);
        await loadData();
        alert('Category deleted successfully');
      } catch (err) {
        console.error('Error deleting category:', err);
        alert(`Failed to delete category: ${err.response?.data?.detail || err.message}`);
      }
    }
  };

  const handleDeleteRule = async (ruleId) => {
    if (window.confirm('Are you sure you want to delete this categorization rule?')) {
      try {
        await api.delete(`/categories/rules/${ruleId}/`);
        await loadData();
        alert('Rule deleted successfully');
      } catch (err) {
        console.error('Error deleting rule:', err);
        alert('Failed to delete rule');
      }
    }
  };

  const startEditCategory = (category) => {
    setEditingCategory(category);
    setCategoryForm({
      name: category.name,
      type: category.type,
      description: category.description || '',
      color: category.color,
      keywords: typeof category.keywords === 'string' 
        ? category.keywords 
        : (Array.isArray(category.keywords) ? category.keywords.join(', ') : '')
    });
    setShowAddCategory(true);
  };

  const startEditRule = (rule) => {
    setEditingRule(rule);
    setRuleForm({
      name: rule.name,
      category: rule.category,
      keywords: rule.keywords ? rule.keywords.join(', ') : '',
      vendor_patterns: rule.vendor_patterns ? rule.vendor_patterns.join(', ') : '',
      amount_min: rule.amount_min || '',
      amount_max: rule.amount_max || '',
      is_active: rule.is_active
    });
    setShowAddRule(true);
  };

  const resetCategoryForm = () => {
    setCategoryForm({
      name: '',
      type: 'expense',
      description: '',
      color: '#3498db',
      keywords: ''
    });
    setEditingCategory(null);
    setShowAddCategory(false);
  };

  const resetRuleForm = () => {
    setRuleForm({
      name: '',
      category: '',
      keywords: '',
      vendor_patterns: '',
      amount_min: '',
      amount_max: '',
      is_active: true
    });
    setEditingRule(null);
    setShowAddRule(false);
  };

  if (loading) {
    return (
      <div className="category-manager-loading">
        <div className="spinner"></div>
        <p>Loading category management...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="category-manager-error">
        <h3>Error</h3>
        <p>{error}</p>
        <button onClick={loadData} className="retry-btn">Retry</button>
      </div>
    );
  }

  return (
    <div className="category-manager">
      <div className="category-manager-header">
        <h1>Category Management</h1>
        <div className="header-actions">
          <button 
            onClick={() => setShowAddCategory(true)}
            className="add-category-btn"
          >
            Add Category
          </button>
          <button 
            onClick={() => setShowAddRule(true)}
            className="add-rule-btn"
          >
            Add Rule
          </button>
        </div>
      </div>

      {/* Categories Section */}
      <div className="section">
        <h2>Categories ({categories.length})</h2>
        <div className="categories-grid">
          {categories.map(category => (
            <div key={category.id} className="category-card">
              <div className="category-header">
                <div 
                  className="category-color" 
                  style={{ backgroundColor: category.color }}
                ></div>
                <div className="category-info">
                  <h3>{category.name}</h3>
                  <span className="category-type">{category.type}</span>
                </div>
                <div className="category-actions">
                  <button 
                    onClick={() => startEditCategory(category)}
                    className="edit-btn"
                    title="Edit Category"
                  >
                    <FaPenToSquare />
                  </button>
                  <button 
                    onClick={() => handleDeleteCategory(category.id)}
                    className="delete-btn"
                    title="Delete Category"
                  >
                    <FaTrash />
                  </button>
                </div>
              </div>
              
              {category.description && (
                <p className="category-description">{category.description}</p>
              )}
              
              {category.keywords && (
                <div className="category-keywords">
                  <label>Keywords:</label>
                  <div className="keywords-list">
                    {(Array.isArray(category.keywords) 
                      ? category.keywords 
                      : category.keywords.split(',').map(k => k.trim()).filter(k => k)
                    ).map((keyword, idx) => (
                      <span key={`${keyword}-${idx}`} className="keyword-tag">{keyword}</span>
                    ))}
                  </div>
                </div>
              )}
              
              <div className="category-stats">
                <span>Bills: {category.bill_count || 0}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Rules Section */}
      <div className="section">
        <h2>Categorization Rules ({rules.length})</h2>
        {rules.length > 0 ? (
          <div className="rules-list">
            {rules.map(rule => (
              <div key={rule.id} className="rule-card">
                <div className="rule-header">
                  <div className="rule-info">
                    <h4>{rule.name}</h4>
                    <span className="rule-category">
                      {categories.find(c => c.id === rule.category)?.name || 'Unknown Category'}
                    </span>
                  </div>
                  <div className="rule-actions">
                    <div className={`rule-status ${rule.is_active ? 'active' : 'inactive'}`}>
                      {rule.is_active ? '✓ Active' : '✗ Inactive'}
                    </div>
                    <button 
                      onClick={() => startEditRule(rule)}
                      className="edit-btn"
                      title="Edit Rule"
                    >
                      <FaPenToSquare />
                    </button>
                    <button 
                      onClick={() => handleDeleteRule(rule.id)}
                      className="delete-btn"
                      title="Delete Rule"
                    >
                      <FaTrash />
                    </button>
                  </div>
                </div>
                
                <div className="rule-details">
                  {rule.keywords && rule.keywords.length > 0 && (
                    <div className="rule-field">
                      <label>Keywords:</label>
                      <div className="rule-values">
                        {rule.keywords.map(keyword => (
                          <span key={keyword} className="rule-value">{keyword}</span>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {rule.vendor_patterns && rule.vendor_patterns.length > 0 && (
                    <div className="rule-field">
                      <label>Vendor Patterns:</label>
                      <div className="rule-values">
                        {rule.vendor_patterns.map(pattern => (
                          <span key={pattern} className="rule-value">{pattern}</span>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {(rule.amount_min || rule.amount_max) && (
                    <div className="rule-field">
                      <label>Amount Range:</label>
                      <span className="rule-range">
                        ${rule.amount_min || '0'} - ${rule.amount_max || '∞'}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="no-rules">
            <p>No categorization rules found.</p>
            <button 
              onClick={() => setShowAddRule(true)}
              className="add-rule-btn"
            >
              Create your first rule
            </button>
          </div>
        )}
      </div>

      {/* Category Form Modal */}
      {showAddCategory && (
        <div className="modal-overlay" onClick={resetCategoryForm}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{editingCategory ? 'Edit Category' : 'Add New Category'}</h3>
              <button onClick={resetCategoryForm} className="close-btn">✕</button>
            </div>
            
            <form onSubmit={handleCategorySubmit} className="category-form">
              <div className="form-group">
                <label htmlFor="cat-name">Name *</label>
                <input
                  type="text"
                  id="cat-name"
                  value={categoryForm.name}
                  onChange={(e) => setCategoryForm({...categoryForm, name: e.target.value})}
                  required
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="cat-type">Type</label>
                <select
                  id="cat-type"
                  value={categoryForm.type}
                  onChange={(e) => setCategoryForm({...categoryForm, type: e.target.value})}
                >
                  <option value="expense">Expense</option>
                  <option value="income">Income</option>
                </select>
              </div>
              
              <div className="form-group">
                <label htmlFor="cat-color">Color</label>
                <input
                  type="color"
                  id="cat-color"
                  value={categoryForm.color}
                  onChange={(e) => setCategoryForm({...categoryForm, color: e.target.value})}
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="cat-description">Description</label>
                <textarea
                  id="cat-description"
                  value={categoryForm.description}
                  onChange={(e) => setCategoryForm({...categoryForm, description: e.target.value})}
                  rows="3"
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="cat-keywords">Keywords (comma-separated)</label>
                <input
                  type="text"
                  id="cat-keywords"
                  value={categoryForm.keywords}
                  onChange={(e) => setCategoryForm({...categoryForm, keywords: e.target.value})}
                  placeholder="food, restaurant, grocery..."
                />
              </div>
              
              <div className="form-actions">
                <button type="button" onClick={resetCategoryForm} className="cancel-btn">
                  Cancel
                </button>
                <button type="submit" className="save-btn">
                  {editingCategory ? 'Update' : 'Create'} Category
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Rule Form Modal */}
      {showAddRule && (
        <div className="modal-overlay" onClick={resetRuleForm}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{editingRule ? 'Edit Rule' : 'Add New Rule'}</h3>
              <button onClick={resetRuleForm} className="close-btn">✕</button>
            </div>
            
            <form onSubmit={handleRuleSubmit} className="rule-form">
              <div className="form-group">
                <label htmlFor="rule-name">Rule Name *</label>
                <input
                  type="text"
                  id="rule-name"
                  value={ruleForm.name}
                  onChange={(e) => setRuleForm({...ruleForm, name: e.target.value})}
                  required
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="rule-category">Category *</label>
                <select
                  id="rule-category"
                  value={ruleForm.category}
                  onChange={(e) => setRuleForm({...ruleForm, category: e.target.value})}
                  required
                >
                  <option value="">Select a category...</option>
                  {categories.map(category => (
                    <option key={category.id} value={category.id}>
                      {category.name}
                    </option>
                  ))}
                </select>
              </div>
              
              <div className="form-group">
                <label htmlFor="rule-keywords">Keywords (comma-separated)</label>
                <input
                  type="text"
                  id="rule-keywords"
                  value={ruleForm.keywords}
                  onChange={(e) => setRuleForm({...ruleForm, keywords: e.target.value})}
                  placeholder="keywords to match in bill description..."
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="rule-vendors">Vendor Patterns (comma-separated)</label>
                <input
                  type="text"
                  id="rule-vendors"
                  value={ruleForm.vendor_patterns}
                  onChange={(e) => setRuleForm({...ruleForm, vendor_patterns: e.target.value})}
                  placeholder="Walmart, Amazon, McDonald's..."
                />
              </div>
              
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="rule-amount-min">Min Amount</label>
                  <input
                    type="number"
                    id="rule-amount-min"
                    step="0.01"
                    value={ruleForm.amount_min}
                    onChange={(e) => setRuleForm({...ruleForm, amount_min: e.target.value})}
                    placeholder="0.00"
                  />
                </div>
                
                <div className="form-group">
                  <label htmlFor="rule-amount-max">Max Amount</label>
                  <input
                    type="number"
                    id="rule-amount-max"
                    step="0.01"
                    value={ruleForm.amount_max}
                    onChange={(e) => setRuleForm({...ruleForm, amount_max: e.target.value})}
                    placeholder="999.99"
                  />
                </div>
              </div>
              
              <div className="form-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={ruleForm.is_active}
                    onChange={(e) => setRuleForm({...ruleForm, is_active: e.target.checked})}
                  />
                  <span>Active Rule</span>
                </label>
              </div>
              
              <div className="form-actions">
                <button type="button" onClick={resetRuleForm} className="cancel-btn">
                  Cancel
                </button>
                <button type="submit" className="save-btn">
                  {editingRule ? 'Update' : 'Create'} Rule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default CategoryManager;