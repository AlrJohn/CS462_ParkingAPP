import React from 'react';
import './ParkingLotCard.css';

function ParkingLotCard({ lotName, occupancy }) {
  const getOccupancyColor = (occupancy) => {
    if (occupancy >= 90) return '#ef4444';
    if (occupancy >= 70) return '#f59e0b';
    return '#22c55e';
  };

  return (
    <div className="parking-lot-card">
      <h2 className="lot-name">{lotName}</h2>
      <div
        className="occupancy-circle"
        style={{ borderColor: getOccupancyColor(occupancy) }}
      >
        <span className="occupancy-value">{occupancy}%</span>
      </div>
      <div className="occupancy-label">Occupied</div>
    </div>
  );
}

export default ParkingLotCard;
