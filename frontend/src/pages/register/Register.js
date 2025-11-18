import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { FaArrowLeft } from 'react-icons/fa';
import './Register.css';

const Register = () => {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirm_password: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (formData.password !== formData.confirm_password) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);

    const result = await register(formData);

    if (result.success) {
      navigate('/login');
    } else {
      if (typeof result.error === 'object') {
        const errorMessages = Object.values(result.error).flat();
        setError(errorMessages.join(', '));
      } else {
        setError(result.error);
      }
    }

    setLoading(false);
  };

  return (
    <div className="auth-container">
      <Link to="/" className="back-button">
        <FaArrowLeft /> Back to Home
      </Link>
      <div className="auth-card">
        <div className="auth-header">
          <h1>Create Account</h1>
          <p>Sign up to get started</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          {error && <div className="error-message">{error}</div>}

          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleChange}
              required
              placeholder="Choose a username"
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              placeholder="Enter your email"
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              placeholder="Create a password"
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label htmlFor="confirm_password">Confirm Password</label>
            <input
              type="password"
              id="confirm_password"
              name="confirm_password"
              value={formData.confirm_password}
              onChange={handleChange}
              required
              placeholder="Confirm your password"
              className="form-input"
            />
          </div>

          <button
            type="submit"
            className="auth-button"
            disabled={loading}
          >
            {loading ? 'Creating account...' : 'Sign Up'}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            Already have an account?{' '}
            <Link to="/login" className="auth-link">
              Sign in here
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Register;
