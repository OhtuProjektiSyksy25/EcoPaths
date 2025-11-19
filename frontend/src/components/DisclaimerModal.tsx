// DisclaimerModal.tsx (Prettier‑compliant)
import React, { useState, useEffect } from 'react';
import { Info, X } from 'lucide-react';
import '../styles/DisclaimerModal.css';

const DisclaimerModal: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setIsAnimating(true);
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  const handleClose = () => {
    setIsAnimating(false);
    setTimeout(() => setIsOpen(false), 300);
  };

  return (
    <>
      <button onClick={() => setIsOpen(true)} className='info-button' aria-label='Open disclaimer'>
        <Info size={20} />
      </button>

      {isOpen && (
        <>
          <div
            className={`modal-overlay ${isAnimating ? 'overlay-visible' : ''}`}
            onClick={handleClose}
          />

          <div className='modal-wrapper'>
            <div className={`modal-container ${isAnimating ? 'modal-open' : 'modal-closed'}`}>
              <div className='modal-header'>
                <div className='lang-buttons'>
                  <button className='underline'>EN</button>
                </div>
                <button
                  onClick={handleClose}
                  className='close-button'
                  aria-label='Close disclaimer'
                >
                  <X size={20} />
                </button>
              </div>

              <div className='modal-content'>
                <h1 className='title'>Welcome to EcoPaths!</h1>

                <div className='warning-box'>
                  <Info className='warning-icon' size={20} />
                  <p>The app is a prototype and may not be functional at all times.</p>
                </div>

                <section>
                  <h2>Problem</h2>
                  <p>
                    While fresh air and greenery bring benefits, pollution and noise may cause
                    health issues. A healthier route may only be slightly longer than the shortest.
                  </p>
                </section>

                <section>
                  <h2>Solution</h2>
                  <p>
                    This tool guides you to pleasant walking routes in big cities. Compare shortest,
                    cleanest, or balanced routes and find what suits you.
                  </p>
                </section>

                <section>
                  <h2>Data & methods</h2>
                  <p>Street network data from OpenStreetMap.</p>
                  <p>Air quality index from Google Air Quality API.</p>
                  <p></p>
                </section>

                <section>
                  <h2>Team</h2>
                  <p>Developed by PathPlanners at the University of Helsinki</p>
                </section>

                <section>
                  <h2>Links</h2>
                  <a
                    href='https://github.com/OhtuProjektiSyksy25/EcoPaths'
                    target='_blank'
                    rel='noopener noreferrer'
                  >
                    GitHub Repository
                  </a>
                </section>
              </div>
            </div>
          </div>
        </>
      )}
    </>
  );
};

export default DisclaimerModal;
