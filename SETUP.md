# PSUPark Setup Guide

## Quick Start

### Backend Setup

1. **Install Python dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Set your API key (choose one method):**

   **Option A: Environment Variable (Recommended)**
   ```bash
   export API_KEY='your-secure-api-key-here'
   python app.py
   ```

   **Option B: Let the app generate one**
   The app will auto-generate an API key on first run. Check the console output for the generated key.

3. **Start the backend server:**
   ```bash
   python app.py
   ```
   
   The server will start on `http://localhost:5002` and display the API key in the console.

### Frontend Setup

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Configure API Key:**

   **Option A: Environment Variable (Recommended)**
   Create a `.env` file in the `frontend` folder:
   ```
   REACT_APP_API_KEY=your-api-key-here
   REACT_APP_API_BASE_URL=http://localhost:5002
   ```
   
   **Option B: Update apiConfig.js directly**
   Edit `frontend/src/apiConfig.js` and replace `'your-api-key-here'` with your actual API key.

3. **Start the frontend:**
   ```bash
   npm start
   ```

## Important Notes

- **API Key Security**: Never commit API keys to version control. Use environment variables or `.env` files (which should be in `.gitignore`).
- **CORS**: The backend is configured to allow requests from `localhost:3000` and `localhost:3001`. For production, update `backend/config.py` with your production frontend URL.
- **Backend must be running**: Make sure the backend server is running on port 5002 before starting the frontend.

## Troubleshooting

### "ERR_CONNECTION_REFUSED" Error

This means the backend server is not running. 
1. Make sure you've started the backend server (`python app.py` in the backend folder)
2. Check that it's running on port 5002
3. Verify the API key in the frontend matches the one in the backend

### "Unauthorized: Invalid or missing API key" Error

1. Check that the API key in `frontend/src/apiConfig.js` matches the one in the backend
2. Make sure you've set the `REACT_APP_API_KEY` environment variable if using that method
3. Restart the frontend after changing the API key

### CORS Errors

If you see CORS errors, make sure:
1. The frontend is running on `localhost:3000` or `localhost:3001`
2. The backend's `ALLOWED_ORIGINS` in `config.py` includes your frontend URL
3. Both servers are running

