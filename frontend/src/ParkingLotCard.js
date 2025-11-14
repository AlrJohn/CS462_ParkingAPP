import React from 'react';
import { COLORS, OCCUPANCY_THRESHOLDS } from './constants';
import './ParkingLotCard.css';

function ParkingLotCard({ lot, occupancy, capacity, occupiedSpaces, lastUpdated }) {
  const getOccupancyColor = (occupancy) => {
    if (occupancy <= OCCUPANCY_THRESHOLDS.GREEN_MAX) return COLORS.GREEN;
    if (occupancy <= OCCUPANCY_THRESHOLDS.YELLOW_MAX) return COLORS.YELLOW;
    return COLORS.RED;
  };

  const formatTimestamp = (date) => {
    if (!date) return '';
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const lotId = lot || 'Unknown';
  const occupancyValue = Math.round(occupancy || 0);
  const capacityValue = capacity != null ? capacity : 'N/A';
  const occupiedValue = occupiedSpaces != null ? occupiedSpaces : 'N/A';

  return (
    <div
      className="parking-lot-card"
      role="article"
      aria-label={`Student Parking Lot ${lotId}: ${occupancyValue}% occupied, ${occupiedValue} of ${capacityValue} spaces`}
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
      <div className="lot-details">
        <div className="lot-capacity">
          <span className="detail-label">Capacity:</span>
          <span className="detail-value">{capacityValue}</span>
        </div>
        <div className="lot-occupied">
          <span className="detail-label">Occupied:</span>
          <span className="detail-value">{occupiedValue}</span>
        </div>
      </div>
      {lastUpdated && (
        <div className="lot-timestamp" aria-live="polite">
          Last updated: {formatTimestamp(lastUpdated)}
        </div>
      )}
    </div>
  );
}

export default ParkingLotCard;
