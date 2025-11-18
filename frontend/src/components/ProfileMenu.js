import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import Icon from './Icon';
import { FaPenToSquare, FaCircleUser } from 'react-icons/fa6';

const ProfileMenu = () => {
  const navigate = useNavigate();
  const { user, logout, loadUser } = useAuth();
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({ username: '', email: '', avatar: '' });

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const openProfileModal = () => {
    setForm({ username: user?.username || '', email: user?.email || '', avatar: user?.avatar || '' });
    setIsEditing(false);
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

            {!isEditing ? (
              <>
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
                    onClick={() => setIsEditing(true)} 
                    style={{ 
                      width: '100%',
                      padding: '0.75rem', 
                      fontSize: '0.875rem', 
                      fontWeight: '500',
                      background: '#FFD700', 
                      color: '#000',
                      border: 'none', 
                      borderRadius: '8px', 
                      cursor: 'pointer', 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'center',
                      gap: '0.5rem',
                      transition: 'all 0.2s'
                    }}
                    onMouseEnter={(e) => e.target.style.background = '#FFC700'}
                    onMouseLeave={(e) => e.target.style.background = '#FFD700'}
                  >
                    <FaPenToSquare /> Edit Profile
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
              </>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', color: '#374151', marginBottom: '0.5rem' }}>
                    Username
                  </label>
                  <input
                    type="text"
                    value={form.username}
                    onChange={(e) => setForm({ ...form, username: e.target.value })}
                    placeholder="Username"
                    style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', border: '1px solid #E5E7EB', fontSize: '0.875rem', outline: 'none', transition: 'border-color 0.2s' }}
                    onFocus={(e) => e.target.style.borderColor = '#FFD700'}
                    onBlur={(e) => e.target.style.borderColor = '#E5E7EB'}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', color: '#374151', marginBottom: '0.5rem' }}>
                    Email
                  </label>
                  <input
                    type="email"
                    value={form.email}
                    onChange={(e) => setForm({ ...form, email: e.target.value })}
                    placeholder="Email"
                    style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', border: '1px solid #E5E7EB', fontSize: '0.875rem', outline: 'none', transition: 'border-color 0.2s' }}
                    onFocus={(e) => e.target.style.borderColor = '#FFD700'}
                    onBlur={(e) => e.target.style.borderColor = '#E5E7EB'}
                  />
                </div>
                <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.5rem' }}>
                  <button
                    onClick={async () => {
                      try {
                        setSaving(true);
                        await api.put('/profile/', { username: form.username, email: form.email });
                        await loadUser();
                        setIsEditing(false);
                      } catch (err) {
                        console.error('Profile update failed', err);
                        alert('Failed to update profile');
                      } finally {
                        setSaving(false);
                      }
                    }}
                    disabled={saving}
                    style={{ 
                      flex: 1,
                      padding: '0.75rem', 
                      background: '#FFD700', 
                      color: '#000',
                      border: 'none', 
                      borderRadius: '8px', 
                      cursor: saving ? 'not-allowed' : 'pointer',
                      fontSize: '0.875rem',
                      fontWeight: '500',
                      opacity: saving ? 0.7 : 1,
                      transition: 'all 0.2s'
                    }}
                    onMouseEnter={(e) => !saving && (e.target.style.background = '#FFC700')}
                    onMouseLeave={(e) => e.target.style.background = '#FFD700'}
                  >
                    {saving ? 'Saving...' : 'Save Changes'}
                  </button>
                  <button 
                    onClick={() => setIsEditing(false)} 
                    style={{ 
                      flex: 1,
                      padding: '0.75rem', 
                      background: '#F3F4F6', 
                      color: '#374151',
                      border: '1px solid #E5E7EB', 
                      borderRadius: '8px', 
                      cursor: 'pointer',
                      fontSize: '0.875rem',
                      fontWeight: '500',
                      transition: 'all 0.2s'
                    }}
                    onMouseEnter={(e) => { e.target.style.background = '#E5E7EB'; }}
                    onMouseLeave={(e) => { e.target.style.background = '#F3F4F6'; }}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </>
    )}
    </div>
  </>
  );
};

export default ProfileMenu;