// API Configuration
// IMPORTANT: In production, this should be set via environment variables
// and this file should be in .gitignore

// API Key - This should match the backend API_KEY
// For development, you can set this in your environment or update it here
// For production, use environment variables: REACT_APP_API_KEY
// 
// SETUP INSTRUCTIONS:
// 1. Start the backend server first - it will display an API key in the console
// 2. Copy that API key and either:
//    - Set environment variable: export REACT_APP_API_KEY='your-key-here'
//    - Or update the default value below (NOT recommended for production)
export const API_KEY = process.env.REACT_APP_API_KEY || '123';

// API Base URL
export const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || "https://cs462-parkingapp.onrender.com/";

// API Endpoints
export const API_ENDPOINTS = {
  GET_LOT_COUNT: `${API_BASE_URL}/getLotCount`,
  UPDATE_LOT_COUNT: `${API_BASE_URL}/updateLotCount`,
};

// Request headers with API key
export const getApiHeaders = () => {
  return {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY,
  };
};

