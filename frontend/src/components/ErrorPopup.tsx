import React, { useEffect, useState } from 'react';
import '../styles/ErrorPopup.css';

interface ErrorPopupProps {
  message: string | null;
  onClose: () => void;
  duration?: number;
}

const ErrorPopup: React.FC<ErrorPopupProps> = ({ message, onClose, duration = 4000 }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [isFading, setIsFading] = useState(false);

  useEffect(() => {
    if (message) {
      setIsVisible(true);
      setIsFading(false);

      const fadeTimer = setTimeout(() => {
        setIsFading(true);
      }, duration - 500);

      const closeTimer = setTimeout(() => {
        setIsVisible(false);
        onClose();
      }, duration);

      return () => {
        clearTimeout(fadeTimer);
        clearTimeout(closeTimer);
      };
    }
  }, [message, duration, onClose]);

  const handleClick = (): void => {
    setIsFading(true);
    setTimeout(() => {
      setIsVisible(false);
      onClose();
    }, 300);
  };

  if (!isVisible || !message) return null;

  return (
    <div className={`error-popup ${isFading ? 'fade-out' : ''}`} onClick={handleClick}>
      <div className='error-popup-content'>{message}</div>
    </div>
  );
};

export default ErrorPopup;
