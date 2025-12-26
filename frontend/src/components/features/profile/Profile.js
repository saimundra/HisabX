import React, { useState, useEffect } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import api from '../../../services/api';
import Icon from '../../common/Icon';
import './Profile.css';

const Profile = () => {
  const { user, logout, loadUser } = useAuth();
  const navigate = useNavigate();
  const [editing, setEditing] = useState(false);
  const [formData, setFormData] = useState({
    company_name: '',
    pan_vat_number: '',
    business_type: '',
    phone_number: '',
    address: '',
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  useEffect(() => {
    if (user) {
      setFormData({
        company_name: user.company_name || '',
        pan_vat_number: user.pan_vat_number || '',
        business_type: user.business_type || '',
        phone_number: user.phone_number || '',
        address: user.address || '',
      });
    }
  }, [user]);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ type: '', text: '' });

    try {
      const response = await api.put('/profile/', formData);
      
      // Reload user data from server
      await loadUser();
      setMessage({ type: 'success', text: 'Profile updated successfully!' });
      setEditing(false);
    } catch (error) {
      console.error('Error updating profile:', error);
      
      // Show more specific error message
      const errorMsg = error.response?.data?.message 
        || error.response?.data?.error
        || Object.values(error.response?.data || {}).flat().join(', ')
        || 'Failed to update profile. Please try again.';
      
      setMessage({ type: 'error', text: errorMsg });
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (!user) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="profile-container">
      <div className="profile-card">
        <div className="profile-header">
          <div className="profile-avatar">
            {user.company_name?.charAt(0).toUpperCase() || user.username?.charAt(0).toUpperCase() || 'U'}
          </div>
          <h1>{user.company_name || user.username}</h1>
          <p className="profile-subtitle">Company Profile & Account Information</p>
        </div>

        {message.text && (
          <div className={`message ${message.type}`}>
            {message.text}
          </div>
        )}

        <div className="profile-content">
          {editing ? (
            <form onSubmit={handleSubmit} className="profile-edit-form">
              <div className="info-card">
                <label>Company/Business Name</label>
                <input
                  type="text"
                  name="company_name"
                  value={formData.company_name}
                  onChange={handleChange}
                  className="form-input"
                  placeholder="Enter company name"
                />
              </div>

              <div className="info-card">
                <label>PAN/VAT Number</label>
                <input
                  type="text"
                  name="pan_vat_number"
                  value={formData.pan_vat_number}
                  onChange={handleChange}
                  className="form-input"
                  placeholder="Enter PAN/VAT number"
                />
              </div>

              <div className="info-card">
                <label>Business Type</label>
                <select
                  name="business_type"
                  value={formData.business_type}
                  onChange={handleChange}
                  className="form-input"
                >
                  <option value="">Select business type</option>
                  <option value="Retail">Retail</option>
                  <option value="Wholesale">Wholesale</option>
                  <option value="Service">Service</option>
                  <option value="Manufacturing">Manufacturing</option>
                  <option value="Restaurant/Hotel">Restaurant/Hotel</option>
                  <option value="Trading">Trading</option>
                  <option value="Professional Services">Professional Services</option>
                  <option value="Other">Other</option>
                </select>
              </div>

              <div className="info-card">
                <label>Phone Number</label>
                <input
                  type="tel"
                  name="phone_number"
                  value={formData.phone_number}
                  onChange={handleChange}
                  className="form-input"
                  placeholder="Enter phone number"
                />
              </div>

              <div className="info-card">
                <label>Business Address</label>
                <input
                  type="text"
                  name="address"
                  value={formData.address}
                  onChange={handleChange}
                  className="form-input"
                  placeholder="Enter business address"
                />
              </div>

              <div className="button-group">
                <button type="submit" className="save-button" disabled={loading}>
                  {loading ? 'Saving...' : 'Save Changes'}
                </button>
                <button 
                  type="button" 
                  onClick={() => setEditing(false)} 
                  className="cancel-button"
                  disabled={loading}
                >
                  Cancel
                </button>
              </div>
            </form>
          ) : (
            <>
              <div className="info-section">
                <h3>Account Information</h3>
                <div className="info-card">
                  <div className="info-icon" aria-hidden>
                    <Icon name="address-card" size={28} />
                  </div>
                  <div className="info-details">
                    <label>Username</label>
                    <p>{user.username}</p>
                  </div>
                </div>

                <div className="info-card">
                  <div className="info-icon" aria-hidden>
                    <Icon name="email" size={28} />
                  </div>
                  <div className="info-details">
                    <label>Email</label>
                    <p>{user.email}</p>
                  </div>
                </div>
              </div>

              <div className="info-section">
                <h3>Company Information</h3>
                <div className="info-card">
                  <div className="info-icon" aria-hidden>
                    <Icon name="buildings" size={28} />
                  </div>
                  <div className="info-details">
                    <label>Company Name</label>
                    <p>{user.company_name || 'Not set'}</p>
                  </div>
                </div>

                <div className="info-card">
                  <div className="info-icon" aria-hidden>
                    <Icon name="id-card" size={28} />
                  </div>
                  <div className="info-details">
                    <label>PAN/VAT Number</label>
                    <p>{user.pan_vat_number || 'Not set'}</p>
                  </div>
                </div>

                <div className="info-card">
                  <div className="info-icon" aria-hidden>
                    <Icon name="briefcase" size={28} />
                  </div>
                  <div className="info-details">
                    <label>Business Type</label>
                    <p>{user.business_type || 'Not set'}</p>
                  </div>
                </div>

                <div className="info-card">
                  <div className="info-icon" aria-hidden>
                    <Icon name="phone" size={28} />
                  </div>
                  <div className="info-details">
                    <label>Phone Number</label>
                    <p>{user.phone_number || 'Not set'}</p>
                  </div>
                </div>

                <div className="info-card">
                  <div className="info-icon" aria-hidden>
                    <Icon name="map-pin" size={28} />
                  </div>
                  <div className="info-details">
                    <label>Address</label>
                    <p>{user.address || 'Not set'}</p>
                  </div>
                </div>
              </div>

              <button onClick={() => setEditing(true)} className="edit-button">
                Edit Company Profile
              </button>
            </>
          )}
        </div>

        <button onClick={handleLogout} className="logout-button">
          Logout
        </button>
      </div>
    </div>
  );
};

export default Profile;
