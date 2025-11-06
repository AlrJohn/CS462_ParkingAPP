import React, { useState } from 'react';
import './ErrorBanner.css';

function ErrorBanner({ message, onClose }) {
  const [isVisible, setIsVisible] = useState(true);

  const handleClose = () => {
    setIsVisible(false);
    if (onClose) {
      onClose();
    }
  };

  if (!isVisible) return null;

  return (
    <div 
      className="error-banner" 
      role="alert"
      aria-live="assertive"
      aria-atomic="true"
    >
      <div className="error-banner-content">
        <span className="error-icon" aria-hidden="true">⚠️</span>
        <span className="error-message">{message}</span>
      </div>
      <button
        className="error-close-button"
        onClick={handleClose}
        aria-label="Close error message"
      >
        ×
      </button>
    </div>
  );
}

export default ErrorBanner;

