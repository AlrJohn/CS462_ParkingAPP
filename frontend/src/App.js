import React, { useEffect, useState } from 'react';
import ParkingLotCard from './ParkingLotCard';
import LoadingSkeleton from './LoadingSkeleton';
import ErrorBanner from './ErrorBanner';
import { API_URL, API_HEADERS, REFRESH_INTERVAL, ALLOWED_LOTS, OCCUPANCY_THRESHOLDS } from './constants';
import './App.css';

function App() {
  const [parkingLots, setParkingLots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchLots = async () => {
    try {
      const res = await fetch(API_URL, {
        method: 'GET',
        headers: API_HEADERS(),
      });
      
      if (!res.ok) {
        if (res.status === 401) {
          throw new Error('Unauthorized: Invalid or missing API key');
        }
        throw new Error(`Failed to fetch: ${res.status} ${res.statusText}`);
      }
      
      const data = await res.json();

      let lotsArray = [];

      if (Array.isArray(data)) {
        // Backend returns an array of objects like { lot: 'G', occupancy_pct: 45.0, ... }
        lotsArray = data
          .filter((item) => {
            const lotKey = item.lot || item.name || item.lotName || '';
            const lotId = typeof lotKey === 'string' ? lotKey.replace(/[^A-Z]/gi, '').toUpperCase() : '';
            return ALLOWED_LOTS.includes(lotId);
          })
          .map((item) => {
            const lotKey = item.lot || item.name || item.lotName || '';
            const lotId = typeof lotKey === 'string' ? lotKey.replace(/[^A-Z]/gi, '').toUpperCase() : '';
            const occupancyRaw = item.occupancy_pct ?? item.occupancy ?? item.occupied_spaces ?? null;
            const occupancy = occupancyRaw == null ? 0 : Math.round(Number(occupancyRaw));
            return {
              lot: lotId,
              occupancy_pct: occupancy,
              available_spaces: item.available_spaces,
              capacity: item.capacity,
              occupied_spaces: item.occupied_spaces,
            };
          });
      } else if (data && typeof data === 'object') {
        // If backend returns a dictionary/object mapping
        lotsArray = Object.entries(data)
          .filter(([key]) => {
            const lotId = typeof key === 'string' ? key.replace(/[^A-Z]/gi, '').toUpperCase() : '';
            return ALLOWED_LOTS.includes(lotId);
          })
          .map(([key, val]) => {
            const lotId = typeof key === 'string' ? key.replace(/[^A-Z]/gi, '').toUpperCase() : '';
            const availableSpaces = typeof val === 'number' ? val : 0;
            return {
              lot: lotId,
              occupancy_pct: 0,
              available_spaces: availableSpaces,
            };
          });
      }

      // Sort by lot ID (G, H, J, M)
      lotsArray.sort((a, b) => {
        const order = { G: 0, H: 1, J: 2, M: 3 };
        return (order[a.lot] || 99) - (order[b.lot] || 99);
      });

      setParkingLots(lotsArray);
      setError(null);
      setLastUpdated(new Date());
    } catch (err) {
      setError(err.message || 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Set CSS custom property for background image
    document.documentElement.style.setProperty(
      '--bg-image-url',
      `url(${process.env.PUBLIC_URL || ''}/image.png)`
    );
  }, []);

  useEffect(() => {
    let mounted = true;
    let intervalId = null;

    const initialFetch = async () => {
      await fetchLots();
      if (mounted) {
        // Set up polling
        intervalId = setInterval(() => {
          fetchLots();
        }, REFRESH_INTERVAL);
      }
    };

    initialFetch();

    return () => {
      mounted = false;
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, []);

  return (
    <div className="app">
      <header className="app-header" role="banner">
        <div className="header-content">
          <div className="logo-container">
            <img
              src="/logo.jpg"
              alt="Penn State Abington Logo"
              className="psu-logo"
            />
          </div>
          <h1 className="app-title">PSUPark – Student Parking Availability</h1>
        </div>
      </header>

      <main className="app-main">
        {error && <ErrorBanner message={`Error loading parking data: ${error}`} onClose={() => setError(null)} />}

        {loading ? (
          <LoadingSkeleton />
        ) : (
          <>
            {parkingLots.length === 0 ? (
              <div className="no-data" role="alert">No parking data available.</div>
            ) : (
              <>
                <div className="parking-grid">
                  {parkingLots.map((lot) => (
                    <ParkingLotCard
                      key={lot.lot}
                      lot={lot.lot}
                      occupancy={lot.occupancy_pct}
                      capacity={lot.capacity}
                      occupiedSpaces={lot.occupied_spaces}
                      lastUpdated={lastUpdated}
                    />
                  ))}
                </div>
                <div className="legend-container">
                  <div className="legend" role="region" aria-label="Parking status color legend">
                    <div className="legend-item">
                      <div className="legend-color green" aria-hidden="true"></div>
                      <span>Open (≤{OCCUPANCY_THRESHOLDS.GREEN_MAX}%)</span>
                    </div>
                    <span className="legend-separator" aria-hidden="true">•</span>
                    <div className="legend-item">
                      <div className="legend-color yellow" aria-hidden="true"></div>
                      <span>Busy ({OCCUPANCY_THRESHOLDS.GREEN_MAX + 1}–{OCCUPANCY_THRESHOLDS.YELLOW_MAX}%)</span>
                    </div>
                    <span className="legend-separator" aria-hidden="true">•</span>
                    <div className="legend-item">
                      <div className="legend-color red" aria-hidden="true"></div>
                      <span>Full (&gt;{OCCUPANCY_THRESHOLDS.YELLOW_MAX}%)</span>
                    </div>
                  </div>
                </div>
              </>
            )}
          </>
        )}
      </main>
    </div>
  );
}

export default App;
