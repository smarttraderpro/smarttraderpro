# Smart Trader Hub

**Smart Trader Hub** is a full-stack software solution designed for Indian intraday traders. It aims to support real trading via broker APIs (AngelOne, Zerodha, Upstox) and allow paper trading with comprehensive performance tracking, across Web, Windows Desktop, and Android/iOS platforms.

## Project Overview

This project is divided into several key components:

*   **Backend (`/backend`)**: A Python FastAPI application serving the core logic, API, and database interactions.
*   **Web Dashboard (`/frontend_web`)**: A ReactJS single-page application for the web interface.
*   **Windows Desktop App (`/frontend_desktop`)**: An Electron-based application for Windows users.
*   **Mobile App (`/mobile_app`)**: A Flutter application for Android and iOS devices.

## Features (Planned)

*   **User Authentication**: Secure signup/login (email, mobile, OTP), role-based access, profile management.
*   **Live Market Dashboard**: Real-time data for Nifty, BankNifty, Sensex, India VIX.
*   **Broker Integration**: Connect AngelOne, Zerodha, Upstox accounts; fetch data; place orders.
*   **Paper Trading Engine**: Mock trading with virtual capital and performance tracking.
*   **Trade Journal & Analytics**: Detailed statistics and equity curve visualization.
*   **Learning Hub**: Tutorials and quizzes on trading concepts.
*   **Strategy Center**: Manual and (future) automated trading strategy setup.
*   **Cross-Platform Support**: Web, Windows (.exe), Android/iOS.

## Tech Stack

*   **Backend**: Python (FastAPI)
*   **Database**: PostgreSQL
*   **Market Data**: `yfinance` library (for fetching stock/index data)
*   **Web Frontend**: ReactJS
*   **Windows Desktop Frontend**: Electron (with HTML/JS/CSS, potentially a framework like React/Vue)
*   **Mobile Frontend**: Flutter (Dart)
*   **API Communication**: RESTful APIs
*   **Containerization**: Docker (for backend and database)

## Implemented Features (Phase 1)

*   **User Authentication**: Secure signup (with email OTP verification and account activation), login, role-based access (basic setup), profile management (`/users/me`), secure storage of (mock) broker API keys via Fernet encryption.
*   **Live Market Dashboard (Backend & Web UI)**:
    *   Backend service to fetch live data for Nifty, BankNifty, Sensex, and India VIX using the `yfinance` library.
    *   API endpoint (`/api/v1/market/live-indices`) to serve this data.
    *   Web dashboard displays Symbol, LTP, Change (points & %), with periodic refresh.
*   **Development Infrastructure**:
    *   Docker setup for backend and PostgreSQL database.
    *   Unit tests for backend authentication and user modules.
    *   Placeholder projects for Electron and Flutter frontends.
    *   Basic project and API documentation.


## Getting Started

### Prerequisites

*   Python (3.10+) for backend development.
*   Node.js and npm/yarn for frontend development (React, Electron).
*   Flutter SDK for mobile app development.
*   Docker and Docker Compose for running the backend and database services.
*   Access to a PostgreSQL instance (can be run via Docker Compose).

### Backend Setup

1.  **Navigate to the backend directory**:
    ```bash
    cd backend
    ```
