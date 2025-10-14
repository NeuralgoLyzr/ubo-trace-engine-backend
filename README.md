# UBO Trace Engine Backend

A comprehensive backend system for Ultimate Beneficial Owner (UBO) tracing using Lyzr AI agents. This system implements a 4-stage tracing process to identify direct and indirect ownership connections between entities and beneficial owners with verified factual evidence.

## 🚀 Features

- **4-Stage AI Tracing**: Direct and indirect evidence collection with time-filtered searches
- **Lyzr AI Integration**: Seamless integration with Lyzr AI agents for each tracing stage
- **Simplified Parameters**: Only requires entity, UBO name, location, and optional domain
- **Verified Sources**: All findings include verified URLs and source citations
- **RESTful API**: Complete REST API for trace management and results retrieval
- **MongoDB Storage**: Persistent storage for traces and results
- **Batch Processing**: Support for processing multiple traces concurrently
- **Real-time Monitoring**: Live status tracking and progress monitoring
- **Comprehensive Logging**: Detailed logging for debugging and monitoring
- **Docker Support**: Easy deployment with Docker and Docker Compose

## 🏗️ Architecture

The system follows a modular architecture with clear separation of concerns:

```
├── app.py                 # Main FastAPI application
├── api/
│   └── endpoints.py       # API route handlers
├── models/
│   └── schemas.py         # Pydantic data models
├── services/
│   ├── lyzr_service.py        # Lyzr AI agent integration
│   └── ubo_trace_service.py   # Core UBO tracing logic
├── utils/
│   ├── settings.py        # Configuration management
│   └── database.py        # MongoDB connection and utilities
└── requirements.txt       # Python dependencies
```

## 🔧 Installation & Setup

### Prerequisites

- Python 3.11+
- MongoDB 7.0+
- Docker & Docker Compose (optional)

### Local Development Setup

1. **Clone and navigate to the project:**
   ```bash
   cd /Users/abhishekkumar/Desktop/ubo-trace-engine-backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start MongoDB:**
   ```bash
   # Using Docker
   docker run -d -p 27017:27017 --name mongodb mongo:7.0
   
   # Or install MongoDB locally
   # Follow MongoDB installation guide for your OS
   ```

5. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

6. **Run the application:**
   ```bash
   python app.py
   ```

### Docker Setup

1. **Using Docker Compose (Recommended):**
   ```bash
   docker-compose up --build
   ```

2. **Using Docker only:**
   ```bash
   # Build the image
   docker build -t ubo-trace-engine .
   
   # Run with MongoDB
   docker run -d --name mongodb -p 27017:27017 mongo:7.0
   docker run -d --name ubo-backend -p 8000:8000 --link mongodb ubo-trace-engine
   ```

## 📚 API Documentation

Once running, access the interactive API documentation at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Core Endpoints

#### UBO Trace Management

- `POST /api/v1/trace` - Create a new UBO trace
- `POST /api/v1/trace/{trace_id}/execute` - Execute a trace (all 4 stages)
- `GET /api/v1/trace/{trace_id}` - Get trace details
- `GET /api/v1/trace/{trace_id}/summary` - Get complete trace summary
- `GET /api/v1/trace/{trace_id}/stages` - Get individual stage results
- `DELETE /api/v1/trace/{trace_id}` - Delete a trace

#### Batch Operations

- `POST /api/v1/trace/batch` - Execute multiple traces in batch

#### Monitoring & Statistics

- `GET /api/v1/traces` - List all traces with filtering
- `GET /api/v1/traces/stats` - Get trace statistics
- `GET /api/v1/health` - Health check with service status

## 🔍 UBO Tracing Process

The system implements a 4-stage tracing process:

### Stage 1A: Direct Evidence (General)
- Searches company registries, beneficial ownership filings
- Looks for official documents and government data
- Focuses on verified factual information

### Stage 1B: Direct Evidence (Time-filtered)
- Time-scoped search (Jan 2023 - present)
- Recent ownership filings and appointments
- Updated government and regulator databases

### Stage 2A: Indirect Evidence (General)
- Investigates layered ownership structures
- Parent/subsidiary relationships, funds, trusts
- Cross-border vehicles and nominee shareholders

### Stage 2B: Indirect Evidence (Time-filtered)
- Recent indirect connections (2023-2025)
- Acquisitions, restructurings, control transfers
- Fund ownership changes and trust amendments

## 📊 Data Models

### UBO Trace Request
```json
{
  "entity": "Louis Dreyfus Company Metals MEA DMCC",
  "ubo_name": "Liu Jianfeng",
  "location": "UAE",
  "domain_name": "louisdreyfus.com"  // Optional
}
```

### Trace Summary Response
```json
{
  "trace_id": "uuid",
  "entity": "Entity Name",
  "ubo_name": "UBO Name",
  "location": "Location",
  "overall_status": "completed",
  "has_direct_evidence": true,
  "has_indirect_evidence": false,
  "connection_status": "DIRECT CONNECTION",
  "total_urls": 15,
  "total_direct_facts": 3,
  "total_indirect_facts": 0,
  "stage_results": [...],
  "total_processing_time_ms": 45000
}
```

## 🚀 Usage Examples

### Create and Execute a Single Trace

```bash
# Create trace
curl -X POST "http://localhost:8000/api/v1/trace" \
  -H "Content-Type: application/json" \
  -d '{
    "entity": "Louis Dreyfus Company Metals MEA DMCC",
    "ubo_name": "Liu Jianfeng",
    "location": "UAE"
  }'

