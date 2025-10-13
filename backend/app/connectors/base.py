from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from ..models import MetricData, AlertData

class BaseConnector(ABC):
    """Base class for all monitoring data connectors"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the connector is healthy and can connect to its data source"""
        pass
    
    @abstractmethod
    async def query_metrics(self, query: str, **kwargs) -> List[MetricData]:
        """Execute a metrics query and return structured data"""
        pass
    
    @abstractmethod
    async def get_active_alerts(self) -> List[AlertData]:
        """Get currently active alerts"""
        pass
    
    @abstractmethod
    async def get_services(self) -> List[str]:
        """Get list of available services/applications"""
        pass
    
    @abstractmethod
    async def get_metrics_list(self) -> List[str]:
        """Get list of available metrics"""
        pass
    
    async def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of available metrics and services"""
        try:
            services = await self.get_services()
            metrics = await self.get_metrics_list()
            
            return {
                "connector": self.name,
                "services": services[:50],  # Limit for performance
                "metric_names": metrics[:100],  # Limit for performance
                "service_count": len(services),
                "metric_count": len(metrics)
            }
        except Exception as e:
            return {
                "connector": self.name,
                "error": str(e),
                "services": [],
                "metric_names": []
            }