# PSUPark Backend API

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set API Key

You have two options for setting the API key:

**Option A: Environment Variable (Recommended)**
```bash
export API_KEY='your-secure-api-key-here'
python app.py
```

**Option B: Let the app generate one**
The app will automatically generate an API key if none is set. Check the console output for the generated key.

### 3. Run the Server

```bash
python app.py
```

The server will start on `http://localhost:5002` by default.

## API Endpoints

All endpoints require an API key in the request header:

### GET /getLotCount
Returns all parking lot data.

**Headers:**
```
X-API-Key: your-api-key-here
```

**Response:**
```json
[
  {
    "lot": "G",
    "available_spaces": 169,
    "capacity": 169,
    "occupied_spaces": 0,
    "occupancy_pct": 0.0
  },
  ...
]
```

### POST /updateLotCount
Updates parking lot count.

**Headers:**
```
X-API-Key: your-api-key-here
Content-Type: application/json
```

**Body:**
```json
{
  "lot": "G",
  "delta": -1
}
```

## CORS Configuration

The backend is configured to allow requests from:
- `http://localhost:3000` (React dev server)
- `http://localhost:3001`
- `http://127.0.0.1:3000`
- `http://127.0.0.1:3001`

To add production URLs, edit `config.py` and add to `ALLOWED_ORIGINS`.

## Security Notes

- Never commit `config.py` with hardcoded API keys
- Use environment variables for API keys in production
- Keep your API key secure and don't share it publicly
- The API key is required for all endpoints

