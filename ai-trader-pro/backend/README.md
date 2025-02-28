# AI Trader Pro Backend

The backend service for AI Trader Pro platform, built with FastAPI and Python.

## Features

- Real-time market data processing
- AI-powered trading strategies
- User authentication and authorization
- Portfolio management
- Trade execution
- WebSocket support for real-time updates

## Setup

1. Install dependencies:
```bash
poetry install
```

2. Run the development server:
```bash
poetry run uvicorn app.main:app --reload
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc 