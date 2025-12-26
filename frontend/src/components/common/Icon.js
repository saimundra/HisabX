import React from 'react';

const Icon = ({ name, className, size = 20 }) => {
  const commonProps = { width: size, height: size, viewBox: '0 0 24 24', fill: 'none', xmlns: 'http://www.w3.org/2000/svg', className };

  switch (name) {
    case 'user':
      return (
        <svg {...commonProps}>
          <path d="M12 12c2.7614 0 5-2.2386 5-5s-2.2386-5-5-5-5 2.2386-5 5 2.2386 5 5 5z" fill="#333"/>
          <path d="M4 20c0-3.3137 2.6863-6 6-6h4c3.3137 0 6 2.6863 6 6v1H4v-1z" fill="#333"/>
        </svg>
      );
    case 'email':
      return (
        <svg {...commonProps}>
          <path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2z" stroke="#333" strokeWidth="1.5" fill="none"/>
          <path d="M20 6l-8 5-8-5" stroke="#333" strokeWidth="1.5" fill="none"/>
        </svg>
      );
    case 'edit':
      return (
        <svg {...commonProps}>
          <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04a1 1 0 000-1.41l-2.34-2.34a1 1 0 00-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z" fill="#333"/>
        </svg>
      );
    case 'address-card':
      return (
        <svg {...commonProps}>
          <path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2z" stroke="#333" strokeWidth="1.5" fill="none"/>
          <circle cx="8" cy="10" r="2.5" stroke="#333" strokeWidth="1.5" fill="none"/>
          <path d="M5 15c0-1.66 1.34-3 3-3s3 1.34 3 3" stroke="#333" strokeWidth="1.5" fill="none"/>
          <line x1="13" y1="8" x2="18" y2="8" stroke="#333" strokeWidth="1.5"/>
          <line x1="13" y1="12" x2="18" y2="12" stroke="#333" strokeWidth="1.5"/>
          <line x1="13" y1="16" x2="16" y2="16" stroke="#333" strokeWidth="1.5"/>
        </svg>
      );
    case 'buildings':
      return (
        <svg {...commonProps}>
          {/* Left building */}
          <path d="M3 21V7h6v14" stroke="#333" strokeWidth="1.5" fill="none"/>
          <line x1="5" y1="9" x2="7" y2="9" stroke="#333" strokeWidth="1"/>
          <line x1="5" y1="12" x2="7" y2="12" stroke="#333" strokeWidth="1"/>
          <line x1="5" y1="15" x2="7" y2="15" stroke="#333" strokeWidth="1"/>
          <line x1="5" y1="18" x2="7" y2="18" stroke="#333" strokeWidth="1"/>
          {/* Right building */}
          <path d="M9 21V4h9v17" stroke="#333" strokeWidth="1.5" fill="none"/>
          <line x1="11" y1="7" x2="13" y2="7" stroke="#333" strokeWidth="1"/>
          <line x1="15" y1="7" x2="16" y2="7" stroke="#333" strokeWidth="1"/>
          <line x1="11" y1="10" x2="13" y2="10" stroke="#333" strokeWidth="1"/>
          <line x1="15" y1="10" x2="16" y2="10" stroke="#333" strokeWidth="1"/>
          <line x1="11" y1="13" x2="13" y2="13" stroke="#333" strokeWidth="1"/>
          <line x1="15" y1="13" x2="16" y2="13" stroke="#333" strokeWidth="1"/>
          <line x1="11" y1="16" x2="13" y2="16" stroke="#333" strokeWidth="1"/>
          <line x1="15" y1="16" x2="16" y2="16" stroke="#333" strokeWidth="1"/>
          {/* Ground line */}
          <line x1="2" y1="21" x2="19" y2="21" stroke="#333" strokeWidth="1.5"/>
        </svg>
      );
    case 'id-card':
      return (
        <svg {...commonProps}>
          <rect x="3" y="7" width="18" height="12" rx="2" stroke="#333" strokeWidth="1.5" fill="none"/>
          <line x1="6" y1="11" x2="10" y2="11" stroke="#333" strokeWidth="1.5"/>
          <line x1="6" y1="14" x2="9" y2="14" stroke="#333" strokeWidth="1.5"/>
          <circle cx="15.5" cy="12.5" r="2" stroke="#333" strokeWidth="1.5" fill="none"/>
        </svg>
      );
    case 'briefcase':
      return (
        <svg {...commonProps}>
          <rect x="3" y="8" width="18" height="11" rx="2" stroke="#333" strokeWidth="1.5" fill="none"/>
          <path d="M8 8V6c0-1.1.9-2 2-2h4c1.1 0 2 .9 2 2v2" stroke="#333" strokeWidth="1.5" fill="none"/>
          <line x1="3" y1="13" x2="21" y2="13" stroke="#333" strokeWidth="1.5"/>
          <path d="M10 13v2h4v-2" stroke="#333" strokeWidth="1.5" fill="none"/>
        </svg>
      );
    case 'phone':
      return (
        <svg {...commonProps}>
          <path d="M6.62 10.79c1.44 2.83 3.76 5.14 6.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24 1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17 0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02l-2.2 2.2z" stroke="#333" strokeWidth="1.5" fill="none"/>
        </svg>
      );
    case 'map-pin':
      return (
        <svg {...commonProps}>
          <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z" stroke="#333" strokeWidth="1.5" fill="none"/>
          <circle cx="12" cy="9" r="2.5" stroke="#333" strokeWidth="1.5" fill="none"/>
        </svg>
      );
    default:
      return null;
  }
};

export default Icon;
