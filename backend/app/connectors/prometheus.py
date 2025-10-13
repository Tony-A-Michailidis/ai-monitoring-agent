import aiohttp
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, quote

from .base import BaseConnector
from ..models import MetricData, AlertData

logger = logging.getLogger(__name__)

class PrometheusConnector(BaseConnector):
    """Connector for Prometheus metrics API"""
    
    def __init__(self, base_url: str, username: Optional[str] = None, password: Optional[str] = None):
        super().__init__("prometheus")
        self.base_url = base_url.rstrip('/')
        self.auth = aiohttp.BasicAuth(username, password) if username and password else None
        
    async def health_check(self) -> bool:
        """Check Prometheus connectivity"""
        try:
            async with aiohttp.ClientSession(auth=self.auth) as session:
                url = f"{self.base_url}/api/v1/query"
                params = {"query": "up"}
                
                async with session.get(url, params=params, timeout=10) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Prometheus health check failed: {e}")
            return False
    
    async def query_metrics(self, query: str, **kwargs) -> List[MetricData]:
        """Execute a PromQL query"""
        try:
            async with aiohttp.ClientSession(auth=self.auth) as session:
                # Handle both instant and range queries
                time_range = kwargs.get('time_range', '1h')
                query_type = kwargs.get('query_type', 'instant')
                
                if query_type == 'range':
                    url = f"{self.base_url}/api/v1/query_range"
                    params = {
                        "query": query,
                        "start": (datetime.now() - timedelta(hours=1)).isoformat(),
                        "end": datetime.now().isoformat(),
                        "step": kwargs.get('step', '30s')
                    }
                else:
                    url = f"{self.base_url}/api/v1/query"
                    params = {"query": query}
                
                async with session.get(url, params=params, timeout=30) as response:
                    if response.status != 200:
                        logger.error(f"Prometheus query failed: {response.status}")
                        return []
                    
                    data = await response.json()
                    return self._parse_prometheus_response(data)
        
        except Exception as e:
            logger.error(f"Error querying Prometheus: {e}")
            return []
    
    async def get_active_alerts(self) -> List[AlertData]:
        """Get active alerts from Alertmanager"""
        try:
            # Try to get alerts from Alertmanager API
            alertmanager_url = self.base_url.replace(':9090', ':9093')  # Default Alertmanager port
            
            async with aiohttp.ClientSession(auth=self.auth) as session:
                url = f"{alertmanager_url}/api/v1/alerts"
                
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_alertmanager_response(data)
                    
            # Fallback: query alert rules from Prometheus
            alert_query = "ALERTS{alertstate=\"firing\"}"
            metrics = await self.query_metrics(alert_query)
            
            alerts = []
            for metric in metrics:
                alerts.append(AlertData(
                    name=metric.labels.get('alertname', 'Unknown'),
                    severity=metric.labels.get('severity', 'warning'),
                    description=metric.labels.get('description', ''),
                    service=metric.labels.get('service', metric.labels.get('job', 'unknown')),
                    timestamp=datetime.now(),
                    labels=metric.labels
                ))
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting alerts: {e}")
            return []
    
    async def get_services(self) -> List[str]:
        """Get list of services from Prometheus targets"""
        try:
            # Query for all job labels
            query = "group by (job) ({__name__=~\".+\"})"
            metrics = await self.query_metrics(query)
            
            services = set()
            for metric in metrics:
                job = metric.labels.get('job')
                if job:
                    services.add(job)
            
            return sorted(list(services))
            
        except Exception as e:
            logger.error(f"Error getting services: {e}")
            return []
    
    async def get_metrics_list(self) -> List[str]:
        """Get list of available metrics"""
        try:
            async with aiohttp.ClientSession(auth=self.auth) as session:
                url = f"{self.base_url}/api/v1/label/__name__/values"
                
                async with session.get(url, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('data', [])
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting metrics list: {e}")
            return []
    
    def _parse_prometheus_response(self, data: Dict[str, Any]) -> List[MetricData]:
        """Parse Prometheus API response into MetricData objects"""
        metrics = []
        
        if data.get('status') != 'success':
            logger.warning(f"Prometheus query failed: {data}")
            return metrics
        
        result = data.get('data', {}).get('result', [])
        
        for item in result:
            metric_name = item.get('metric', {}).get('__name__', 'unknown')
            labels = item.get('metric', {})
            
            # Handle both instant and range queries
            if 'value' in item:
                # Instant query
                timestamp, value = item['value']
                try:
                    metrics.append(MetricData(
                        name=metric_name,
                        value=float(value),
                        timestamp=datetime.fromtimestamp(timestamp),
                        labels=labels,
                        unit=self._infer_unit(metric_name)
                    ))
                except (ValueError, TypeError):
                    continue
            elif 'values' in item:
                # Range query
                for timestamp, value in item['values']:
                    try:
                        metrics.append(MetricData(
                            name=metric_name,
                            value=float(value),
                            timestamp=datetime.fromtimestamp(timestamp),
                            labels=labels,
                            unit=self._infer_unit(metric_name)
                        ))
                    except (ValueError, TypeError):
                        continue
        
        return metrics
    
    def _parse_alertmanager_response(self, data: Dict[str, Any]) -> List[AlertData]:
        """Parse Alertmanager API response into AlertData objects"""
        alerts = []
        
        for alert in data.get('data', []):
            if alert.get('status', {}).get('state') == 'active':
                labels = alert.get('labels', {})
                annotations = alert.get('annotations', {})
                
                alerts.append(AlertData(
                    name=labels.get('alertname', 'Unknown'),
                    severity=labels.get('severity', 'warning'),
                    description=annotations.get('description', annotations.get('summary', '')),
                    service=labels.get('service', labels.get('job', 'unknown')),
                    timestamp=datetime.fromisoformat(
                        alert.get('startsAt', datetime.now().isoformat()).replace('Z', '+00:00')
                    ),
                    labels=labels
                ))
        
        return alerts
    
    def _infer_unit(self, metric_name: str) -> str:
        """Infer the unit of measurement from metric name"""
        metric_lower = metric_name.lower()
        
        if any(x in metric_lower for x in ['bytes', 'size', 'memory']):
            return 'bytes'
        elif any(x in metric_lower for x in ['duration', 'time', 'latency']):
            return 'seconds'
        elif any(x in metric_lower for x in ['rate', 'rps', 'qps']):
            return 'per_second'
        elif any(x in metric_lower for x in ['percent', 'ratio']):
            return 'percent'
        elif any(x in metric_lower for x in ['count', 'total', 'num']):
            return 'count'
        else:
            return 'unknown'