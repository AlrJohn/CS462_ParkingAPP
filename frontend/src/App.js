import React, { useEffect, useState } from 'react';
import ParkingLotCard from './ParkingLotCard';
import './App.css';

function App() {
  const [parkingLots, setParkingLots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;

    const fetchLots = async () => {
      try {
        const res = await fetch('http://localhost:5002/getLotCount');
        if (!res.ok) throw new Error(`Failed to fetch: ${res.status} ${res.statusText}`);
        const data = await res.json();

        let lotsArray = [];

        if (Array.isArray(data)) {
          // Backend returns an array of objects like { lot: 'A', occupancy_pct: 45.0, ... }
          lotsArray = data.map((item) => {
            const lotKey = item.lot || item.name || item.lotName || '';
            const occupancyRaw = item.occupancy_pct ?? item.occupancy ?? item.occupied_spaces ?? null;
            const occupancy = occupancyRaw == null ? 0 : Math.round(Number(occupancyRaw));
            const name = typeof lotKey === 'string' && lotKey.toLowerCase().includes('parking')
              ? lotKey
              : `Parking Lot ${lotKey}`;
            return { name, occupancy };
          });
        } else if (data && typeof data === 'object') {
          // If backend returns a dictionary/object mapping
          // e.g., { "Parking Lot A": 85 } or { "A": 85 }
          lotsArray = Object.entries(data).map(([key, val]) => {
            const occupancy = Math.round(Number(val || 0));
            const name = typeof key === 'string' && key.toLowerCase().includes('parking')
              ? key
              : `Parking Lot ${key}`;
            return { name, occupancy };
          });
        }

        if (mounted) setParkingLots(lotsArray);
      } catch (err) {
        if (mounted) setError(err.message || 'Unknown error');
      } finally {
        if (mounted) setLoading(false);
      }
    };

    fetchLots();

    return () => {
      mounted = false;
    };
  }, []);



  return (
    <div className="app">
      <header className="app-header">
        <h1>Campus Parking Status</h1>
      </header>
      {loading ? (
        <div className="loading">Loading parking data…</div>
      ) : error ? (
        <div className="error">Error loading parking data: {error}</div>
      ) : (
        <div className="parking-grid">
          {parkingLots.length === 0 ? (
            <div className="no-data">No parking data available.</div>
          ) : (
            parkingLots.map((lot) => (
              <ParkingLotCard
                key={lot.name}
                lotName={lot.name}
                occupancy={lot.occupancy}
              />
            ))
          )}
        </div>
      )}
    </div>
  );
}

export default App;
