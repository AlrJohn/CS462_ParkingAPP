import React, { useState } from 'react';
import { COLORS, OCCUPANCY_THRESHOLDS } from './constants';
import './CampusMap.css';

function CampusMap({ parkingLots }) {
  const [hoveredLot, setHoveredLot] = useState(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  const getOccupancyColor = (occupancy) => {
    if (occupancy <= OCCUPANCY_THRESHOLDS.GREEN_MAX) return COLORS.GREEN;
    if (occupancy <= OCCUPANCY_THRESHOLDS.YELLOW_MAX) return COLORS.YELLOW;
    return COLORS.RED;
  };

  const getLotData = (lotId) => {
    return parkingLots.find(lot => lot.lot === lotId) || null;
  };

  // Define parking lot zones with percentage-based coordinates
  // Percentages relative to the 1867x1294 image dimensions
  // Format: { lotId, xPercent, yPercent, widthPercent, heightPercent }
  const parkingZones = [
    { lotId: 'G', xPercent: (580 / 1867) * 100, yPercent: (230 / 1294) * 100, widthPercent: (280 / 1867) * 100, heightPercent: (250 / 1294) * 100, label: 'Lot G' },
    { lotId: 'H', xPercent: (1000 / 1867) * 100, yPercent: (800 / 1294) * 100, widthPercent: (250 / 1867) * 100, heightPercent: (200 / 1294) * 100, label: 'Lot H' },
    { lotId: 'J', xPercent: (340 / 1867) * 100, yPercent: (870 / 1294) * 100, widthPercent: (150 / 1867) * 100, heightPercent: (120 / 1294) * 100, label: 'Lot J' },
    { lotId: 'M', xPercent: (710 / 1867) * 100, yPercent: (1000 / 1294) * 100, widthPercent: (150 / 1867) * 100, heightPercent: (120 / 1294) * 100, label: 'Lot M' },
  ];

  const handleZoneHover = (zone, event) => {
    setHoveredLot(zone.lotId);
    // Get the position of the zone relative to the viewport
    const element = event.currentTarget;
    const rect = element.getBoundingClientRect();
    
    // Default: position tooltip to the right of the zone
    let x = rect.right + 10;
    let y = rect.top + rect.height / 2;
    
    // If tooltip would go off-screen to the right, position to the left instead
    if (x + 250 > window.innerWidth) {
      x = rect.left - 10;
    }
    
    // If tooltip would go off-screen at the top, position it below instead
    if (y - 100 < 0) {
      y = rect.bottom + 10;
    }
    
    setTooltipPos({
      x: x,
      y: y,
    });
  };

  const handleZoneLeave = () => {
    setHoveredLot(null);
  };

  return (
    <div className="campus-map-full-screen">
      <header className="campus-map-header">
        <h1 className="campus-map-title">Campus Parking Map</h1>
        <p className="campus-map-subtitle">Hover over parking areas to view occupancy</p>
      </header>

      <div className="map-wrapper">
        <img
          src="/image.png"
          alt="Campus Map"
          className="campus-map-image"
        />

        {/* Parking lot hover zones */}
        <div className="zones-overlay">
          {parkingZones.map((zone) => {
            const lotData = getLotData(zone.lotId);
            const occupancy = lotData?.occupancy_pct ?? 0;
            const isHovered = hoveredLot === zone.lotId;

            return (
              <div
                key={zone.lotId}
                className={`parking-zone ${isHovered ? 'hovered' : ''}`}
                style={{
                  left: `${zone.xPercent}%`,
                  top: `${zone.yPercent}%`,
                  width: `${zone.widthPercent}%`,
                  height: `${zone.heightPercent}%`,
                  borderColor: getOccupancyColor(occupancy),
                }}
                onMouseEnter={(e) => handleZoneHover(zone, e)}
                onMouseLeave={handleZoneLeave}
                title={`Lot ${zone.lotId}: ${occupancy}% occupied`}
                role="button"
                tabIndex={0}
                aria-label={`Parking Lot ${zone.lotId}: ${occupancy}% occupied`}
              />
            );
          })}
        </div>

        {/* Tooltip card on hover */}
        {hoveredLot && (
          <div
            className="parking-tooltip"
            style={{
              left: `${tooltipPos.x}px`,
              top: `${tooltipPos.y}px`,
            }}
            role="tooltip"
          >
            {(() => {
              const lotData = getLotData(hoveredLot);
              const occupancy = lotData?.occupancy_pct ?? 0;
              return (
                <>
                  <h3 className="tooltip-title">Parking Lot {hoveredLot}</h3>
                  <div className="tooltip-occupancy">
                    <div
                      className="occupancy-circle"
                      style={{
                        borderColor: getOccupancyColor(occupancy),
                      }}
                    >
                      <span className="occupancy-value">{occupancy}%</span>
                    </div>
                    <p className="occupancy-label">Occupied</p>
                  </div>
                  {lotData && (
                    <div className="tooltip-details">
                      <p>
                        <strong>Available:</strong> {lotData.available_spaces || 'N/A'}
                      </p>
                      <p>
                        <strong>Capacity:</strong> {lotData.capacity || 100}
                      </p>
                    </div>
                  )}
                </>
              );
            })()}
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="map-legend">
        <h4>Occupancy Status</h4>
        <div className="legend-items">
          <div className="legend-item">
            <span className="legend-color" style={{ backgroundColor: COLORS.GREEN }}></span>
            <span>Open (≤{OCCUPANCY_THRESHOLDS.GREEN_MAX}%)</span>
          </div>
          <div className="legend-item">
            <span className="legend-color" style={{ backgroundColor: COLORS.YELLOW }}></span>
            <span>Busy ({OCCUPANCY_THRESHOLDS.GREEN_MAX + 1}–{OCCUPANCY_THRESHOLDS.YELLOW_MAX}%)</span>
          </div>
          <div className="legend-item">
            <span className="legend-color" style={{ backgroundColor: COLORS.RED }}></span>
            <span>Full (&gt;{OCCUPANCY_THRESHOLDS.YELLOW_MAX}%)</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default CampusMap;

