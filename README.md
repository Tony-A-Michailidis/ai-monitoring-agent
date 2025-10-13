# AI Monitoring Agent 

A conversational AI interface for monitoring systems.

## 🎯 Overview

(extensive documentation here: https://deepwiki.com/Tony-A-Michailidis/ai-monitoring-agent)

This standalone version provides powerful AI-driven monitoring capabilities with simplified deployment using Docker Compose. Perfect for:

- **Local Development**: Quick setup for testing and development
- **Small to Medium Deployments**: Production-ready without Kubernetes complexity
- **Proof of Concept**: Demonstrate AI monitoring capabilities
- **Teams Without K8s**: Get advanced monitoring without orchestration overhead

## ✨ Features

- 🤖 **Conversational Interface**: Chat with your monitoring data using natural language
- 📊 **Multi-Source Support**: Connect to Prometheus, Azure Monitor, and other data sources
- 🚨 **Real-time Alerts**: Intelligent summaries of active alerts and incidents
- 🐳 **Easy Deployment**: Simple Docker Compose setup with minimal configuration
- 💻 **Modern Web UI**: React-based interface with responsive design and dark theme
- ⚡ **High Performance**: Redis caching and async processing throughout
- 🔍 **Health Monitoring**: Comprehensive health checks for all components
- 🧩 **Modular Architecture**: Clean separation between connectors, AI processing, and UI

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend│    │   FastAPI       │    │   Redis Cache   │
│   (Port 3000)   │◄──►│   Backend       │◄──►│   (Port 6379)   │
│                 │    │   (Port 8000)   │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  AI & Connectors│
                    │                 │
                    │ ┌─────────────┐ │
                    │ │OpenAI GPT-4 │ │
                    │ └─────────────┘ │
                    │ ┌─────────────┐ │
                    │ │ Prometheus  │ │
                    │ └─────────────┘ │
                    │ ┌─────────────┐ │
                    │ │Azure Monitor│ │
                    │ └─────────────┘ │
                    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Docker & Docker Compose**: For container orchestration
- **OpenAI API Key**: Required for conversational AI features
- **Monitoring Systems**: Prometheus, Azure Monitor, or other sources

### Installation

1. **Create project directory**:
   ```powershell
   mkdir ai-monitoring-agent-standalone
   cd ai-monitoring-agent-standalone
   ```

2. **Set up environment**:
   ```powershell
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env with your settings (see Configuration section)
   notepad .env  # or your preferred editor
   ```

3. **Configure your OpenAI API key** (required):
   ```bash
   OPENAI_API_KEY=sk-your-openai-api-key-here
   ```

4. **Configure monitoring sources** (optional but recommended):
   ```bash
   # For Prometheus
   PROMETHEUS_URL=http://your-prometheus:9090
   
   # For Azure Monitor
   AZURE_SUBSCRIPTION_ID=your-subscription-id
   AZURE_CLIENT_ID=your-client-id
   AZURE_CLIENT_SECRET=your-client-secret
   AZURE_TENANT_ID=your-tenant-id
   ```

5. **Start the application**:
   ```powershell
   docker-compose up --build
   ```

6. **Access the interface**:
   - **Frontend UI**: http://localhost:3000
   - **Backend API**: http://localhost:8000
   - **API Documentation**: http://localhost:8000/docs

## ⚙️ Configuration

### Required Settings

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for AI features | `sk-abc123...` |

### Optional Monitoring Sources

| Variable | Description | Default |
|----------|-------------|---------|
| `PROMETHEUS_URL` | Prometheus server URL | Not configured |
| `PROMETHEUS_USERNAME` | Basic auth username | - |
| `PROMETHEUS_PASSWORD` | Basic auth password | - |
| `AZURE_SUBSCRIPTION_ID` | Azure subscription ID | - |
| `AZURE_CLIENT_ID` | Service principal client ID | - |
| `AZURE_CLIENT_SECRET` | Service principal secret | - |
| `AZURE_TENANT_ID` | Azure tenant ID | - |

### Application Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Application environment | `development` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `AUTH_ENABLED` | Enable JWT authentication | `false` |
| `CORS_ORIGINS` | Allowed CORS origins | `*` |

## 💬 Usage Examples

### Chat Interface

The conversational interface supports natural language queries:

**System Health**:
- *"What's the overall system health?"*
- *"Show me system status"*
- *"Are all services running normally?"*

**Metrics Queries**:
- *"What's the CPU usage across all services?"*
- *"Show memory consumption for the last hour"*
- *"Network traffic trends"*
- *"Disk usage by service"*

**Alert Management**:
- *"Show me active alerts"*
- *"Any critical issues right now?"*
- *"Alert summary for today"*

**Service-Specific**:
- *"How is the API service performing?"*
- *"Show metrics for database connections"*
- *"Any performance issues in the frontend?"*

### API Integration

Direct API access for programmatic integration:

```bash
# Health check
curl http://localhost:8000/health

# Send chat message
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show system health", 
    "session_id": "my-session"
  }'

# Get metrics summary
curl http://localhost:8000/api/metrics/summary

# Get active alerts
curl http://localhost:8000/api/alerts

# Get available services
curl http://localhost:8000/api/services
```

## 🛠️ Development

### Local Development Setup

**Backend Development**:
```powershell
cd backend
pip install -r requirements.txt

# Set environment variables
$env:OPENAI_API_KEY = "your-key-here"
$env:REDIS_URL = "redis://localhost:6379"

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend Development**:
```powershell
cd frontend
npm install

# Set API URL for development
$env:REACT_APP_API_URL = "http://localhost:8000/api"

# Run development server
npm start
```

**Redis for Development**:
```powershell
docker run -p 6379:6379 redis:7-alpine
```

### Project Structure

```
ai-monitoring-agent-standalone/
├── backend/                    # FastAPI backend service
│   ├── app/
│   │   ├── main.py            # Application entry point
│   │   ├── config.py          # Configuration management
│   │   ├── models.py          # Data models and schemas
│   │   ├── connectors/        # Monitoring system connectors
│   │   │   ├── base.py        # Base connector interface
│   │   │   ├── prometheus.py  # Prometheus connector
│   │   │   ├── azure_monitor.py # Azure Monitor connector
│   │   │   └── manager.py     # Connector orchestration
│   │   └── ai/                # AI processing modules
│   │       ├── nlp_processor.py       # NLP and query parsing
│   │       └── conversation_engine.py # Conversation management
│   └── requirements.txt       # Python dependencies
├── frontend/                  # React TypeScript frontend
│   ├── src/
│   │   ├── components/        # UI components
│   │   │   ├── ChatInterface.tsx      # Main chat interface
│   │   │   ├── Dashboard.tsx          # Metrics dashboard
│   │   │   ├── AlertsPanel.tsx        # Alerts view
│   │   │   └── Sidebar.tsx            # Navigation
│   │   ├── services/api.ts    # API client
│   │   └── App.tsx           # Main app component
│   └── package.json          # Node.js dependencies
├── docker-compose.yml         # Service orchestration
├── .env.example              # Configuration template
└── README.md                 # This file
```

## 🔧 Troubleshooting

### Common Issues

**1. "OpenAI API key not configured"**
- ✅ Ensure `OPENAI_API_KEY` is set in `.env`
- ✅ Verify API key format (starts with `sk-`)
- ✅ Check API key has available credits

**2. "No data sources configured"**
- ✅ Configure at least one monitoring source
- ✅ Check network connectivity to monitoring systems
- ✅ Verify credentials and URLs are correct

**3. Frontend connection issues**
- ✅ Verify backend health: `curl http://localhost:8000/health`
- ✅ Check Docker networks: `docker-compose ps`
- ✅ Review logs: `docker-compose logs backend`

**4. Redis connection problems**
- ✅ Ensure Redis container is running
- ✅ Check Redis logs: `docker-compose logs redis`
- ✅ Verify Redis URL configuration

### Debugging

**View Logs**:
```powershell
# All services
docker-compose logs

# Specific service
docker-compose logs backend
docker-compose logs frontend
docker-compose logs redis

# Follow logs real-time
docker-compose logs -f backend
```

**Enable Debug Mode**:
```bash
# In .env file
LOG_LEVEL=DEBUG
ENVIRONMENT=development
```

## 🔒 Security

### Production Security Checklist

- [ ] Replace default secret keys
- [ ] Enable authentication: `AUTH_ENABLED=true`
- [ ] Configure specific CORS origins (not `*`)
- [ ] Use HTTPS with SSL termination
- [ ] Secure Redis with password
- [ ] Regular security updates
- [ ] Implement rate limiting
- [ ] Monitor for vulnerabilities

### Best Practices

1. **Never commit API keys** to version control
2. **Use environment variables** for sensitive configuration
3. **Enable authentication** in production environments
4. **Configure proper firewall rules**
5. **Implement monitoring** for the monitoring system itself

## 🤝 Contributing

We welcome contributions! Please:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Follow** coding standards and add tests
4. **Update** documentation as needed
5. **Submit** a pull request with clear description

## 📄 License

See the main repository for license details.

## 🆘 Support

**Need Help?**

1. 📖 Check this documentation and troubleshooting section
2. 🔍 Review Docker Compose logs for error details
3. ⚙️ Verify configuration in `.env` file
4. 🌐 Test network connectivity to data sources
5. 💬 Check existing issues in the repository

**When Reporting Issues**, include:
- Docker Compose logs
- Configuration (with sensitive data redacted)
- Steps to reproduce
- Environment details

---

**🚀 By the way, all this was done entirely by another AI agent! So, as soon as you pick your jaw from the floor, copy the project files, configure your `.env`, and run `docker-compose up --build`!

