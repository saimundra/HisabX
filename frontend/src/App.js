import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import './styles/App.css';
import Login from './pages/login/Login';
import Register from './pages/register/Register';
import Profile from './components/features/profile/Profile';
import ProtectedRoute from './utils/ProtectedRoute';
import Home from './pages/home/Home';
import Upload from './pages/upload/Upload';
import ProfileMenu from './components/features/profile/ProfileMenu';
import Dashboard from './components/features/dashboard/Dashboard/Dashboard';
import BillManager from './components/features/bills/BillManager';
import BillDetails from './components/features/bills/BillDetails';
import CategoryManager from './components/features/categories/CategoryManager';
import FinancialDashboard from './components/features/dashboard/FinancialDashboard/FinancialDashboard';

function AppRoutes() {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <>
      {isAuthenticated && (
        <nav className="navbar">
          <div className="nav-container">
            <Link to="/dashboard" className="nav-logo">HisabX</Link>
            <div className="nav-links">
              <Link to="/dashboard">Dashboard</Link>
              <Link to="/bills">Bills</Link>
              <Link to="/categories">Categories</Link>
              <Link to="/financial">Finance & Reports</Link>
              <Link to="/upload">Upload</Link>
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <ProfileMenu />
              </div>
            </div>
          </div>
        </nav>
      )}
      
  {/* add top padding equal to navbar height so content aligns and isn't hidden under fixed navbar */}
  <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8" style={{ paddingTop: isAuthenticated ? '80px' : undefined }}>
        <Routes>
          <Route
            path="/login"
            element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <Login />}
          />
          <Route
            path="/register"
            element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <Register />}
          />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/bills"
            element={
              <ProtectedRoute>
                <BillManager />
              </ProtectedRoute>
            }
          />
          <Route
            path="/bills/:id"
            element={
              <ProtectedRoute>
                <BillDetails />
              </ProtectedRoute>
            }
          />
          <Route
            path="/categories"
            element={
              <ProtectedRoute>
                <CategoryManager />
              </ProtectedRoute>
            }
          />
          <Route
            path="/financial"
            element={
              <ProtectedRoute>
                <FinancialDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/upload"
            element={
              <ProtectedRoute>
                <Upload />
              </ProtectedRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <Profile />
              </ProtectedRoute>
            }
          />
          <Route 
            path="/" 
            element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <Home />} 
          />
        </Routes>
      </main>
      
      <ToastContainer
        position="top-right"
        autoClose={5000}
        hideProgressBar={false}
        newestOnTop
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme="light"
      />
    </>
  );
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </Router>
  );
}

export default App;
