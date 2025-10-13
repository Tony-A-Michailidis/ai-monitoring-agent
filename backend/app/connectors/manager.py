import logging
from typing import Dict, List, Optional, Type
from .base import BaseConnector
from .prometheus import PrometheusConnector
from .azure_monitor import AzureMonitorConnector
from ..config import Settings

logger = logging.getLogger(__name__)

class ConnectorManager:
    """Manages all monitoring data connectors"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.connectors: Dict[str, BaseConnector] = {}
        self._initialize_connectors()
    
    def _initialize_connectors(self):
        """Initialize all configured connectors"""
        try:
            # Initialize Prometheus connector if configured
            if self.settings.prometheus_url:
                self.connectors["prometheus"] = PrometheusConnector(
                    base_url=self.settings.prometheus_url,
                    username=self.settings.prometheus_username,
                    password=self.settings.prometheus_password
                )
                logger.info("Prometheus connector initialized")
            
            # Initialize Azure Monitor connector if configured
            if all([
                self.settings.azure_subscription_id,
                self.settings.azure_client_id,
                self.settings.azure_client_secret,
                self.settings.azure_tenant_id
            ]):
                self.connectors["azure_monitor"] = AzureMonitorConnector(
                    subscription_id=self.settings.azure_subscription_id,
                    client_id=self.settings.azure_client_id,
                    client_secret=self.settings.azure_client_secret,
                    tenant_id=self.settings.azure_tenant_id
                )
                logger.info("Azure Monitor connector initialized")
            
            if not self.connectors:
                logger.warning("No monitoring connectors configured")
            else:
                logger.info(f"Initialized {len(self.connectors)} connector(s): {list(self.connectors.keys())}")
                
        except Exception as e:
            logger.error(f"Error initializing connectors: {e}")
    
    async def health_check_all(self) -> Dict[str, bool]:
        """Check health of all connectors"""
        results = {}
        
        for name, connector in self.connectors.items():
            try:
                results[name] = await connector.health_check()
                logger.debug(f"Health check for {name}: {results[name]}")
            except Exception as e:
                logger.error(f"Health check failed for {name}: {e}")
                results[name] = False
        
        return results
    
    async def get_healthy_connectors(self) -> List[BaseConnector]:
        """Get list of healthy connectors"""
        healthy = []
        
        for connector in self.connectors.values():
            try:
                if await connector.health_check():
                    healthy.append(connector)
            except Exception as e:
                logger.error(f"Error checking connector health: {e}")
        
        return healthy
    
    def get_connector(self, name: str) -> Optional[BaseConnector]:
        """Get a specific connector by name"""
        return self.connectors.get(name)
    
    def list_connectors(self) -> List[str]:
        """Get list of all connector names"""
        return list(self.connectors.keys())
    
    async def query_all_connectors(self, query: str, **kwargs) -> Dict[str, List]:
        """Query all healthy connectors"""
        results = {}
        healthy_connectors = await self.get_healthy_connectors()
        
        for connector in healthy_connectors:
            try:
                metrics = await connector.query_metrics(query, **kwargs)
                results[connector.name] = metrics
                logger.debug(f"Query '{query}' returned {len(metrics)} results from {connector.name}")
            except Exception as e:
                logger.error(f"Error querying {connector.name}: {e}")
                results[connector.name] = []
        
        return results
    
    async def get_all_alerts(self) -> Dict[str, List]:
        """Get alerts from all healthy connectors"""
        results = {}
        healthy_connectors = await self.get_healthy_connectors()
        
        for connector in healthy_connectors:
            try:
                alerts = await connector.get_active_alerts()
                results[connector.name] = alerts
                logger.debug(f"Got {len(alerts)} alerts from {connector.name}")
            except Exception as e:
                logger.error(f"Error getting alerts from {connector.name}: {e}")
                results[connector.name] = []
        
        return results
    
    async def get_all_services(self) -> Dict[str, List[str]]:
        """Get services from all healthy connectors"""
        results = {}
        healthy_connectors = await self.get_healthy_connectors()
        
        for connector in healthy_connectors:
            try:
                services = await connector.get_services()
                results[connector.name] = services
                logger.debug(f"Got {len(services)} services from {connector.name}")
            except Exception as e:
                logger.error(f"Error getting services from {connector.name}: {e}")
                results[connector.name] = []
        
        return results
    
    async def get_all_metrics_summary(self) -> Dict[str, Dict]:
        """Get metrics summary from all healthy connectors"""
        results = {}
        healthy_connectors = await self.get_healthy_connectors()
        
        for connector in healthy_connectors:
            try:
                summary = await connector.get_metrics_summary()
                results[connector.name] = summary
            except Exception as e:
                logger.error(f"Error getting metrics summary from {connector.name}: {e}")
                results[connector.name] = {
                    "connector": connector.name,
                    "error": str(e),
                    "services": [],
                    "metric_names": []
                }
        
        return results