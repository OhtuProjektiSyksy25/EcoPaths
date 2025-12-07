import React, { useEffect, useState } from 'react';
import '../styles/ErrorPopup.css';

interface ErrorPopupProps {
  message: string | null;
  onClose: () => void;
  type?: 'error' | 'warning' | 'info' | 'success';
}

const ErrorPopup: React.FC<ErrorPopupProps> = ({ message, onClose, type = 'error' }) => {
  const [fadeOut, setFadeOut] = useState(false);

  useEffect(() => {
    if (!message) return;

    const timer = setTimeout(() => {
      setFadeOut(true);
      setTimeout(() => {
        onClose();
        setFadeOut(false);
      }, 500);
    }, 5000);

    return () => clearTimeout(timer);
  }, [message, onClose]);

  if (!message) return null;

  return (
    <div className={`error-popup ${fadeOut ? 'fade-out' : ''}`} onClick={onClose}>
      <div className={`error-popup-content ${type}`}>{message}</div>
    </div>
  );
};

export default ErrorPopup;
