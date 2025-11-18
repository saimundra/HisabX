import React from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import Icon from './Icon';
import './Profile.css';

const Profile = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

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
            {user.username?.charAt(0).toUpperCase() || 'U'}
          </div>
          <h1>Welcome, {user.username}!</h1>
          <p className="profile-subtitle">Your Account Information</p>
        </div>

        <div className="profile-content">
          <div className="info-card">
            <div className="info-icon" aria-hidden>
              <Icon name="user" size={20} />
            </div>
            <div className="info-details">
              <label>Username</label>
              <p>{user.username}</p>
            </div>
          </div>

          <div className="info-card">
            <div className="info-icon" aria-hidden>
              <Icon name="email" size={20} />
            </div>
            <div className="info-details">
              <label>Email</label>
              <p>{user.email}</p>
            </div>
          </div>

        </div>

        <button onClick={handleLogout} className="logout-button" style={{ background: '#ffd700', color: '#000', border: 'none' }}>
          Logout
        </button>
      </div>
    </div>
  );
};

export default Profile;
