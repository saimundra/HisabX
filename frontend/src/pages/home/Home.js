import React from 'react';
import { Link } from 'react-router-dom';
import './Home.css';
import { FaReceipt, FaRobot, FaLock } from 'react-icons/fa';

const Navbar = () => {
  const scrollToTop = (e) => {
    e.preventDefault();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const scrollToSection = (e, sectionId) => {
    e.preventDefault();
    const section = document.getElementById(sectionId);
    section.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <nav className="navbar">
      <div className="nav-container">
        <a href="/" className="nav-logo" onClick={scrollToTop}>
          HisabX
        </a>
        <div className="nav-links">
          <a href="/" className="nav-link" onClick={scrollToTop}>Home</a>
          <a href="#features" className="nav-link" onClick={(e) => scrollToSection(e, 'features')}>Features</a>
          <Link to="/pricing" className="nav-link">Pricing</Link>
          <a href="#about" className="nav-link" onClick={(e) => scrollToSection(e, 'about')}>About</a>
          <Link to="/login" className="nav-button">Login / Sign Up</Link>
        </div>
      </div>
    </nav>
  );
};

const Footer = () => (
  <footer className="footer">
    <div className="footer-container">
      <p>&copy; 2025 HisabX. All rights reserved.</p>
      <div className="footer-links">
        <Link to="/privacy" className="footer-link">Privacy Policy</Link>
        <Link to="/terms" className="footer-link">Terms of Service</Link>
        <Link to="/contact" className="footer-link">Contact</Link>
      </div>
    </div>
  </footer>
);

const Home = () => {
  return (
    <div className="home-container">
      <Navbar />
      
      {/* Hero Section */}
      <section className="hero">
        <h1>Transform Your Bills into Audit-Ready Reports Instantly</h1>
        <p>
          Upload your receipts and bills to generate professional, AI-powered audit reports
          in seconds. Simplify your financial documentation process today.
        </p>
      </section>

      {/* Features Section */}
      

      <section id="features" className="features">
        <div className="features-container">
          <h2>Key Features</h2>
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">
                <FaRobot />
              </div>
              <h3>AI-Powered OCR</h3>
              <p>
                Advanced optical character recognition for both printed and handwritten
                bills, ensuring accurate data extraction.
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">
                <FaReceipt />
              </div>
              <h3>Automatic Report Generation</h3>
              <p>
                Transform your receipts into professionally formatted audit reports
                with just one click.
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">
                <FaLock />
              </div>
              <h3>Secure Storage</h3>
              <p>
                Bank-level encryption for your documents with secure e-signature
                ready PDF generation.
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">
                <FaReceipt />
              </div>
              <h3>Smart Categorization</h3>
              <p>
                Automatic expense categorization and tagging using AI to organize your 
                bills by type, date, and vendor.
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">
                <FaRobot />
              </div>
              <h3>Real-time Analytics</h3>
              <p>
                Instant insights and detailed analytics with custom reports, trends, 
                and spending patterns visualization.
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">
                <FaLock />
              </div>
              <h3>Multi-Currency Support</h3>
              <p>
                Handle bills and receipts in multiple currencies with automatic 
                conversion and exchange rate tracking.
              </p>
            </div>
          </div>
        </div>
      </section>

        {/* About Section */}
        <section id="about" className="about">
  <div className="about-container">
    <h2>Revolutionizing Financial Documentation with Intelligence</h2>
    <div className="about-content">
      <p>
        HisabX was born from a simple observation: businesses waste countless hours manually processing receipts and bills for audits. We believed there had to be a better way. Today, we're transforming how organizations handle their financial documentation through the power of artificial intelligence and intuitive design.
      </p>
      <p>
        Our platform combines advanced OCR technology with smart automation to instantly convert any bill—whether handwritten, printed, or photographed—into professional audit reports. We've eliminated the manual data entry, the endless spreadsheets, and the stress of audit preparation. What used to take days now takes seconds.
      </p>
      <p>
        Built with enterprise-grade security and designed for businesses of every size, HisabX doesn't just digitize your documents—it understands them. Our AI learns your spending patterns, categorizes expenses intelligently, and provides insights that help you make better financial decisions while keeping you audit-ready at all times.
      </p>
    </div>
    <div className="key-highlights">
      <h3>Why Businesses Choose HisabX</h3>
      <ul>
        <li>Lightning-fast data extraction from any bill format, saving 95% of processing time.</li>
        <li>Bank-level security with end-to-end encryption and complete audit trails.</li>
        <li>Intelligent categorization and analytics that reveal spending insights automatically.</li>
        <li>Seamless collaboration features for teams, accountants, and auditors.</li>
        <li>Multi-currency support for businesses operating globally.</li>
      </ul>
    </div>
    <div className="about-tagline">
      <p>"From receipt to report in seconds—because your time is worth more than data entry."</p>
    </div>
  </div>
</section>

      <Footer /> 
    </div>
  );
};

export default Home;