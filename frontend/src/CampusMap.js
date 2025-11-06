import React, { useState } from 'react';
import { COLORS, OCCUPANCY_THRESHOLDS } from './constants';
import './CampusMap.css';

function CampusMap({ parkingLots }) {
  const [isExpanded, setIsExpanded] = useState(true);

  const getOccupancyColor = (occupancy) => {
    if (occupancy <= OCCUPANCY_THRESHOLDS.GREEN_MAX) return COLORS.GREEN;
    if (occupancy <= OCCUPANCY_THRESHOLDS.YELLOW_MAX) return COLORS.YELLOW;
    return COLORS.RED;
  };

  const getLotData = (lotId) => {
    return parkingLots.find(lot => lot.lot === lotId) || null;
  };

  // Map coordinates for the 4 lots (relative positions on the map)
  const lotPositions = {
    G: { x: 25, y: 30 },
    H: { x: 75, y: 30 },
    J: { x: 25, y: 70 },
    M: { x: 75, y: 70 },
  };

  const lots = ['G', 'H', 'J', 'M'];

  return (
    <section className="campus-map-section" aria-label="Campus parking map">
      <div className="map-header">
        <h2 className="map-title">Campus Map</h2>
        <button
          className="map-toggle-button"
          onClick={() => setIsExpanded(!isExpanded)}
          aria-expanded={isExpanded}
          aria-controls="campus-map-content"
          aria-label={isExpanded ? 'Collapse map' : 'Expand map'}
        >
          {isExpanded ? '−' : '+'}
        </button>
      </div>
      <div
        id="campus-map-content"
        className={`map-content ${isExpanded ? 'expanded' : 'collapsed'}`}
      >
        <div className="map-container">
          <svg
            viewBox="0 0 100 100"
            className="campus-map-svg"
            aria-label="Penn State Abington campus map"
            role="img"
          >
            {/* Simple campus map background */}
            <rect
              x="0"
              y="0"
              width="100"
              height="100"
              fill="#E9EEF3"
              stroke={COLORS.BEAVER_BLUE}
              strokeWidth="0.5"
            />
            
            {/* Roads/paths */}
            <line x1="0" y1="50" x2="100" y2="50" stroke={COLORS.BEAVER_BLUE} strokeWidth="0.3" strokeDasharray="1,1" />
            <line x1="50" y1="0" x2="50" y2="100" stroke={COLORS.BEAVER_BLUE} strokeWidth="0.3" strokeDasharray="1,1" />

            {/* Parking lot markers */}
            {lots.map((lotId) => {
              const lotData = getLotData(lotId);
              const occupancy = lotData ? lotData.occupancy_pct : 0;
              const color = getOccupancyColor(occupancy);
              const pos = lotPositions[lotId];

              return (
                <g key={lotId}>
                  <circle
                    cx={pos.x}
                    cy={pos.y}
                    r="8"
                    fill={color}
                    stroke={COLORS.WHITE}
                    strokeWidth="1"
                    className="map-marker"
                    aria-label={`Parking Lot ${lotId}: ${occupancy}% occupied`}
                    role="img"
                  >
                    <title>Parking Lot {lotId}: {occupancy}% occupied</title>
                  </circle>
                  <text
                    x={pos.x}
                    y={pos.y + 18}
                    textAnchor="middle"
                    fontSize="6"
                    fill={COLORS.TEXT}
                    fontWeight="bold"
                  >
                    {lotId}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>
      </div>
    </section>
  );
}

export default CampusMap;

