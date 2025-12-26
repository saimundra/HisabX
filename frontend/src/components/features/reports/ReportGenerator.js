import React, { useState, useEffect } from 'react';
import { FaTrash } from 'react-icons/fa';
import { format } from 'date-fns';
import api from '../../../services/api';
import './ReportGenerator.css';

const ReportGenerator = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [categories, setCategories] = useState([]);
  const [reports, setReports] = useState([]);
  const [generating, setGenerating] = useState(false);

  const [reportForm, setReportForm] = useState({
    title: '',
    description: '',
    start_date: format(new Date(new Date().getFullYear(), new Date().getMonth(), 1), 'yyyy-MM-dd'),
    end_date: format(new Date(), 'yyyy-MM-dd'),
    categories: [],
    vendors: '',
    min_amount: '',
    max_amount: '',
    include_business: true,
    include_personal: true,
    export_format: 'excel',
    group_by: 'category'
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError('');
      
      const [categoriesResponse, reportsResponse] = await Promise.all([
        api.get('/bills/categories_summary/'),
        api.get('/reports/audit_reports/')
      ]);
      
      setCategories(categoriesResponse.data);
      setReports(reportsResponse.data || []);
    } catch (err) {
      console.error('Error loading data:', err);
      setError('Failed to load report data');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateReport = async (e) => {
    e.preventDefault();
    try {
      setGenerating(true);
      setError('');

      const formData = {
        ...reportForm,
        categories: reportForm.categories.length > 0 ? reportForm.categories : null,
        vendors: reportForm.vendors ? reportForm.vendors.split(',').map(v => v.trim()).filter(v => v) : null,
        min_amount: reportForm.min_amount ? parseFloat(reportForm.min_amount) : null,
        max_amount: reportForm.max_amount ? parseFloat(reportForm.max_amount) : null
      };

      const response = await api.post('/reports/generate/', formData);
      
      if (reportForm.export_format === 'excel') {
        // Handle Excel download
        const blob = new Blob([response.data], { 
          type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
        });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `expense_report_${format(new Date(), 'yyyy-MM-dd')}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
      }

      await loadData(); // Refresh reports list
      alert('Report generated successfully!');
      
      // Reset form
      setReportForm({
        ...reportForm,
        title: '',
        description: ''
      });
      
    } catch (err) {
      console.error('Error generating report:', err);
      setError('Failed to generate report');
      alert('Failed to generate report');
    } finally {
      setGenerating(false);
    }
  };

  const handleQuickReport = async (type) => {
    try {
      setGenerating(true);
      
      let formData = {
        title: '',
        export_format: 'excel',
        include_business: true,
        include_personal: true
      };

      const today = new Date();
      
      switch (type) {
        case 'monthly':
          formData = {
            ...formData,
            title: `Monthly Report - ${format(today, 'MMMM yyyy')}`,
            start_date: format(new Date(today.getFullYear(), today.getMonth(), 1), 'yyyy-MM-dd'),
            end_date: format(today, 'yyyy-MM-dd'),
            group_by: 'category'
          };
          break;
          
        case 'quarterly':
          const quarter = Math.floor(today.getMonth() / 3);
          const quarterStart = new Date(today.getFullYear(), quarter * 3, 1);
          formData = {
            ...formData,
            title: `Quarterly Report - Q${quarter + 1} ${today.getFullYear()}`,
            start_date: format(quarterStart, 'yyyy-MM-dd'),
            end_date: format(today, 'yyyy-MM-dd'),
            group_by: 'category'
          };
          break;
          
        case 'yearly':
          formData = {
            ...formData,
            title: `Annual Report - ${today.getFullYear()}`,
            start_date: format(new Date(today.getFullYear(), 0, 1), 'yyyy-MM-dd'),
            end_date: format(today, 'yyyy-MM-dd'),
            group_by: 'month'
          };
          break;
          
        case 'business':
          formData = {
            ...formData,
            title: `Business Expenses - ${format(today, 'MMMM yyyy')}`,
            start_date: format(new Date(today.getFullYear(), today.getMonth(), 1), 'yyyy-MM-dd'),
            end_date: format(today, 'yyyy-MM-dd'),
            include_business: true,
            include_personal: false,
            group_by: 'category'
          };
          break;
      }

      const response = await api.post('/reports/generate/', formData);
      
      // Handle Excel download
      const blob = new Blob([response.data], { 
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `${formData.title.toLowerCase().replace(/\s+/g, '_')}.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      
      await loadData();
      alert('Quick report generated successfully!');
      
    } catch (err) {
      console.error('Error generating quick report:', err);
      alert('Failed to generate quick report');
    } finally {
      setGenerating(false);
    }
  };

  const handleDeleteReport = async (reportId) => {
    if (window.confirm('Are you sure you want to delete this report?')) {
      try {
        await api.delete(`/reports/audit_reports/${reportId}/`);
        await loadData();
        alert('Report deleted successfully');
      } catch (err) {
        console.error('Error deleting report:', err);
        alert('Failed to delete report');
      }
    }
  };

  const handleDownloadReport = async (reportId) => {
    try {
      const response = await api.get(`/reports/audit_reports/${reportId}/download/`, {
        responseType: 'blob'
      });
      
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `report_${reportId}.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Error downloading report:', err);
      alert('Failed to download report');
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const handleCategoryChange = (categoryId) => {
    const currentCategories = reportForm.categories;
    if (currentCategories.includes(categoryId)) {
      setReportForm({
        ...reportForm,
        categories: currentCategories.filter(id => id !== categoryId)
      });
    } else {
      setReportForm({
        ...reportForm,
        categories: [...currentCategories, categoryId]
      });
    }
  };

  if (loading) {
    return (
      <div className="report-generator-loading">
        <div className="spinner"></div>
        <p>Loading report generator...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="report-generator-error">
        <h3>Error</h3>
        <p>{error}</p>
        <button onClick={loadData} className="retry-btn">Retry</button>
      </div>
    );
  }

  return (
    <div className="report-generator">
      <div className="report-generator-header">
        <h1>Report Generator</h1>
        <p>Generate custom reports and export your expense data</p>
      </div>

      {/* Quick Actions */}
      <div className="quick-reports-section">
        <h2>Quick Reports</h2>
        <div className="quick-reports-grid">
          <button 
            onClick={() => handleQuickReport('monthly')}
            className="quick-report-btn"
            disabled={generating}
          >
            <div className="icon">📊</div>
            <div className="content">
              <h3>Monthly Report</h3>
              <p>Current month summary</p>
            </div>
          </button>
          
          <button 
            onClick={() => handleQuickReport('quarterly')}
            className="quick-report-btn"
            disabled={generating}
          >
            <div className="icon">📈</div>
            <div className="content">
              <h3>Quarterly Report</h3>
              <p>Current quarter breakdown</p>
            </div>
          </button>
          
          <button 
            onClick={() => handleQuickReport('yearly')}
            className="quick-report-btn"
            disabled={generating}
          >
            <div className="icon">📋</div>
            <div className="content">
              <h3>Annual Report</h3>
              <p>Full year analysis</p>
            </div>
          </button>
          
          <button 
            onClick={() => handleQuickReport('business')}
            className="quick-report-btn"
            disabled={generating}
          >
            <div className="icon">💼</div>
            <div className="content">
              <h3>Business Expenses</h3>
              <p>Tax-deductible items</p>
            </div>
          </button>
        </div>
      </div>

      {/* Custom Report Form */}
      <div className="custom-report-section">
        <h2>Custom Report</h2>
        <form onSubmit={handleGenerateReport} className="report-form">
          <div className="form-section">
            <h3>Basic Information</h3>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="title">Report Title *</label>
                <input
                  type="text"
                  id="title"
                  value={reportForm.title}
                  onChange={(e) => setReportForm({...reportForm, title: e.target.value})}
                  required
                  placeholder="Enter report title..."
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="export-format">Export Format</label>
                <select
                  id="export-format"
                  value={reportForm.export_format}
                  onChange={(e) => setReportForm({...reportForm, export_format: e.target.value})}
                >
                  <option value="excel">Excel (.xlsx)</option>
                  <option value="pdf">PDF</option>
                </select>
              </div>
            </div>
            
            <div className="form-group">
              <label htmlFor="description">Description</label>
              <textarea
                id="description"
                value={reportForm.description}
                onChange={(e) => setReportForm({...reportForm, description: e.target.value})}
                rows="3"
                placeholder="Optional description for this report..."
              />
            </div>
          </div>

          <div className="form-section">
            <h3>Date Range</h3>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="start-date">Start Date *</label>
                <input
                  type="date"
                  id="start-date"
                  value={reportForm.start_date}
                  onChange={(e) => setReportForm({...reportForm, start_date: e.target.value})}
                  required
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="end-date">End Date *</label>
                <input
                  type="date"
                  id="end-date"
                  value={reportForm.end_date}
                  onChange={(e) => setReportForm({...reportForm, end_date: e.target.value})}
                  required
                />
              </div>
            </div>
          </div>

          <div className="form-section">
            <h3>Filters</h3>
            
            <div className="form-group">
              <label>Categories (select multiple)</label>
              <div className="categories-filter">
                {categories.map(category => (
                  <label key={category.id} className="category-checkbox">
                    <input
                      type="checkbox"
                      checked={reportForm.categories.includes(category.id)}
                      onChange={() => handleCategoryChange(category.id)}
                    />
                    <span 
                      className="category-name"
                      style={{ color: category.color }}
                    >
                      {category.name}
                    </span>
                  </label>
                ))}
              </div>
              <small>Leave empty to include all categories</small>
            </div>
            
            <div className="form-group">
              <label htmlFor="vendors">Vendors (comma-separated)</label>
              <input
                type="text"
                id="vendors"
                value={reportForm.vendors}
                onChange={(e) => setReportForm({...reportForm, vendors: e.target.value})}
                placeholder="Walmart, Amazon, Starbucks..."
              />
              <small>Leave empty to include all vendors</small>
            </div>
            
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="min-amount">Minimum Amount</label>
                <input
                  type="number"
                  id="min-amount"
                  step="0.01"
                  value={reportForm.min_amount}
                  onChange={(e) => setReportForm({...reportForm, min_amount: e.target.value})}
                  placeholder="0.00"
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="max-amount">Maximum Amount</label>
                <input
                  type="number"
                  id="max-amount"
                  step="0.01"
                  value={reportForm.max_amount}
                  onChange={(e) => setReportForm({...reportForm, max_amount: e.target.value})}
                  placeholder="999.99"
                />
              </div>
            </div>
            
            <div className="form-row">
              <div className="form-group">
                <label className="checkbox-group">
                  <input
                    type="checkbox"
                    checked={reportForm.include_business}
                    onChange={(e) => setReportForm({...reportForm, include_business: e.target.checked})}
                  />
                  <span>Include Business Expenses</span>
                </label>
              </div>
              
              <div className="form-group">
                <label className="checkbox-group">
                  <input
                    type="checkbox"
                    checked={reportForm.include_personal}
                    onChange={(e) => setReportForm({...reportForm, include_personal: e.target.checked})}
                  />
                  <span>Include Personal Expenses</span>
                </label>
              </div>
            </div>
          </div>

          <div className="form-section">
            <h3>Grouping & Organization</h3>
            <div className="form-group">
              <label htmlFor="group-by">Group By</label>
              <select
                id="group-by"
                value={reportForm.group_by}
                onChange={(e) => setReportForm({...reportForm, group_by: e.target.value})}
              >
                <option value="category">Category</option>
                <option value="vendor">Vendor</option>
                <option value="month">Month</option>
                <option value="date">Date</option>
              </select>
            </div>
          </div>

          <div className="form-actions">
            <button 
              type="submit" 
              className="generate-btn"
              disabled={generating}
            >
              {generating ? (
                <>
                  <div className="button-spinner"></div>
                  Generating...
                </>
              ) : (
                <>
                  📊 Generate Report
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Report History */}
      <div className="report-history-section">
        <h2>Report History</h2>
        {reports.length > 0 ? (
          <div className="reports-list">
            {reports.map(report => (
              <div key={report.id} className="report-item">
                <div className="report-info">
                  <h4>{report.title}</h4>
                  {report.description && <p>{report.description}</p>}
                  <div className="report-meta">
                    <span>Generated: {formatDate(report.generated_date)}</span>
                    <span>Period: {formatDate(report.start_date)} - {formatDate(report.end_date)}</span>
                    <span>Format: {report.export_format.toUpperCase()}</span>
                  </div>
                </div>
                <div className="report-actions">
                  <button 
                    onClick={() => handleDownloadReport(report.id)}
                    className="download-btn"
                    title="Download Report"
                  >
                    💾
                  </button>
                  <button 
                    onClick={() => handleDeleteReport(report.id)}
                    className="delete-btn"
                    title="Delete Report"
                  >
                    <FaTrash />
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="no-reports">
            <p>No reports generated yet.</p>
            <p>Create your first report using the options above.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReportGenerator;