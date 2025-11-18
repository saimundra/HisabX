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
          <path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2z" fill="#333"/>
          <path d="M20 6l-8 5-8-5" fill="#fff"/>
        </svg>
      );
    case 'edit':
      return (
        <svg {...commonProps}>
          <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04a1 1 0 000-1.41l-2.34-2.34a1 1 0 00-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z" fill="#333"/>
        </svg>
      );
    default:
      return null;
  }
};

export default Icon;
