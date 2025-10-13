from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import logging
from typing import Optional, Dict, Any, List
import os
from datetime import datetime
import asyncio

# Import our modules
from .config import settings
from .models import ChatRequest, ChatResponse, HealthResponse, ErrorResponse
from .cache import get_redis_client
from .auth import get_current_user

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables for connectors (will be initialized in lifespan)
connector_manager = None
conversation_engine = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup application resources"""
    global connector_manager, conversation_engine
    
    logger.info("🚀 Starting AI Monitoring Agent...")
    
    try:
        # Import connectors here to avoid circular imports
        from .connectors.manager import ConnectorManager
        from .ai import ConversationEngine
        
        # Initialize Redis client
        redis_client = await get_redis_client()
        logger.info("✅ Redis connection established")
        
        # Initialize connector manager
        connector_manager = ConnectorManager(settings)
        logger.info("✅ Connector manager initialized")
        
        # Check connector health
        health_status = await connector_manager.health_check_all()
        for name, healthy in health_status.items():
            status = "✅" if healthy else "❌"
            logger.info(f"{status} {name.title()} connector: {'healthy' if healthy else 'unhealthy'}")
        
        # Initialize conversation engine
        if settings.openai_api_key and settings.openai_api_key != "your_openai_api_key_here":
            conversation_engine = ConversationEngine(settings, connector_manager)
            logger.info("✅ Conversation engine initialized")
        else:
            logger.warning("⚠️ OpenAI API key not configured - conversation engine disabled")
        
        logger.info("🎉 AI Monitoring Agent startup complete!")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    yield  # Application runs here
    
    # Cleanup
    logger.info("🔄 Shutting down AI Monitoring Agent...")
    if 'redis_client' in locals():
        await redis_client.close()
    logger.info("👋 Shutdown complete")

# Create FastAPI app
app = FastAPI(
    title=settings.app_title,
    description=settings.app_description,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(",") if settings.cors_origins != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with basic info"""
    return {
        "message": "AI Monitoring Agent API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint for container orchestration"""
    checks = {}
    overall_status = "healthy"
    
    try:
        # Check Redis
        try:
            redis_client = await get_redis_client()
            await redis_client.ping()
            checks["redis"] = "healthy"
        except Exception as e:
            checks["redis"] = f"unhealthy: {str(e)}"
            overall_status = "unhealthy"
        
        # Check connectors
        if connector_manager:
            try:
                connector_health = await connector_manager.health_check_all()
                for name, healthy in connector_health.items():
                    if healthy:
                        checks[f"connector_{name}"] = "healthy"
                    else:
                        checks[f"connector_{name}"] = "unhealthy"
                        overall_status = "degraded"
                
                if not connector_health:
                    checks["connectors"] = "none_configured"
                    overall_status = "degraded"
            except Exception as e:
                checks["connectors"] = f"error: {str(e)}"
                overall_status = "unhealthy"
        else:
            checks["connectors"] = "not_initialized"
            overall_status = "unhealthy"
            
        # Check conversation engine
        if conversation_engine:
            checks["conversation_engine"] = "healthy"
        else:
            checks["conversation_engine"] = "not_configured"
            overall_status = "degraded"
        
        return HealthResponse(
            status=overall_status,
            timestamp=datetime.utcnow(),
            checks=checks,
            version="1.0.0"
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.utcnow(),
            checks={"error": str(e)},
            version="1.0.0"
        )

@app.get("/ready", tags=["Health"])
async def readiness_check():
    """Readiness check for Kubernetes"""
    if not conversation_engine:
        raise HTTPException(
            status_code=503, 
            detail="Service not ready - conversation engine not initialized"
        )
    return {"status": "ready", "timestamp": datetime.utcnow()}

@app.post("/api/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """Main chat endpoint for conversational monitoring queries"""
    try:
        logger.info(f"Chat request from user: {request.message[:100]}...")
        
        if not conversation_engine:
            # Return a helpful error message if not configured
            return ChatResponse(
                message="I'm not fully configured yet. Please check that your OpenAI API key and monitoring sources are set up correctly in the .env file.",
                session_id=request.session_id or "default",
                query_type=None,
                timestamp=datetime.utcnow(),
                processing_time=0.0
            )
        
        # Process the conversation
        start_time = asyncio.get_event_loop().time()
        
        response = await conversation_engine.process_message(
            message=request.message,
            session_id=request.session_id or "default",
            user_id=current_user.get("user_id") if current_user else "anonymous",
            context=request.context or {}
        )
        
        processing_time = asyncio.get_event_loop().time() - start_time
        response.processing_time = processing_time
        
        return response
        
    except Exception as e:
        logger.error(f"Chat processing failed: {e}")
        return ChatResponse(
            message=f"I encountered an error processing your request: {str(e)}. Please try again or check your configuration.",
            session_id=request.session_id or "default",
            query_type=None,
            timestamp=datetime.utcnow(),
            processing_time=0.0
        )

@app.get("/api/sessions/{session_id}/history", tags=["Chat"])
async def get_session_history(
    session_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """Get conversation history for a session"""
    try:
        if not conversation_engine:
            raise HTTPException(status_code=503, detail="Conversation engine not initialized")
            
        history = await conversation_engine.get_session_history(session_id)
        return {"session_id": session_id, "history": history}
        
    except Exception as e:
        logger.error(f"Failed to get session history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/sessions/{session_id}", tags=["Chat"])
async def clear_session(
    session_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """Clear conversation history for a session"""
    try:
        if not conversation_engine:
            raise HTTPException(status_code=503, detail="Conversation engine not initialized")
            
        await conversation_engine.clear_session(session_id)
        return {"message": "Session cleared successfully"}
        
    except Exception as e:
        logger.error(f"Failed to clear session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/metrics/summary", tags=["Metrics"])
async def get_metrics_summary(
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """Get a summary of available metrics and services"""
    try:
        if not connector_manager:
            raise HTTPException(status_code=503, detail="Connector manager not initialized")
            
        # Get summary from all connectors
        summaries = await connector_manager.get_all_metrics_summary()
        all_services = await connector_manager.get_all_services()
        
        # Combine data
        total_metrics = sum(len(s.get("metric_names", [])) for s in summaries.values())
        all_services_list = []
        for services in all_services.values():
            all_services_list.extend(services)
        
        return {
            "metrics_count": total_metrics,
            "services": list(set(all_services_list)),
            "connectors": list(summaries.keys()),
            "connector_summaries": summaries,
            "last_updated": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Failed to get metrics summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/alerts", tags=["Alerts"])
async def get_active_alerts(
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """Get current active alerts"""
    try:
        if not connector_manager:
            raise HTTPException(status_code=503, detail="Connector manager not initialized")
            
        # Get alerts from all connectors
        alerts_results = await connector_manager.get_all_alerts()
        all_alerts = []
        for connector_alerts in alerts_results.values():
            all_alerts.extend(connector_alerts)
            
        return {"alerts": all_alerts, "count": len(all_alerts), "timestamp": datetime.utcnow()}
        
    except Exception as e:
        logger.error(f"Failed to get active alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Global HTTP exception handler"""
    logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "timestamp": datetime.utcnow().isoformat()}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error", 
            "message": str(exc) if settings.environment == "development" else "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower()
    )