2.  **Create and activate a virtual environment** (recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure Environment Variables**:
    *   The backend uses settings from `backend/core/config.py`. Critical settings like database URL, JWT secrets, and encryption keys might need to be configured via environment variables or a `.env` file (if Pydantic settings is configured to load it).
    *   Ensure `CREDENTIALS_ENCRYPTION_KEY` and `SECRET_KEY` in `backend/core/config.py` (or environment) are set to secure, unique values for production.
5.  **Database Migrations**:
    *   Ensure your PostgreSQL server is running and accessible.
    *   Update `alembic.ini` (or environment variables used by `backend/core/config.py`) with your database connection details.
    *   Run Alembic migrations from the project root directory:
        ```bash
        # Ensure PYTHONPATH includes the project root if running from outside backend dir
        # export PYTHONPATH=$(pwd):$PYTHONPATH
        alembic -c alembic.ini upgrade head
        ```
6.  **Run the backend server**:
    ```bash
    uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
    ```
    The API will be available at `http://localhost:8000`.

### Dockerized Backend Setup

Alternatively, use Docker Compose to run the backend and PostgreSQL database:

1.  **Ensure Docker and Docker Compose are installed.**
2.  **(Optional) Create a `.env` file** in the project root to customize environment variables (see `docker-compose.yml` for examples like `POSTGRES_USER`, `SECRET_KEY`).
3.  **Build and run the services**:
    ```bash
    docker-compose up --build -d
    ```
4.  **Run database migrations against the containerized DB**:
    ```bash
    docker-compose exec backend alembic -c /app/alembic.ini upgrade head
    # (The alembic.ini inside the container at /app/alembic.ini will be used, as WORKDIR is /app)
    ```
    The API will be available at `http://localhost:8000`.

### Web Frontend Setup (`frontend_web`)

1.  **Navigate to the web frontend directory**:
    ```bash
    cd frontend_web
    ```
2.  **Install dependencies**:
    ```bash
    npm install
    # or yarn install
    ```
3.  **Run the development server**:
    ```bash
    npm start
    # or yarn start
    ```
    The React app will typically open at `http://localhost:3000` and proxy API requests to `http://localhost:8000` (as configured in `package.json`).

### Desktop Frontend Setup (`frontend_desktop`)

1.  **Navigate to the desktop frontend directory**:
    ```bash
    cd frontend_desktop
    ```
2.  **Install dependencies**:
    ```bash
    npm install
    # or yarn install
    ```
3.  **Run the Electron app**:
    ```bash
    npm start
    # or yarn start
    ```

### Mobile Frontend Setup (`mobile_app`)

1.  **Navigate to the mobile app directory**:
    ```bash
    cd mobile_app
    ```
2.  **Ensure Flutter SDK is installed and configured.**
3.  **Get dependencies**:
    ```bash
    flutter pub get
    ```
4.  **Run the app** (on a connected device or emulator):
    ```bash
    flutter run
    ```
    Refer to `mobile_app/README.md` for more details if a full Flutter project is initialized.

## API Documentation

The backend API documentation (Swagger UI) is automatically generated by FastAPI and can be accessed at:

*   `http://localhost:8000/docs` (Swagger UI)
*   `http://localhost:8000/redoc` (ReDoc)

When the backend is running.

## Project Structure

```
smart-trader-hub/
├── backend/                  # FastAPI backend application
│   ├── alembic/              # Alembic database migrations
│   │   └── versions/         # Migration scripts
│   ├── app/                  # Core application logic, models, schemas, API endpoints
│   │   ├── api/              # API routers and versions
│   │   │   └── v1/
│   │   │       ├── endpoints/  # Specific endpoint files (auth.py, users.py)
│   │   │       └── api.py      # v1 API router aggregator
│   │   ├── core/             # Configuration, security utilities, OTP logic
│   │   ├── db/               # Database session management
│   │   ├── models.py         # SQLAlchemy models
│   │   ├── schemas.py        # Pydantic schemas
│   │   ├── crud.py           # CRUD operations
│   │   ├── dependencies.py   # FastAPI dependencies
│   │   └── main.py           # FastAPI app instance and main entry point
│   ├── tests/                # Backend unit and integration tests
│   │   ├── api/
│   │   │   └── v1/           # Tests for v1 API endpoints
│   │   └── conftest.py       # Pytest shared fixtures
│   └── requirements.txt      # Python dependencies
├── frontend_web/             # ReactJS web dashboard
│   ├── public/
│   ├── src/
│   │   ├── components/       # React components (Login, Signup, Dashboard etc.)
│   │   ├── App.js
│   │   ├── index.js
│   │   └── api.js            # Axios API client
│   └── package.json
├── frontend_desktop/         # Electron desktop application
│   ├── main.js               # Electron main process
│   ├── index.html            # Main HTML for renderer
│   ├── renderer.js           # Renderer process JS
│   ├── preload.js            # Optional preload script
│   └── package.json
├── mobile_app/               # Flutter mobile application
│   ├── lib/
│   │   └── main.dart         # Main Flutter application code
│   ├── test/
│   └── pubspec.yaml
├── .dockerignore             # Files to ignore for Docker builds
├── Dockerfile                # Dockerfile for the backend
├── docker-compose.yml        # Docker Compose for backend and DB
├── alembic.ini               # Alembic configuration (project root)
└── README.md                 # This file
```

## Contributing

(Details on contributing to the project can be added here later.)

## License

(License information can be added here later.)
---

*This README provides a high-level overview. Each sub-project (backend, frontend_web, etc.) may have its own more detailed README file.*
