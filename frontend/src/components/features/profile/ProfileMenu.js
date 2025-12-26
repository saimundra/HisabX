import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import api from '../../../services/api';
import Icon from '../../common/Icon';
import { FaPenToSquare, FaCircleUser } from 'react-icons/fa6';

const ProfileMenu = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [showProfileModal, setShowProfileModal] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const openProfileModal = () => {
    setShowProfileModal(true);
  };

  // Prevent body scroll when modal is open
  useEffect(() => {
    if (showProfileModal) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [showProfileModal]);

  return (
    <>
    <div style={{ position: 'relative', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.25rem' }}>
      <button 
        onClick={openProfileModal}
        style={{ border: 'none', background: 'none', padding: 0, cursor: 'pointer', display: 'flex', alignItems: 'center' }}
      >
        <FaCircleUser style={{ width: '40px', height: '40px', color: '#6B7280' }} />
      </button>
      <span style={{ fontSize: '0.95rem', color: '#333', fontWeight: '500' }}>
        {user?.username}
      </span>

    {/* Profile Modal */}
    {showProfileModal && (
      <>
        <div 
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.3)',
            zIndex: 9998
          }}
          onClick={() => setShowProfileModal(false)}
        />
        <div 
          style={{
            position: 'absolute',
            top: '60px',
            right: 0,
            backgroundColor: 'white',
            borderRadius: '12px',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.12)',
            width: '340px',
            overflow: 'hidden',
            zIndex: 9999
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <div style={{ padding: '2rem' }}>
            <button 
              onClick={() => setShowProfileModal(false)}
              style={{ position: 'absolute', top: '1rem', right: '1rem', background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.5rem', color: '#9CA3AF', transition: 'color 0.2s' }}
              onMouseEnter={(e) => e.target.style.color = '#374151'}
              onMouseLeave={(e) => e.target.style.color = '#9CA3AF'}
            >
              ×
            </button>
            
            {/* Profile Header */}
            <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
              <div style={{ 
                width: '80px', 
                height: '80px', 
                borderRadius: '50%', 
                background: 'linear-gradient(135deg, #FFD700 0%, #FFA500 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 1rem',
                fontSize: '2rem',
                fontWeight: 'bold',
                color: 'white',
                boxShadow: '0 4px 12px rgba(255, 215, 0, 0.3)'
              }}>
                {user?.username?.charAt(0).toUpperCase() || 'U'}
              </div>
              <h2 style={{ fontSize: '1.5rem', fontWeight: '600', margin: '0 0 0.25rem 0', color: '#111827' }}>
                {user?.username}
              </h2>
              <p style={{ fontSize: '0.875rem', color: '#6B7280', margin: 0 }}>{user?.email}</p>
            </div>

            {/* Info Cards */}
            <div style={{ marginBottom: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div style={{ 
                padding: '1rem', 
                background: '#F9FAFB', 
                borderRadius: '8px',
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem'
              }}>
                <div style={{ color: '#9CA3AF' }}>
                  <Icon name="user" size={20} />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '0.75rem', color: '#6B7280', marginBottom: '0.25rem' }}>Username</div>
                  <div style={{ fontSize: '0.875rem', color: '#111827', fontWeight: '500' }}>{user?.username}</div>
                </div>
              </div>

              <div style={{ 
                padding: '1rem', 
                background: '#F9FAFB', 
                borderRadius: '8px',
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem'
              }}>
                <div style={{ color: '#9CA3AF' }}>
                  <Icon name="email" size={20} />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '0.75rem', color: '#6B7280', marginBottom: '0.25rem' }}>Email</div>
                  <div style={{ fontSize: '0.875rem', color: '#111827', fontWeight: '500' }}>{user?.email}</div>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  <button 
                    onClick={() => {
                      setShowProfileModal(false);
                      navigate('/profile');
                    }} 
                    style={{ 
                      width: '100%',
                      padding: '0.75rem', 
                      fontSize: '0.875rem', 
                      fontWeight: '500',
                      background: '#333', 
                      color: '#fff',
                      border: 'none', 
                      borderRadius: '8px', 
                      cursor: 'pointer', 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'center',
                      gap: '0.5rem',
                      transition: 'all 0.2s'
                    }}
                    onMouseEnter={(e) => e.target.style.background = '#666'}
                    onMouseLeave={(e) => e.target.style.background = '#333'}
                  >
                    <FaPenToSquare /> Edit Company Profile
                  </button>
                  <button 
                    onClick={handleLogout} 
                    style={{ 
                      width: '100%',
                      padding: '0.75rem', 
                      fontSize: '0.875rem', 
                      fontWeight: '500',
                      background: '#F3F4F6', 
                      color: '#374151',
                      border: '1px solid #E5E7EB', 
                      borderRadius: '8px', 
                      cursor: 'pointer',
                      transition: 'all 0.2s'
                    }}
                    onMouseEnter={(e) => { e.target.style.background = '#E5E7EB'; e.target.style.borderColor = '#D1D5DB'; }}
                    onMouseLeave={(e) => { e.target.style.background = '#F3F4F6'; e.target.style.borderColor = '#E5E7EB'; }}
                  >
                  Logout
                </button>
              </div>
            </div>
          </div>
        </>
      )}
      </div>
    </>
  );
};

export default ProfileMenu;