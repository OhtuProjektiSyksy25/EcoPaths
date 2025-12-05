import React, { useState, useEffect } from 'react';
import { Info, X, AlertTriangle } from 'lucide-react';
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
        <Info size={24} data-testid="info-icon" />
      </button>

      {isOpen && (
        <>
          <div
            className={`modal-overlay ${isAnimating ? 'overlay-visible' : ''}`}
            onClick={handleClose}
          />

          <div className='modal-wrapper'>
            <div className={`modal-container ${isAnimating ? 'modal-open' : 'modal-closed'}`}>
              {/* ---------------- HEADER WITH TITLE INSIDE GREEN BAR ---------------- */}
              <div className='modal-header'>
                <div className='modal-title'>
                  <h4 className='title'>Welcome to EcoPaths!</h4>
                </div>
                <button
                  onClick={handleClose}
                  className='close-button'
                  aria-label='Close disclaimer'
                >
                  <X size={20} data-testid="close-icon" />
                </button>
              </div>

              <div className='modal-content'>
                {/* ---------------- ABOUT ---------------- */}
                <section>
                  <h2>About</h2>
                  <p>
                    EcoPaths is a student project from the University of Helsinki, created in
                    collaboration with MegaSense Oy. The app helps pedestrians and runners explore
                    routes that balance distance with estimated air quality, anywhere in the world.
                  </p>
                </section>

                {/* ---------------- WHY IT MATTERS ---------------- */}
                <section>
                  <h2>Why It Matters</h2>
                  <p>
                    Air quality can vary significantly from street to street, and small adjustments
                    in route choice can reduce exposure to pollution. EcoPaths highlights these
                    differences, supporting healthier and more informed everyday movement.
                  </p>

                  {/* placeholder requested by team */}
                  <p>
                    <em>
                      More detailed exposure data is available when searching and clicking on route
                      cards
                    </em>
                  </p>
                </section>
                {/* ---------------- HOW TO USE (with bullet points) ---------------- */}
                <section>
                  <h2>How to Use EcoPaths</h2>

                  <ul className='bullet-list'>
                    <li>
                      Select the city you want to explore. The highlighted zone shows where routing
                      is available.
                    </li>
                    <li>Type in your starting point and destination.</li>
                    <li>You will receive three alternative routes</li>
                    <li>
                      Each route displays an average <strong>US Air Quality Index (AQI) </strong>
                      value (lower is better).
                    </li>
                  </ul>

                  <p>
                    <strong>Blue:</strong> Fastest route (not optimized for air quality)
                    <br />
                    <strong>Green:</strong> Maximum air-quality optimization
                    <br />
                    <strong>Custom:</strong> Use the slider to balance speed & air cleanliness
                  </p>
                </section>
                {/* ---------------- LOOP FEATURE (own subsection) ---------------- */}
                <section>
                  <h3>Loop Feature</h3>
                  <p>
                    Runners can generate a clean-air loop by selecting a starting point and choosing
                    the desired total distance. EcoPaths will calculate a round trip optimized for
                    air-quality exposure.
                  </p>
                </section>

                {/* ---------------- DATA & METHODS ---------------- */}
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
                    </a>
                  </p>

                  <p>
                    <strong>Air quality data: </strong>
                    Real-time
                    <strong> US Air Quality Index (AQI)</strong> from{' '}
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
                    <strong>Routing logic:</strong> Walking ≈ 1.4 m/s, Running ≈ 3.0 m/s. Routes are
                    computed using weighted combinations of distance and estimated exposure.
                  </p>

                  {/* placeholder for route weighting */}
                  <p>
                    <em>Route weighting details: _______________________________________</em>
                  </p>
                </section>

                {/* ---------------- TEAM ---------------- */}
                <section>
                  <h2>Team</h2>
                  <p>
                    <strong>PathPlanners</strong> — Software Engineering Project, University of
                    Helsinki.
                  </p>
                  {/* team names */}
                  <p>
                    <strong>Team members:</strong>
                    <br />
                    Eero Jantunen <br />
                    Ilari Ranin <br />
                    Juho Kronlöf <br />
                    Laura Anttila <br />
                    Suvi Liimatainen <br />
                    Uyen Hoang
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

                {/* ---------------- ACKNOWLEDGMENTS ---------------- */}
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

                {/* ---------------- WARNING ---------------- */}
                <div className='warning-box'>
                  <AlertTriangle size={50} data-testid="warning-icon" />
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