# Execute trace (replace {trace_id} with actual ID)
curl -X POST "http://localhost:8000/api/v1/trace/{trace_id}/execute"

# Get results
curl -X GET "http://localhost:8000/api/v1/trace/{trace_id}/summary"
```

### Batch Processing

```bash
curl -X POST "http://localhost:8000/api/v1/trace/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "traces": [
      {
        "entity": "Entity 1",
        "ubo_name": "UBO 1",
        "location": "Location 1"
      },
      {
        "entity": "Entity 2",
        "ubo_name": "UBO 2",
        "location": "Location 2"
      }
    ],
    "max_concurrent": 2
  }'
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MONGODB_URL` | MongoDB connection string | `mongodb://localhost:27017` | Yes |
| `DATABASE_NAME` | Database name | `ubo_trace_engine` | No |
| `LYZR_API_KEY` | Lyzr AI API key | - | Yes |
| `LYZR_USER_ID` | Lyzr user ID | - | Yes |
| `AGENT_STAGE_1A` | Agent ID for Stage 1A | - | Yes |
| `AGENT_STAGE_1B` | Agent ID for Stage 1B | - | Yes |
| `AGENT_STAGE_2A` | Agent ID for Stage 2A | - | Yes |
| `AGENT_STAGE_2B` | Agent ID for Stage 2B | - | Yes |
| `SESSION_STAGE_1A` | Session ID for Stage 1A | - | Yes |
| `SESSION_STAGE_1B` | Session ID for Stage 1B | - | Yes |
| `SESSION_STAGE_2A` | Session ID for Stage 2A | - | Yes |
| `SESSION_STAGE_2B` | Session ID for Stage 2B | - | Yes |
| `API_TIMEOUT` | API request timeout (seconds) | `60` | No |
| `RATE_LIMIT_PER_MINUTE` | Rate limit for API calls | `10` | No |

## 📈 Monitoring & Logging

### Health Checks

- `GET /health` - Basic health check
- `GET /api/v1/health` - Detailed health check with service status

### Logging

The application provides comprehensive logging:
- Request/response logging
- Error tracking
- Performance metrics
- Database operation logs

### Statistics

Access trace statistics:
```bash
curl -X GET "http://localhost:8000/api/v1/traces/stats"
```

## 🛠️ Development

### Project Structure

```
ubo-trace-engine-backend/
├── app.py                 # Main application entry point
├── api/
│   └── endpoints.py       # API route definitions
├── models/
│   └── schemas.py         # Pydantic data models
├── services/
│   ├── lyzr_service.py    # Lyzr AI integration
│   └── ubo_trace_service.py # Core business logic
├── utils/
│   ├── settings.py        # Configuration management
│   └── database.py         # Database utilities
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose setup
└── .env                  # Environment variables
```

### Adding New Features

1. **New API Endpoints**: Add to `api/endpoints.py`
2. **New Data Models**: Add to `models/schemas.py`
3. **New Services**: Add to `services/` directory
4. **New Utilities**: Add to `utils/` directory

### Testing

```bash
# Test Lyzr integration
python test_perplexity_integration.py

# Test specific endpoint
curl -X GET "http://localhost:8000/api/v1/health"
```

## 🚨 Troubleshooting

### Common Issues

1. **MongoDB Connection Failed**
   - Ensure MongoDB is running
   - Check connection string in `.env`
   - Verify network connectivity

2. **Lyzr API Errors**
   - Verify API key and user ID are correct
   - Check agent IDs and session IDs
   - Monitor API rate limits

3. **Trace Execution Failed**
   - Check logs for specific error messages
   - Verify input data format
   - Check Lyzr API status

### Debug Mode

Enable debug mode by setting `DEBUG=true` in `.env` file.

## 📄 License

This project is proprietary software. All rights reserved.

## 🤝 Support

For support and questions, please contact the development team.

---

**UBO Trace Engine Backend v1.0.0** - Comprehensive Ultimate Beneficial Owner tracing system powered by AI agents.
