# Running with Docker

## Prerequisites
1. **Start Docker Desktop** - Make sure Docker Desktop is running on your Mac
2. Ensure ports 8000 and 27017 are available

## Quick Start

### 1. Start Docker Desktop
- Open Docker Desktop application
- Wait until it's fully started (whale icon in menu bar should be steady)

### 2. Build and Start Services
```bash
cd /Users/abhishekkumar/Desktop/ubo-trace-engine-backend

# Stop any existing containers
docker-compose down

# Build and start services
docker-compose up --build -d

# View logs
docker-compose logs -f
```

### 3. Verify Services
```bash
# Check container status
docker-compose ps

# Test API
curl http://localhost:8000/api/v1/health

# Access API docs
open http://localhost:8000/docs
```

## Docker Compose Services

- **app**: FastAPI backend server (port 8000)
- **mongodb**: MongoDB database (port 27017)

## Useful Commands

```bash
# View logs
docker-compose logs -f app          # App logs
docker-compose logs -f mongodb      # MongoDB logs

# Stop services
docker-compose stop

# Restart services
docker-compose restart

# Stop and remove containers
docker-compose down

# Remove volumes (clean slate)
docker-compose down -v
```

## Environment Variables

The `.env` file is automatically loaded. Make sure it contains:
- `LYZR_API_KEY`
- `LYZR_USER_ID`
- `MONGODB_URL` (will be overridden by docker-compose to use local MongoDB)

## Access

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **MongoDB**: localhost:27017

