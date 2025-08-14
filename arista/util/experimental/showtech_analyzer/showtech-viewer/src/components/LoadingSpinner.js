import React from 'react';

const LoadingSpinner = ({ message = "Loading...", size = "medium" }) => {
  const sizeClass = size === "small" ? "spinner-small" : size === "large" ? "spinner-large" : "spinner-medium";
  
  return (
    <div className="loading-spinner-container">
      <div className={`loading-spinner ${sizeClass}`}></div>
      <p className="loading-message">{message}</p>
    </div>
  );
};

export default LoadingSpinner;
