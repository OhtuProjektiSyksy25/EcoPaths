// DisclaimerModal.tsx
import React, { useState, useEffect } from 'react';

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

  const handleClose = (): void => {
    setIsAnimating(false);
    setTimeout(() => setIsOpen(false), 300);
  };

  return (
    <>
      <button onClick={() => setIsOpen(true)} className='info-button' aria-label='Open disclaimer'>
        About EcoPaths
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
                <button
                  onClick={handleClose}
                  className='close-button'
                  aria-label='Close disclaimer'
                ></button>
              </div>

              <div className='modal-content'>
                <h1 className='title'>Welcome to EcoPaths!</h1>

                <section>
                  <h2>About</h2>
                  <p>
                    EcoPaths is a student project from the University of Helsinki, created in
                    collaboration with MegaSense Oy. The app helps pedestrians and runners explore
                    routes that balance distance with estimated air quality—anywhere in the world.
                  </p>
                </section>

                <section>
                  <h2>Why It Matters</h2>
                  <p>
                    Air quality can vary significantly from street to street, and small adjustments
                    in route choice can reduce exposure to pollution. EcoPaths highlights these
                    differences, supporting healthier and more informed everyday movement.
                  </p>
                </section>

                <section>
                  <h2>How to Use EcoPaths</h2>
                  <p>
                    Choose the city you want to explore. The highlighted area shows where routing is
                    available.
                  </p>
                  <p>
                    Select your starting point and your destination. You will then see up to three
                    route options:
                  </p>
                  <p>
                    <strong>Blue:</strong> Fastest route (not optimized for air quality)
                    <br />
                    <strong>Green:</strong> Maximum air-quality optimization
                    <br />
                    <strong>Custom:</strong> Adjust the slider to balance speed and air cleanliness
                    based on your preference
                  </p>
                  <p>
                    Each route displays an average AQI value (lower is better). You can also toggle
                    a view that reveals local air quality along each part of the route.
                  </p>
                  <p>
                    Runners can use the loop feature: pick a starting point, set your desired
                    distance, and receive an air-quality-optimized round trip.
                  </p>
                </section>

                <section>
                  <h2>Data & Methods</h2>
                  <p>
                    <strong>Street network data:</strong> Provided by{' '}
                    <a
                      href='https://www.openstreetmap.org'
                      target='_blank'
                      rel='noopener noreferrer'
                    >
                      OpenStreetMap
                    </a>{' '}
                  </p>
                  <p>
                    <strong>Air quality data:</strong> Real-time Air Quality Index (AQI) from{' '}
                    <a
                      href='https://developers.google.com/maps/documentation/air-quality'
                      target='_blank'
                      rel='noopener noreferrer'
                    >
                      Google Air Quality API
                    </a>
                    .
                  </p>
                  <p>
                    <strong>Routing logic:</strong> Walking speed ≈ 1.4 m/s (5 km/h), running speed
                    ≈ 3.0 m/s (10.8 km/h). Routes are computed by combining distance with estimated
                    exposure along each segment.
                  </p>
                </section>

                <section>
                  <h2>Team</h2>
                  <p>
                    Developed by <strong>PathPlanners</strong> as part of the Software Engineering
                    Project course at the University of Helsinki.
                  </p>
                  <p>
                    <strong>GitHub Organization:</strong>{' '}
                    <a
                      href='https://github.com/OhtuProjektiSyksy25'
                      target='_blank'
                      rel='noopener noreferrer'
                    >
                      PathPlanners
                    </a>
                  </p>
                  <p>
                    <strong>Repositories:</strong>
                    <br />
                    <a
                      href='https://github.com/OhtuProjektiSyksy25/EcoPaths'
                      target='_blank'
                      rel='noopener noreferrer'
                    >
                      EcoPaths — Frontend / Backend
                    </a>
                  </p>
                </section>

                <section>
                  <h2>Acknowledgments</h2>
                  <p>
                    This project takes inspiration from the{' '}
                    <a
                      href='https://github.com/DigitalGeographyLab/hope-green-path-ui'
                      target='_blank'
                      rel='noopener noreferrer'
                    >
                      Green Paths
                    </a>{' '}
                    project by the Digital Geography Lab, University of Helsinki.
                  </p>
                </section>

                <div className='warning-box'>
                  <p>
                    EcoPaths is a prototype and may not function reliably at all times. Air quality
                    estimates and route suggestions should be treated as approximations.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </>
  );
};

export default DisclaimerModal;
