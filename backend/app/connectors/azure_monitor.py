import aiohttp
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .base import BaseConnector
from ..models import MetricData, AlertData

logger = logging.getLogger(__name__)

class AzureMonitorConnector(BaseConnector):
    """Connector for Azure Monitor APIs"""
    
    def __init__(self, subscription_id: str, client_id: str, client_secret: str, tenant_id: str):
        super().__init__("azure_monitor")
        self.subscription_id = subscription_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.access_token = None
        self.token_expires = None
    
    async def health_check(self) -> bool:
        """Check Azure Monitor connectivity"""
        try:
            token = await self._get_access_token()
            if not token:
                return False
            
            # Test with a simple subscription call
            headers = {"Authorization": f"Bearer {token}"}
            url = f"https://management.azure.com/subscriptions/{self.subscription_id}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params={"api-version": "2020-01-01"}) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Azure Monitor health check failed: {e}")
            return False
    
    async def query_metrics(self, query: str, **kwargs) -> List[MetricData]:
        """Execute a KQL query or get metrics from Azure Monitor"""
        try:
            token = await self._get_access_token()
            if not token:
                return []
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Handle different query types
            resource_id = kwargs.get('resource_id')
            if resource_id:
                # Get specific resource metrics
                return await self._get_resource_metrics(resource_id, query, headers, **kwargs)
            elif query.startswith("Heartbeat") or "|" in query:
                # Log Analytics KQL query
                return await self._execute_kql_query(query, headers, **kwargs)
            else:
                # Try to find resources by type/name
                return await self._search_and_query_resources(query, headers, **kwargs)
                
        except Exception as e:
            logger.error(f"Error querying Azure Monitor: {e}")
            return []
    
    async def get_active_alerts(self) -> List[AlertData]:
        """Get active alerts from Azure Monitor"""
        try:
            token = await self._get_access_token()
            if not token:
                return []
            
            headers = {"Authorization": f"Bearer {token}"}
            
            # Get alerts from Alert Management API
            url = f"https://management.azure.com/subscriptions/{self.subscription_id}/providers/Microsoft.AlertsManagement/alerts"
            params = {
                "api-version": "2019-05-05-preview",
                "alertState": "New,Acknowledged"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_azure_alerts(data)
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting Azure alerts: {e}")
            return []
    
    async def get_services(self) -> List[str]:
        """Get list of Azure resources/services"""
        try:
            token = await self._get_access_token()
            if not token:
                return []
            
            headers = {"Authorization": f"Bearer {token}"}
            url = f"https://management.azure.com/subscriptions/{self.subscription_id}/resources"
            params = {"api-version": "2021-04-01"}
            
            services = set()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        for resource in data.get('value', []):
                            resource_type = resource.get('type', '')
                            name = resource.get('name', '')
                            if resource_type and name:
                                services.add(f"{resource_type.split('/')[-1]}: {name}")
            
            return sorted(list(services))[:50]  # Limit for performance
            
        except Exception as e:
            logger.error(f"Error getting Azure services: {e}")
            return []
    
    async def get_metrics_list(self) -> List[str]:
        """Get list of available metrics from common Azure services"""
        # Common Azure metrics - in a real implementation, you'd query the metric definitions API
        common_metrics = [
            "Percentage CPU",
            "Network In Total",
            "Network Out Total",
            "Disk Read Bytes",
            "Disk Write Bytes",
            "Available Memory Bytes",
            "Total Requests",
            "Response Time",
            "Failed Requests",
            "Successful Requests",
            "CPU Credits Consumed",
            "CPU Credits Remaining",
            "Data Disk IOPS Consumed Percentage",
            "OS Disk IOPS Consumed Percentage"
        ]
        return common_metrics
    
    async def _get_access_token(self) -> Optional[str]:
        """Get Azure access token using client credentials"""
        if self.access_token and self.token_expires and datetime.now() < self.token_expires:
            return self.access_token
        
        try:
            url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/token"
            data = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "resource": "https://management.azure.com/"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        token_data = await response.json()
                        self.access_token = token_data.get("access_token")
                        expires_in = token_data.get("expires_in", 3600)
                        self.token_expires = datetime.now() + timedelta(seconds=expires_in - 300)  # 5min buffer
                        return self.access_token
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting Azure access token: {e}")
            return None
    
    async def _get_resource_metrics(self, resource_id: str, metric_names: str, headers: Dict[str, str], **kwargs) -> List[MetricData]:
        """Get metrics for a specific Azure resource"""
        try:
            url = f"https://management.azure.com{resource_id}/providers/Microsoft.Insights/metrics"
            
            # Parse timespan
            timespan_hours = kwargs.get('timespan', 1)
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=timespan_hours)
            timespan = f"{start_time.isoformat()}Z/{end_time.isoformat()}Z"
            
            params = {
                "api-version": "2018-01-01",
                "metricnames": metric_names,
                "timespan": timespan,
                "interval": kwargs.get('interval', 'PT1M'),
                "aggregation": kwargs.get('aggregation', 'Average')
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_azure_metrics(data, resource_id)
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting resource metrics: {e}")
            return []
    
    async def _execute_kql_query(self, query: str, headers: Dict[str, str], **kwargs) -> List[MetricData]:
        """Execute a KQL query against Log Analytics"""
        try:
            workspace_id = kwargs.get('workspace_id')
            if not workspace_id:
                logger.warning("No workspace_id provided for KQL query")
                return []
            
            url = f"https://api.loganalytics.io/v1/workspaces/{workspace_id}/query"
            
            payload = {
                "query": query,
                "timespan": kwargs.get('timespan', 'P1D')  # Last day by default
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_kql_results(data)
            
            return []
            
        except Exception as e:
            logger.error(f"Error executing KQL query: {e}")
            return []
    
    async def _search_and_query_resources(self, search_term: str, headers: Dict[str, str], **kwargs) -> List[MetricData]:
        """Search for resources and query their metrics"""
        try:
            # This is a simplified version - would need more sophisticated resource discovery
            logger.info(f"Searching for resources matching: {search_term}")
            return []
            
        except Exception as e:
            logger.error(f"Error searching resources: {e}")
            return []
    
    def _parse_azure_metrics(self, data: Dict[str, Any], resource_id: str) -> List[MetricData]:
        """Parse Azure Monitor metrics response"""
        metrics = []
        
        for metric in data.get('value', []):
            metric_name = metric.get('name', {}).get('value', 'unknown')
            unit = metric.get('unit', 'count')
            
            for timeseries in metric.get('timeseries', []):
                labels = {}
                
                # Add metadata dimensions
                for dimension in timeseries.get('metadatavalues', []):
                    name = dimension.get('name', {}).get('value', '')
                    value = dimension.get('value', '')
                    if name and value:
                        labels[name] = value
                
                # Add resource info
                labels['resource_id'] = resource_id
                labels['resource_type'] = resource_id.split('/')[-2] if '/' in resource_id else 'unknown'
                
                # Parse data points
                for point in timeseries.get('data', []):
                    timestamp_str = point.get('timeStamp')
                    if timestamp_str:
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        
                        # Get the aggregated value (average, maximum, etc.)
                        value = point.get('average') or point.get('maximum') or point.get('minimum') or point.get('total')
                        
                        if value is not None:
                            metrics.append(MetricData(
                                name=metric_name,
                                value=float(value),
                                timestamp=timestamp,
                                labels=labels.copy(),
                                unit=self._convert_azure_unit(unit)
                            ))
        
        return metrics
    
    def _parse_kql_results(self, data: Dict[str, Any]) -> List[MetricData]:
        """Parse KQL query results"""
        metrics = []
        
        tables = data.get('tables', [])
        for table in tables:
            columns = table.get('columns', [])
            rows = table.get('rows', [])
            
            # Find time and value columns
            time_col = None
            value_col = None
            
            for i, col in enumerate(columns):
                col_name = col.get('name', '').lower()
                col_type = col.get('type', '')
                
                if col_type == 'datetime' and time_col is None:
                    time_col = i
                elif col_type in ['real', 'long', 'int'] and 'time' not in col_name:
                    value_col = i
            
            if time_col is not None and value_col is not None:
                for row in rows:
                    try:
                        timestamp = datetime.fromisoformat(row[time_col].replace('Z', '+00:00'))
                        value = float(row[value_col])
                        
                        # Create labels from other columns
                        labels = {}
                        for i, col in enumerate(columns):
                            if i not in [time_col, value_col] and i < len(row):
                                labels[col.get('name', f'col_{i}')] = str(row[i])
                        
                        metrics.append(MetricData(
                            name="kql_result",
                            value=value,
                            timestamp=timestamp,
                            labels=labels,
                            unit="count"
                        ))
                    except (ValueError, TypeError, IndexError):
                        continue
        
        return metrics
    
    def _parse_azure_alerts(self, data: Dict[str, Any]) -> List[AlertData]:
        """Parse Azure Monitor alerts response"""
        alerts = []
        
        for alert in data.get('value', []):
            properties = alert.get('properties', {})
            essentials = properties.get('essentials', {})
            
            alerts.append(AlertData(
                name=essentials.get('alertRule', 'Unknown'),
                severity=essentials.get('severity', 'Sev3').lower(),
                description=properties.get('context', {}).get('description', ''),
                service=essentials.get('targetResourceName', 'unknown'),
                timestamp=datetime.fromisoformat(
                    essentials.get('firedDateTime', datetime.now().isoformat()).replace('Z', '+00:00')
                ),
                labels=essentials
            ))
        
        return alerts
    
    def _convert_azure_unit(self, unit: str) -> str:
        """Convert Azure Monitor units to standard units"""
        unit_mapping = {
            'Percent': 'percent',
            'Count': 'count',
            'Bytes': 'bytes',
            'Seconds': 'seconds',
            'BytesPerSecond': 'bytes_per_second',
            'CountPerSecond': 'per_second',
            'Milliseconds': 'milliseconds'
        }
        return unit_mapping.get(unit, unit.lower())