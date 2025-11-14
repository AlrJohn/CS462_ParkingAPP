// Import API configuration first
import { API_ENDPOINTS, getApiHeaders } from './apiConfig';

// Penn State Brand Colors
export const COLORS = {
  NITTANY_NAVY: '#001E44',
  BEAVER_BLUE: '#1E407C',
  WHITE: '#FFFFFF',
  LIGHT_GRAY: '#E9EEF3',
  TEXT: '#0B2141',
  // Occupancy Colors
  GREEN: '#22c55e',      // Open (≤60%)
  YELLOW: '#f59e0b',     // Busy (61-85%)
  RED: '#ef4444',        // Full (>85%)
};

// Occupancy Thresholds
export const OCCUPANCY_THRESHOLDS = {
  GREEN_MAX: 60,   // ≤60% = Green (Open)
  YELLOW_MAX: 85,  // 61-85% = Yellow (Busy)
  // >85% = Red (Full)
};

// Spacing Values (in pixels)
export const SPACING = {
  XS: '8px',
  SM: '12px',
  MD: '16px',
  LG: '20px',
  XL: '24px',
  XXL: '40px',
  // Specific spacing
  HEADER_PADDING: '16px 20px',
  CARD_PADDING: '24px',
  SECTION_PADDING: '20px',
  GRID_GAP: '24px',
  GRID_GAP_MOBILE: '16px',
  MAP_PADDING: '20px',
};

// Border Radius Values
export const RADIUS = {
  SM: '4px',
  MD: '8px',
  LG: '12px',
  CIRCLE: '50%',
};

// Box Shadow Values
export const SHADOWS = {
  SM: '0 2px 4px rgba(0, 0, 0, 0.1)',
  MD: '0 2px 8px rgba(0, 30, 68, 0.1)',
  LG: '0 4px 12px rgba(0, 30, 68, 0.15)',
  CARD: '0 2px 8px rgba(0, 30, 68, 0.1)',
  CARD_HOVER: '0 4px 12px rgba(0, 30, 68, 0.15)',
};

// Transition Durations
export const TRANSITIONS = {
  FAST: '0.2s',
  NORMAL: '0.3s',
  SLOW: '0.5s',
  EASE: 'ease',
  EASE_OUT: 'ease-out',
};

// Responsive Breakpoints (in pixels)
export const BREAKPOINTS = {
  MOBILE: 768,
  TABLET: 1024,
  DESKTOP: 1025,
};

// Re-export API configuration for convenience
export const API_URL = API_ENDPOINTS.GET_LOT_COUNT;
export const API_HEADERS = getApiHeaders;
export const REFRESH_INTERVAL = 30000; // 30 seconds

// Allowed Parking Lots (Student Parking)
export const ALLOWED_LOTS = ['G', 'H', 'J', 'M'];
