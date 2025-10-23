import React from 'react';
import ParkingLotCard from './ParkingLotCard';
import './App.css';

function App() {
  const parkingLots = [
    { name: 'Parking Lot A', occupancy: 85 },
    { name: 'Parking Lot B', occupancy: 62 },
    { name: 'Parking Lot C', occupancy: 91 },
    { name: 'Parking Lot D', occupancy: 45 },
    { name: 'Parking Lot E', occupancy: 78 },
    { name: 'Parking Lot F', occupancy: 55 },
    { name: 'Parking Lot G', occupancy: 93 },
    { name: 'Parking Lot H', occupancy: 38 },
    { name: 'Parking Lot I', occupancy: 72 },
    { name: 'Parking Lot J', occupancy: 88 },
    { name: 'Parking Lot K', occupancy: 41 },
    { name: 'Parking Lot L', occupancy: 67 },
    { name: 'Parking Lot M', occupancy: 54 },
  ];

  return (
    <div className="app">
      <header className="app-header">
        <h1>Campus Parking Status</h1>
      </header>
      <div className="parking-grid">
        {parkingLots.map((lot) => (
          <ParkingLotCard
            key={lot.name}
            lotName={lot.name}
            occupancy={lot.occupancy}
          />
        ))}
      </div>
    </div>
  );
}

export default App;
