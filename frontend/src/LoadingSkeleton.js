import React from 'react';
import './LoadingSkeleton.css';

function LoadingSkeleton() {
  return (
    <div className="skeleton-container">
      {[1, 2, 3, 4].map((index) => (
        <div key={index} className="skeleton-card" aria-label="Loading parking lot data">
          <div className="skeleton-title"></div>
          <div className="skeleton-circle"></div>
          <div className="skeleton-label"></div>
        </div>
      ))}
    </div>
  );
}

export default LoadingSkeleton;

