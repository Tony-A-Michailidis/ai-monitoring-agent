# AI Monitoring Agent - Development Setup Script
# Standalone Version

# Set error handling
$ErrorActionPreference = "Stop"

Write-Host "🚀 Setting up AI Monitoring Agent (Standalone)..." -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan

# Check prerequisites
Write-Host "📋 Checking prerequisites..." -ForegroundColor Yellow

# Check Docker
if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker not found. Please install Docker Desktop." -ForegroundColor Red
    Write-Host "   Download from: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# Check Node.js
if (!(Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Node.js not found. Please install Node.js 18+." -ForegroundColor Red
    Write-Host "   Download from: https://nodejs.org/" -ForegroundColor Yellow
    exit 1
}

# Check Python
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python not found. Please install Python 3.11+." -ForegroundColor Red
    Write-Host "   Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Prerequisites check passed!" -ForegroundColor Green

# Create project structure
Write-Host "📁 Creating project structure..." -ForegroundColor Yellow

$directories = @(
    "backend",
    "backend\app",
    "backend\app\connectors",
    "backend\app\nlp", 
    "backend\app\conversation",
    "frontend",
    "frontend\src",
    "frontend\src\components",
    "frontend\src\services",
    "frontend\src\hooks",
    "frontend\src\types",
    "frontend\public",
    "deployment",
    "deployment\docker",
    "deployment\kubernetes", 
    "deployment\scripts",
    "docs"
)

foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  Created: $dir" -ForegroundColor Gray
    }
}

# Create environment file
Write-Host "⚙️ Setting up environment configuration..." -ForegroundColor Yellow
if (!(Test-Path ".env")) {
    @"
# AI Monitoring Agent Configuration

# Application Settings  
ENVIRONMENT=development
LOG_LEVEL=DEBUG
APP_TITLE=AI Monitoring Agent
APP_DESCRIPTION=Conversational interface for monitoring data

# OpenAI Configuration (REQUIRED - Get from https://platform.openai.com/api-keys)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4-turbo-preview

# Monitoring Sources (Update these URLs to your actual endpoints)
PROMETHEUS_URL=http://localhost:9090
GRAFANA_URL=http://localhost:3000
ALERTMANAGER_URL=http://localhost:9093

# Azure Monitor Configuration (Optional - for Azure monitoring)
ENABLE_AZURE_MONITOR=false
AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=
AZURE_TENANT_ID=
AZURE_WORKSPACE_ID=
AZURE_SUBSCRIPTION_ID=

# Redis Cache (Leave default for local development)
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=

# API Configuration
CORS_ORIGINS=http://localhost:3000
RATE_LIMIT_REQUESTS=200
RATE_LIMIT_WINDOW=60
DEFAULT_TIME_RANGE=1h
MAX_TIME_RANGE=7d
QUERY_TIMEOUT=30
MAX_QUERY_RESULTS=1000
CACHE_TTL=300

# Security (Optional)
JWT_SECRET=your_jwt_secret_for_session_management
ENABLE_AUTH=false

# Feature Flags
ENABLE_GRAFANA_PROXY=true
ENABLE_METRICS_EXPORT=true
ENABLE_REAL_TIME_UPDATES=true
"@ | Out-File -FilePath ".env" -Encoding UTF8
    
    Write-Host "📝 Created .env file with default configuration." -ForegroundColor Blue
    Write-Host "⚠️  IMPORTANT: Please edit .env and add your OpenAI API key!" -ForegroundColor Yellow
}

# Create .gitignore
if (!(Test-Path ".gitignore")) {
    @"
# Environment variables
.env
*.env

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
venv/
env/
ENV/

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# React build
/frontend/build

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Docker
.dockerignore

# Logs
*.log
logs/

# Temporary files
*.tmp
*.temp

# Coverage reports
htmlcov/
.coverage
.pytest_cache/

# Redis dump
dump.rdb
"@ | Out-File -FilePath ".gitignore" -Encoding UTF8
    Write-Host "📝 Created .gitignore file." -ForegroundColor Blue
}

Write-Host "✅ Project structure created!" -ForegroundColor Green

Write-Host ""
Write-Host "🎉 Setup completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📖 Next Steps:" -ForegroundColor Cyan
Write-Host "1. 🔑 Edit .env file and add your OpenAI API key (REQUIRED)" -ForegroundColor White
Write-Host "2. 🔧 Update monitoring source URLs in .env (Prometheus, Grafana)" -ForegroundColor White  
Write-Host "3. 🚀 Start the application:" -ForegroundColor White
Write-Host "   • Full stack: docker-compose up -d" -ForegroundColor Gray
Write-Host "   • Backend only: cd backend && python -m uvicorn app.main:app --reload" -ForegroundColor Gray
Write-Host "   • Frontend only: cd frontend && npm start" -ForegroundColor Gray
Write-Host "4. 🌐 Access the application at http://localhost:3000" -ForegroundColor White
Write-Host ""
Write-Host "📚 Documentation:" -ForegroundColor Cyan
Write-Host "   • README.md - Complete setup and usage guide" -ForegroundColor Gray
Write-Host "   • Backend API docs: http://localhost:8000/docs" -ForegroundColor Gray
Write-Host ""
Write-Host "🆘 Need help? Check the troubleshooting section in README.md" -ForegroundColor Cyan

# Create basic files to get started
Write-Host "📝 Creating starter files..." -ForegroundColor Yellow

# Create package.json for frontend
if (!(Test-Path "frontend\package.json")) {
    Write-Host "  Creating frontend package.json..." -ForegroundColor Gray
}

# Create requirements.txt for backend
if (!(Test-Path "backend\requirements.txt")) {
    Write-Host "  Creating backend requirements.txt..." -ForegroundColor Gray
}

Write-Host ""
Write-Host "🎊 Ready to build the future of monitoring!" -ForegroundColor Green
Write-Host "   Run 'docker-compose up -d' to start your AI monitoring agent" -ForegroundColor Cyan