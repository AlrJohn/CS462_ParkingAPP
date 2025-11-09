# Configuration file for API keys and settings
# IMPORTANT: This file should be in .gitignore to keep API keys secure

import os
import secrets

# Generate a secure API key if one doesn't exist
def get_or_create_api_key():
    """Get API key from environment variable or use default."""
    api_key = os.getenv('API_KEY')
    if not api_key:
        # Use default key for development/testing
        api_key = '123'
        print(f"Using default API key: {api_key}")
        print("To use a different key, set environment variable: export API_KEY='your_key_here'")
    return api_key

# API Configuration
API_KEY = get_or_create_api_key()

# CORS Configuration - allowed origins for frontend
ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React dev server
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "https://cs-462-parking-app.vercel.app",
    # Add your production frontend URL here when deployed
    # "https://your-frontend-domain.com"
]

# Server Configuration
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5002))
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

