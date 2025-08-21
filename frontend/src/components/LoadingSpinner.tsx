// src/components/LoadingSpinner.tsx
import React from 'react';

const LoadingSpinner = () => {
  return (
    <div className="flex justify-center items-center">
      <div className="animate-spin ..."></div>
    </div>
  );
};

export default LoadingSpinner;