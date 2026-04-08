# FakeShield

A comprehensive fake news detection platform combining machine learning, blockchain verification, and geolocation analytics.

## Project Overview

FakeShield is a multi-component system designed to detect, verify, and track fake news with geographic insights and blockchain integrity.

## Components

### Backend (`/backend`)
- Python FastAPI application
- REST API for ML model predictions
- Database integration
- Web scraping capabilities

### Frontend (`/frontend`)
- React + Vite application
- Real-time news analysis dashboard
- History tracking
- Responsive UI with monitoring capabilities

### Machine Learning (`/ml`)
- Fake news detection models
- Data preprocessing pipelines
- Model training and evaluation
- Pre-trained models included

### Blockchain (`/blockchain`)
- Blockchain integration for news verification
- Immutable record keeping

### Chrome Extension (`/chrome-extension`)
- Browser extension for inline fake news detection
- Real-time analysis while browsing

### Geo Analytics (`/geo-analytics`)
- Geographic analysis of news sources
- Location-based insights

## Getting Started

### Prerequisites
- Python 3.8+
- Node.js 16+
- Docker & Docker Compose

### Installation

1. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   ```

3. **ML Setup**
   ```bash
   cd ml
   pip install -r requirements.txt
   ```

### Running the Application

#### Using Docker Compose
```bash
docker-compose up
```

#### Local Development
```bash
# Terminal 1: Backend
cd backend
python main.py

# Terminal 2: Frontend
cd frontend
npm run dev
```

## API Documentation

The backend API provides endpoints for:
- News analysis and fake detection
- Model predictions
- Data collection and scraping
- Historical data management

## Features

- 🔍 **Real-time Detection**: Analyze news for authenticity
- 📊 **Dashboard**: Visualize analysis results
- 🔗 **Blockchain Verified**: Immutable verification records
- 🌍 **Geo Analytics**: Geographic source tracking
- 🧠 **ML Models**: Advanced fake news detection
- 🔌 **Browser Integration**: Chrome extension support

## Technology Stack

- **Backend**: Python, FastAPI
- **Frontend**: React, Vite
- **ML**: scikit-learn, joblib
- **Blockchain**: Custom implementation
- **Deployment**: Docker, Docker Compose

## Project Structure

```
FakeShield/
├── backend/           # FastAPI application
├── frontend/          # React application
├── ml/                # ML models and training
├── blockchain/        # Blockchain integration
├── chrome-extension/  # Browser extension
├── geo-analytics/     # Geographic analytics
├── docker-compose.yml # Container orchestration
└── Dockerfile.backend # Backend container config
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Commit with clear messages
4. Push and create a pull request

## License

[Add your license here]

## Contact

[Add contact information]
