import openai
import json
import re
import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from ..config import Settings
from ..models import ChatMessage, MetricData, AlertData

logger = logging.getLogger(__name__)

class NLPProcessor:
    """Natural Language Processing for monitoring queries"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        openai.api_key = settings.openai_api_key
        
        # Query templates and patterns
        self.metric_patterns = {
            'cpu': ['cpu', 'processor', 'computation'],
            'memory': ['memory', 'ram', 'mem'],
            'disk': ['disk', 'storage', 'io', 'filesystem'],
            'network': ['network', 'net', 'bandwidth', 'traffic'],
            'latency': ['latency', 'response time', 'delay'],
            'throughput': ['throughput', 'requests per second', 'rps', 'qps'],
            'errors': ['error', 'failure', 'exception', 'fault']
        }
        
        self.time_patterns = {
            'minute': ['last minute', '1m', '60s'],
            'hour': ['last hour', '1h', 'hour ago'],
            'day': ['today', 'last day', '24h', 'day ago'],
            'week': ['this week', 'last week', '7d', 'week ago']
        }
        
        self.service_keywords = ['service', 'app', 'application', 'pod', 'container', 'instance']
    
    async def parse_user_query(self, query: str, available_services: List[str], available_metrics: List[str]) -> Dict[str, Any]:
        """Parse a natural language query into structured monitoring request"""
        try:
            # Use OpenAI to understand the intent
            intent = await self._analyze_intent_with_ai(query, available_services, available_metrics)
            
            # Extract components using patterns and AI results
            components = {
                'intent': intent.get('intent', 'unknown'),
                'metrics': intent.get('metrics', self._extract_metrics(query, available_metrics)),
                'services': intent.get('services', self._extract_services(query, available_services)),
                'time_range': intent.get('time_range', self._extract_time_range(query)),
                'aggregation': intent.get('aggregation', self._extract_aggregation(query)),
                'filters': intent.get('filters', {}),
                'query_type': intent.get('query_type', 'metrics'),
                'original_query': query
            }
            
            logger.info(f"Parsed query: {query} -> {components}")
            return components
            
        except Exception as e:
            logger.error(f"Error parsing query '{query}': {e}")
            return {
                'intent': 'unknown',
                'metrics': [],
                'services': [],
                'time_range': '1h',
                'aggregation': 'avg',
                'filters': {},
                'query_type': 'metrics',
                'original_query': query,
                'error': str(e)
            }
    
    async def generate_prometheus_query(self, components: Dict[str, Any]) -> Optional[str]:
        """Generate PromQL query from parsed components"""
        try:
            intent = components.get('intent', '')
            metrics = components.get('metrics', [])
            services = components.get('services', [])
            time_range = components.get('time_range', '5m')
            
            if not metrics and intent != 'alerts':
                return None
            
            # Handle different query types
            if intent == 'alerts':
                return "ALERTS{alertstate=\"firing\"}"
            elif intent == 'health' or 'health' in components.get('original_query', '').lower():
                return "up"
            elif intent == 'cpu' or any('cpu' in m.lower() for m in metrics):
                base_query = "cpu_usage_percent" if "cpu_usage_percent" in metrics else "rate(cpu_seconds_total[5m]) * 100"
            elif intent == 'memory' or any('memory' in m.lower() for m in metrics):
                base_query = "memory_usage_percent" if "memory_usage_percent" in metrics else "memory_working_set_bytes"
            elif intent == 'network' or any('network' in m.lower() for m in metrics):
                base_query = "rate(network_receive_bytes_total[5m])"
            else:
                # Use first available metric
                base_query = metrics[0] if metrics else "up"
            
            # Add service filters
            if services:
                service_filter = '|'.join(services)
                if '{' in base_query:
                    # Insert into existing braces
                    base_query = base_query.replace('{', f'{{job=~"{service_filter}",', 1)
                else:
                    # Add new braces
                    base_query = f"{base_query}{{job=~\"{service_filter}\"}}"
            
            # Add aggregation if needed
            aggregation = components.get('aggregation', 'avg')
            if aggregation and aggregation != 'raw':
                agg_func = {
                    'avg': 'avg',
                    'sum': 'sum',
                    'max': 'max',
                    'min': 'min'
                }.get(aggregation, 'avg')
                
                if services:
                    base_query = f"{agg_func} by (job) ({base_query})"
                else:
                    base_query = f"{agg_func}({base_query})"
            
            return base_query
            
        except Exception as e:
            logger.error(f"Error generating Prometheus query: {e}")
            return None
    
    async def generate_response(self, query: str, metrics: List[MetricData], alerts: List[AlertData], context: Dict[str, Any] = None) -> str:
        """Generate a natural language response based on query results"""
        try:
            # Prepare data summary
            data_summary = {
                'metrics_count': len(metrics),
                'alerts_count': len(alerts),
                'services': list(set([m.labels.get('job', 'unknown') for m in metrics if m.labels])),
                'metric_names': list(set([m.name for m in metrics])),
                'time_range': context.get('time_range', '1h') if context else '1h'
            }
            
            # Create sample data for context
            sample_metrics = metrics[:5] if metrics else []
            sample_alerts = alerts[:3] if alerts else []
            
            # Use AI to generate response
            prompt = self._build_response_prompt(query, data_summary, sample_metrics, sample_alerts)
            
            response = await openai.ChatCompletion.acreate(
                model=self.settings.openai_model,
                messages=[
                    {"role": "system", "content": "You are a monitoring assistant. Provide clear, concise responses about system metrics and alerts."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self._fallback_response(query, metrics, alerts)
    
    async def _analyze_intent_with_ai(self, query: str, services: List[str], metrics: List[str]) -> Dict[str, Any]:
        """Use OpenAI to analyze query intent"""
        try:
            prompt = f"""
            Analyze this monitoring query and extract structured information:
            
            Query: "{query}"
            
            Available services: {services[:20]}
            Available metrics: {metrics[:30]}
            
            Extract and return JSON with:
            - intent: main intent (cpu, memory, network, alerts, health, errors, performance)
            - metrics: list of relevant metric names from available metrics
            - services: list of relevant service names from available services
            - time_range: time period (5m, 1h, 24h, etc.)
            - aggregation: aggregation type (avg, sum, max, min, raw)
            - query_type: type of query (metrics, alerts, logs, health)
            - filters: any additional filters as key-value pairs
            
            Return only valid JSON.
            """
            
            response = await openai.ChatCompletion.acreate(
                model=self.settings.openai_model,
                messages=[
                    {"role": "system", "content": "You are a monitoring query analyzer. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.1
            )
            
            content = response.choices[0].message.content.strip()
            
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            return {}
            
        except Exception as e:
            logger.error(f"Error analyzing intent with AI: {e}")
            return {}
    
    def _extract_metrics(self, query: str, available_metrics: List[str]) -> List[str]:
        """Extract metric names from query using pattern matching"""
        query_lower = query.lower()
        matched_metrics = []
        
        # Direct matches with available metrics
        for metric in available_metrics:
            if metric.lower() in query_lower:
                matched_metrics.append(metric)
        
        # Pattern-based matching
        for category, patterns in self.metric_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                # Find metrics that match this category
                category_metrics = [m for m in available_metrics if category in m.lower()]
                matched_metrics.extend(category_metrics[:3])  # Limit to avoid too many
        
        return list(set(matched_metrics))
    
    def _extract_services(self, query: str, available_services: List[str]) -> List[str]:
        """Extract service names from query"""
        query_lower = query.lower()
        matched_services = []
        
        # Direct matches
        for service in available_services:
            service_lower = service.lower()
            if service_lower in query_lower:
                matched_services.append(service)
        
        # Extract quoted service names
        quoted_matches = re.findall(r'["\']([^"\']+)["\']', query)
        for match in quoted_matches:
            if match in available_services:
                matched_services.append(match)
        
        return list(set(matched_services))
    
    def _extract_time_range(self, query: str) -> str:
        """Extract time range from query"""
        query_lower = query.lower()
        
        # Look for explicit time patterns
        for time_range, patterns in self.time_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                return {'minute': '1m', 'hour': '1h', 'day': '24h', 'week': '7d'}[time_range]
        
        # Look for numeric patterns
        time_match = re.search(r'(\d+)\s*(m|h|d|s)', query_lower)
        if time_match:
            return f"{time_match.group(1)}{time_match.group(2)}"
        
        return '1h'  # Default
    
    def _extract_aggregation(self, query: str) -> str:
        """Extract aggregation function from query"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['average', 'avg', 'mean']):
            return 'avg'
        elif any(word in query_lower for word in ['sum', 'total']):
            return 'sum'
        elif any(word in query_lower for word in ['max', 'maximum', 'peak']):
            return 'max'
        elif any(word in query_lower for word in ['min', 'minimum', 'lowest']):
            return 'min'
        
        return 'avg'  # Default
    
    def _build_response_prompt(self, query: str, data_summary: Dict, sample_metrics: List[MetricData], sample_alerts: List[AlertData]) -> str:
        """Build prompt for response generation"""
        return f"""
        User asked: "{query}"
        
        Data summary:
        - Found {data_summary['metrics_count']} metrics
        - Found {data_summary['alerts_count']} alerts
        - Services: {', '.join(data_summary['services'][:5])}
        - Metrics: {', '.join(data_summary['metric_names'][:5])}
        - Time range: {data_summary['time_range']}
        
        Sample metrics (showing first few):
        {self._format_sample_metrics(sample_metrics)}
        
        Sample alerts (showing first few):
        {self._format_sample_alerts(sample_alerts)}
        
        Generate a helpful, conversational response that:
        1. Answers the user's question directly
        2. Highlights important findings or anomalies
        3. Suggests next steps if relevant
        4. Keeps technical details accessible
        
        Be concise but informative.
        """
    
    def _format_sample_metrics(self, metrics: List[MetricData]) -> str:
        """Format sample metrics for prompt"""
        if not metrics:
            return "No metrics found."
        
        formatted = []
        for metric in metrics[:3]:
            service = metric.labels.get('job', 'unknown') if metric.labels else 'unknown'
            formatted.append(f"- {metric.name}: {metric.value:.2f} {metric.unit} (service: {service})")
        
        return '\n'.join(formatted)
    
    def _format_sample_alerts(self, alerts: List[AlertData]) -> str:
        """Format sample alerts for prompt"""
        if not alerts:
            return "No active alerts."
        
        formatted = []
        for alert in alerts[:3]:
            formatted.append(f"- {alert.name} ({alert.severity}): {alert.description} (service: {alert.service})")
        
        return '\n'.join(formatted)
    
    def _fallback_response(self, query: str, metrics: List[MetricData], alerts: List[AlertData]) -> str:
        """Generate a fallback response when AI fails"""
        if alerts:
            return f"Found {len(alerts)} active alerts. The most critical ones need attention."
        elif metrics:
            return f"Retrieved {len(metrics)} metrics for your query. The data shows recent activity across your monitored services."
        else:
            return f"No data found for query '{query}'. Please check if the services are running and metrics are available."