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
        <Info size={24} data-testid='info-icon' />
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
                  <X size={20} data-testid='close-icon' />
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
                    <li>
                      You will receive three alternative routes with different optimization
                      strategies.
                    </li>
                    <li>
                      Each route displays an average <strong>US Air Quality Index (AQI) </strong>
                      value (lower is better).
                    </li>
                    <li>Click on any route card to select it and view it on the map.</li>
                  </ul>

                  <h3>Route Types</h3>

                  <p>
                    <strong>
                      Best AQ (<span style={{ color: '#008b23' }}>Green</span>):
                    </strong>{' '}
                    Maximizes air quality by selecting paths with the lowest pollution levels. This
                    route may be longer in distance but offers the cleanest air.
                  </p>

                  <p>
                    <strong>
                      Fastest (<span style={{ color: '#003cff' }}>Blue</span>):
                    </strong>{' '}
                    Prioritizes the shortest travel time without considering air quality. This is
                    the most direct path to your destination.
                  </p>

                  <p>
                    <strong>
                      Custom (<span style={{ color: '#01a597ff' }}>Cyan</span>):
                    </strong>{' '}
                    Use the slider to find your preferred balance between speed and air quality.
                    Adjust the weight to create a personalized route that matches your priorities.
                  </p>

                  <p>
                    <em>
                      Note: Click any route card to view detailed PM2.5 and PM10 exposure graphs
                      along your journey.
                    </em>
                  </p>
                </section>
                {/* ---------------- LOOP FEATURE (own subsection) ---------------- */}
                <section>
                  <h3>Loop Feature</h3>
                  <p>
                    Toggle Loop mode to create circular routes that start and end at the same
                    location. Select your desired distance (1-5 km), and you'll receive up to three
                    optimized loop options:
                  </p>
                  <ul className='bullet-list'>
                    <li>The first loop prioritizes the best possible air quality.</li>
                    <li>
                      Additional loops explore different directions while maintaining good air
                      quality.
                    </li>
                    <li>Route lengths are approximate and may vary based on available paths.</li>
                  </ul>
                  <p>
                    <em>
                      Note: The number of loops generated (1-3) depends on your starting location
                      and available routing options.
                    </em>
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
                    <strong>Air quality data:</strong> Real-time{' '}
                    <strong>US Air Quality Index (AQI)</strong> values from{' '}
                    <a
                      href='https://developers.google.com/maps/documentation/air-quality'
                      target='_blank'
                      rel='noopener noreferrer'
                    >
                      Google Air Quality API
                    </a>
                  </p>

                  <p>
                    <strong>Speed assumptions:</strong> Walking: 5 km/h, Running: 10.8 km/h
                  </p>

                  <p>
                    <strong>Route optimization:</strong> Routes are weighted using real-time AQI
                    data, traffic proximity (penalties near busy roads), and green space proximity
                    (benefits near green areas and trees). The algorithm balances these factors with
                    distance to recommend healthier paths.
                  </p>
                </section>

                {/* ---------------- TEAM ---------------- */}
                <section>
                  <h2>Team</h2>
                  <p>
                    We are <strong>PathPlanners</strong>, a software development team from the
                    University of Helsinki.
                  </p>
                  <p>
                    <strong>Team members:</strong> Eero Jantunen, Ilari Ranin, Juho Kronlöf, Laura
                    Anttila, Suvi Liimatainen, Uyen Hoang
                  </p>

                  <p>
                    <strong>Github Repository:</strong>{' '}
                    <a
                      href='https://github.com/OhtuProjektiSyksy25/EcoPaths'
                      target='_blank'
                      rel='noopener noreferrer'
                    >
                      EcoPaths (Frontend / Backend)
                    </a>
                  </p>
                </section>

                {/* ---------------- ACKNOWLEDGMENTS ---------------- */}
                <section>
                  <h2>Acknowledgments</h2>
                  <p>
                    Inspired by the{' '}
                    <a
                      href='https://github.com/DigitalGeographyLab/hope-green-path-ui'
                      target='_blank'
                      rel='noopener noreferrer'
                    >
                      Green Paths
                    </a>{' '}
                    project from the Digital Geography Lab, University of Helsinki.
                  </p>
                </section>

                {/* ---------------- WARNING ---------------- */}
                <div className='warning-box'>
                  <AlertTriangle size={50} data-testid='warning-icon' />
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
