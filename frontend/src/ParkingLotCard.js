import React from 'react';
import { COLORS, OCCUPANCY_THRESHOLDS } from './constants';
import './ParkingLotCard.css';

function ParkingLotCard({ lot, occupancy }) {
  const getOccupancyColor = (occupancy) => {
    if (occupancy <= OCCUPANCY_THRESHOLDS.GREEN_MAX) return COLORS.GREEN;
    if (occupancy <= OCCUPANCY_THRESHOLDS.YELLOW_MAX) return COLORS.YELLOW;
    return COLORS.RED;
  };

  const lotId = lot || 'Unknown';
  const occupancyValue = Math.round(occupancy || 0);

  return (
    <div
      className="parking-lot-card"
      role="article"
      aria-label={`Student Parking Lot ${lotId}: ${occupancyValue}% occupied`}
      tabIndex={0}
    >
      <h2 className="lot-name">Student Parking Lot {lotId}</h2>
      <div
        className="occupancy-circle"
        style={{ borderColor: getOccupancyColor(occupancyValue) }}
        aria-label={`Occupancy: ${occupancyValue}%`}
      >
        <span className="occupancy-value">{occupancyValue}%</span>
      </div>
      <div className="occupancy-label">OCCUPIED</div>
    </div>
  );
}

export default ParkingLotCard;
