import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from ..models import ChatMessage, ConversationSummary
from ..cache import get_redis_client
from ..config import Settings
from .nlp_processor import NLPProcessor
from ..connectors.manager import ConnectorManager

logger = logging.getLogger(__name__)

class ConversationEngine:
    """Manages conversation flow and context for monitoring interactions"""
    
    def __init__(self, settings: Settings, connector_manager: ConnectorManager):
        self.settings = settings
        self.connector_manager = connector_manager
        self.nlp_processor = NLPProcessor(settings)
        self.redis = get_redis_client()
        
        # Conversation settings
        self.max_conversation_length = 50
        self.context_retention_hours = 24
        
    async def process_message(self, message: str, session_id: str, user_context: Dict[str, Any] = None) -> ChatMessage:
        """Process a user message and generate a response"""
        try:
            # Store user message
            user_message = ChatMessage(
                content=message,
                sender="user",
                timestamp=datetime.now()
            )
            
            await self._store_message(session_id, user_message)
            
            # Get conversation context
            conversation_history = await self._get_conversation_history(session_id)
            
            # Get available data sources
            available_services = await self.connector_manager.get_all_services()
            all_services = []
            for services in available_services.values():
                all_services.extend(services)
            
            metrics_summary = await self.connector_manager.get_all_metrics_summary()
            all_metrics = []
            for summary in metrics_summary.values():
                all_metrics.extend(summary.get('metric_names', []))
            
            # Parse the user query
            parsed_query = await self.nlp_processor.parse_user_query(
                message, all_services, all_metrics
            )
            
            # Execute the query based on intent
            response_content = await self._execute_query_and_respond(
                parsed_query, conversation_history, user_context or {}
            )
            
            # Create assistant response
            assistant_message = ChatMessage(
                content=response_content,
                sender="assistant",
                timestamp=datetime.now(),
                metadata={
                    "parsed_query": parsed_query,
                    "connectors_used": list(self.connector_manager.list_connectors())
                }
            )
            
            await self._store_message(session_id, assistant_message)
            
            return assistant_message
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            error_message = ChatMessage(
                content=f"I encountered an error processing your request: {str(e)}. Please try rephrasing your question.",
                sender="assistant",
                timestamp=datetime.now(),
                metadata={"error": str(e)}
            )
            
            await self._store_message(session_id, error_message)
            return error_message
    
    async def _execute_query_and_respond(self, parsed_query: Dict[str, Any], history: List[ChatMessage], context: Dict[str, Any]) -> str:
        """Execute the parsed query and generate a response"""
        try:
            intent = parsed_query.get('intent', 'unknown')
            query_type = parsed_query.get('query_type', 'metrics')
            
            # Handle different query types
            if query_type == 'alerts' or intent == 'alerts':
                return await self._handle_alerts_query(parsed_query, context)
            elif query_type == 'health' or intent == 'health':
                return await self._handle_health_query(parsed_query, context)
            elif query_type == 'services' or 'service' in parsed_query.get('original_query', '').lower():
                return await self._handle_services_query(parsed_query, context)
            else:
                return await self._handle_metrics_query(parsed_query, context)
                
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return f"I had trouble retrieving that information. Error: {str(e)}"
    
    async def _handle_metrics_query(self, parsed_query: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Handle metrics queries"""
        try:
            metrics = parsed_query.get('metrics', [])
            services = parsed_query.get('services', [])
            time_range = parsed_query.get('time_range', '1h')
            
            # Query all connectors
            all_results = {}
            
            # Try Prometheus first
            prometheus_conn = self.connector_manager.get_connector('prometheus')
            if prometheus_conn:
                prom_query = await self.nlp_processor.generate_prometheus_query(parsed_query)
                if prom_query:
                    prom_results = await prometheus_conn.query_metrics(prom_query, time_range=time_range)
                    if prom_results:
                        all_results['prometheus'] = prom_results
            
            # Try Azure Monitor
            azure_conn = self.connector_manager.get_connector('azure_monitor')
            if azure_conn and metrics:
                # For Azure, we need specific resource context
                azure_results = await azure_conn.query_metrics(
                    ','.join(metrics), 
                    timespan=1 if time_range == '1h' else 24
                )
                if azure_results:
                    all_results['azure_monitor'] = azure_results
            
            # Generate response
            all_metrics_data = []
            for connector_results in all_results.values():
                all_metrics_data.extend(connector_results)
            
            if not all_metrics_data:
                return self._no_data_response(parsed_query)
            
            # Use NLP to generate natural language response
            response = await self.nlp_processor.generate_response(
                parsed_query.get('original_query', ''),
                all_metrics_data,
                [],
                {'time_range': time_range, 'connectors': list(all_results.keys())}
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error handling metrics query: {e}")
            return f"I couldn't retrieve the metrics data. Error: {str(e)}"
    
    async def _handle_alerts_query(self, parsed_query: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Handle alerts queries"""
        try:
            all_alerts_results = await self.connector_manager.get_all_alerts()
            
            all_alerts = []
            for connector_alerts in all_alerts_results.values():
                all_alerts.extend(connector_alerts)
            
            if not all_alerts:
                return "Great news! No active alerts found in your monitoring systems."
            
            # Generate response
            response = await self.nlp_processor.generate_response(
                parsed_query.get('original_query', ''),
                [],
                all_alerts,
                {'connectors': list(all_alerts_results.keys())}
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error handling alerts query: {e}")
            return f"I couldn't retrieve the alerts information. Error: {str(e)}"
    
    async def _handle_health_query(self, parsed_query: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Handle health/status queries"""
        try:
            # Check connector health
            health_results = await self.connector_manager.health_check_all()
            
            # Get basic system metrics
            healthy_connectors = await self.connector_manager.get_healthy_connectors()
            
            # Try to get "up" metrics from healthy connectors
            system_status = []
            for connector in healthy_connectors:
                try:
                    if connector.name == 'prometheus':
                        up_metrics = await connector.query_metrics("up")
                        system_status.extend(up_metrics)
                except Exception:
                    continue
            
            # Build response
            connector_status = []
            for name, is_healthy in health_results.items():
                status = "✅ Online" if is_healthy else "❌ Offline"
                connector_status.append(f"{name.title()}: {status}")
            
            response_parts = [
                "🔍 **System Health Status**",
                "",
                "**Data Sources:**"
            ]
            response_parts.extend([f"- {status}" for status in connector_status])
            
            if system_status:
                up_services = len([m for m in system_status if m.value == 1.0])
                total_services = len(system_status)
                response_parts.extend([
                    "",
                    f"**Services Status:** {up_services}/{total_services} services are healthy"
                ])
            
            # Get recent alerts for context
            try:
                all_alerts = await self.connector_manager.get_all_alerts()
                total_alerts = sum(len(alerts) for alerts in all_alerts.values())
                if total_alerts > 0:
                    response_parts.append(f"⚠️  {total_alerts} active alerts requiring attention")
                else:
                    response_parts.append("✅ No active alerts")
            except Exception:
                pass
            
            return "\n".join(response_parts)
            
        except Exception as e:
            logger.error(f"Error handling health query: {e}")
            return f"I couldn't retrieve the health information. Error: {str(e)}"
    
    async def _handle_services_query(self, parsed_query: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Handle services/applications queries"""
        try:
            all_services = await self.connector_manager.get_all_services()
            
            if not any(all_services.values()):
                return "No services found in the monitoring systems. Please check your configuration."
            
            response_parts = ["📋 **Available Services:**", ""]
            
            for connector_name, services in all_services.items():
                if services:
                    response_parts.append(f"**{connector_name.title()} ({len(services)} services):**")
                    # Show first 10 services to avoid overwhelming response
                    for service in services[:10]:
                        response_parts.append(f"- {service}")
                    if len(services) > 10:
                        response_parts.append(f"... and {len(services) - 10} more")
                    response_parts.append("")
            
            total_services = sum(len(services) for services in all_services.values())
            response_parts.append(f"**Total:** {total_services} services across {len([c for c, s in all_services.items() if s])} data sources")
            
            return "\n".join(response_parts)
            
        except Exception as e:
            logger.error(f"Error handling services query: {e}")
            return f"I couldn't retrieve the services information. Error: {str(e)}"
    
    def _no_data_response(self, parsed_query: Dict[str, Any]) -> str:
        """Generate response when no data is found"""
        query = parsed_query.get('original_query', '')
        services = parsed_query.get('services', [])
        metrics = parsed_query.get('metrics', [])
        
        suggestions = []
        if services:
            suggestions.append(f"Check if the service '{', '.join(services)}' is running")
        if metrics:
            suggestions.append(f"Verify that metrics '{', '.join(metrics)}' are being collected")
        
        base_response = f"No data found for your query: '{query}'"
        
        if suggestions:
            return f"{base_response}\n\nSuggestions:\n" + "\n".join(f"- {s}" for s in suggestions)
        else:
            return f"{base_response}\n\nTry asking about available services or check system health."
    
    async def _store_message(self, session_id: str, message: ChatMessage):
        """Store message in conversation history"""
        try:
            key = f"conversation:{session_id}"
            message_data = {
                'content': message.content,
                'sender': message.sender,
                'timestamp': message.timestamp.isoformat(),
                'metadata': message.metadata or {}
            }
            
            # Store as list item with expiration
            await self.redis.lpush(key, json.dumps(message_data))
            await self.redis.ltrim(key, 0, self.max_conversation_length - 1)  # Keep last N messages
            await self.redis.expire(key, self.context_retention_hours * 3600)  # Set expiration
            
        except Exception as e:
            logger.error(f"Error storing message: {e}")
    
    async def _get_conversation_history(self, session_id: str, limit: int = 10) -> List[ChatMessage]:
        """Get recent conversation history"""
        try:
            key = f"conversation:{session_id}"
            messages_data = await self.redis.lrange(key, 0, limit - 1)
            
            messages = []
            for msg_data in messages_data:
                try:
                    msg_dict = json.loads(msg_data)
                    message = ChatMessage(
                        content=msg_dict['content'],
                        sender=msg_dict['sender'],
                        timestamp=datetime.fromisoformat(msg_dict['timestamp']),
                        metadata=msg_dict.get('metadata')
                    )
                    messages.append(message)
                except (json.JSONDecodeError, KeyError):
                    continue
            
            return list(reversed(messages))  # Return in chronological order
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []
    
    async def get_conversation_summary(self, session_id: str) -> ConversationSummary:
        """Get a summary of the conversation"""
        try:
            history = await self._get_conversation_history(session_id)
            
            return ConversationSummary(
                session_id=session_id,
                message_count=len(history),
                start_time=history[0].timestamp if history else datetime.now(),
                last_activity=history[-1].timestamp if history else datetime.now(),
                topics=self._extract_topics(history)
            )
            
        except Exception as e:
            logger.error(f"Error getting conversation summary: {e}")
            return ConversationSummary(
                session_id=session_id,
                message_count=0,
                start_time=datetime.now(),
                last_activity=datetime.now(),
                topics=[]
            )
    
    def _extract_topics(self, messages: List[ChatMessage]) -> List[str]:
        """Extract main topics from conversation"""
        topics = set()
        
        for message in messages:
            if message.sender == "user":
                content_lower = message.content.lower()
                
                # Look for common monitoring topics
                if any(word in content_lower for word in ['cpu', 'processor']):
                    topics.add('CPU Performance')
                if any(word in content_lower for word in ['memory', 'ram']):
                    topics.add('Memory Usage')
                if any(word in content_lower for word in ['disk', 'storage']):
                    topics.add('Disk I/O')
                if any(word in content_lower for word in ['network', 'bandwidth']):
                    topics.add('Network')
                if any(word in content_lower for word in ['alert', 'alarm']):
                    topics.add('Alerts')
                if any(word in content_lower for word in ['health', 'status']):
                    topics.add('System Health')
                if any(word in content_lower for word in ['service', 'app']):
                    topics.add('Services')
        
        return list(topics)