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

// Re-export API configuration for convenience
export const API_URL = API_ENDPOINTS.GET_LOT_COUNT;
export const API_HEADERS = getApiHeaders;
export const REFRESH_INTERVAL = 30000; // 30 seconds

// Allowed Parking Lots (Student Parking)
export const ALLOWED_LOTS = ['G', 'H', 'J', 'M'];
