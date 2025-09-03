"""
OneVice Database Monitoring and Logging

Production-ready monitoring, logging, and alerting system for 
the OneVice Neo4j database infrastructure.
"""

import os
import json
import time
import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from enum import Enum

from .neo4j_client import Neo4jClient
from .schema_manager import SchemaManager
from .connection_manager import ConnectionManager


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning" 
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(Enum):
    """Metric types for monitoring"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class Alert:
    """Alert data structure"""
    id: str
    severity: AlertSeverity
    component: str
    metric: str
    message: str
    value: Any
    threshold: Any
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class Metric:
    """Metric data structure"""
    name: str
    type: MetricType
    value: Any
    unit: str
    timestamp: datetime
    labels: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, Any]] = None


class DatabaseMetricsCollector:
    """Collects comprehensive database metrics"""
    
    def __init__(self, connection_manager: ConnectionManager):
        """Initialize metrics collector"""
        
        self.connection_manager = connection_manager
        self.logger = logging.getLogger(__name__)
        self._metrics_history: List[Metric] = []
        self._collection_intervals = {
            "connection_metrics": 30,   # 30 seconds
            "query_metrics": 60,        # 1 minute
            "schema_metrics": 300,      # 5 minutes
            "health_metrics": 120       # 2 minutes
        }
        
    async def collect_all_metrics(self) -> Dict[str, Any]:
        """Collect all database metrics"""
        
        self.logger.debug("Collecting database metrics...")
        start_time = time.time()
        
        try:
            # Collect metrics in parallel
            metric_tasks = [
                self._collect_connection_metrics(),
                self._collect_query_performance_metrics(),
                self._collect_schema_metrics(),
                self._collect_health_metrics()
            ]
            
            results = await asyncio.gather(*metric_tasks, return_exceptions=True)
            
            # Combine results
            all_metrics = []
            for result in results:
                if isinstance(result, list):
                    all_metrics.extend(result)
                elif isinstance(result, Exception):
                    self.logger.error(f"Metric collection failed: {result}")
            
            # Store metrics in history
            self._metrics_history.extend(all_metrics)
            
            # Keep only last 1000 metrics to prevent memory growth
            if len(self._metrics_history) > 1000:
                self._metrics_history = self._metrics_history[-1000:]
            
            collection_time = time.time() - start_time
            
            return {
                "metrics": [asdict(metric) for metric in all_metrics],
                "collection_time": collection_time,
                "total_metrics": len(all_metrics),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Metrics collection failed: {e}")
            return {
                "error": str(e),
                "collection_time": time.time() - start_time,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def _collect_connection_metrics(self) -> List[Metric]:
        """Collect Neo4j connection metrics"""
        
        metrics = []
        timestamp = datetime.now(timezone.utc)
        
        try:
            if self.connection_manager.neo4j:
                connection_status = self.connection_manager.neo4j.get_connection_status()
                
                # Connection state metric
                metrics.append(Metric(
                    name="neo4j_connection_state",
                    type=MetricType.GAUGE,
                    value=1 if connection_status["connected"] else 0,
                    unit="boolean",
                    timestamp=timestamp,
                    labels={"database": connection_status["database"]},
                    metadata={"state": connection_status["state"]}
                ))
                
                # Connection attempts metric
                metrics.append(Metric(
                    name="neo4j_connection_attempts",
                    type=MetricType.COUNTER,
                    value=connection_status["connection_attempts"],
                    unit="count",
                    timestamp=timestamp,
                    labels={"database": connection_status["database"]}
                ))
                
                # Performance metrics
                perf_metrics = connection_status["performance_metrics"]
                
                metrics.extend([
                    Metric(
                        name="neo4j_queries_executed",
                        type=MetricType.COUNTER,
                        value=perf_metrics["queries_executed"],
                        unit="count",
                        timestamp=timestamp,
                        labels={"database": connection_status["database"]}
                    ),
                    Metric(
                        name="neo4j_total_execution_time",
                        type=MetricType.COUNTER,
                        value=perf_metrics["total_execution_time"],
                        unit="seconds",
                        timestamp=timestamp,
                        labels={"database": connection_status["database"]}
                    ),
                    Metric(
                        name="neo4j_errors",
                        type=MetricType.COUNTER,
                        value=perf_metrics["errors"],
                        unit="count", 
                        timestamp=timestamp,
                        labels={"database": connection_status["database"]}
                    ),
                    Metric(
                        name="neo4j_reconnections",
                        type=MetricType.COUNTER,
                        value=perf_metrics["reconnections"],
                        unit="count",
                        timestamp=timestamp,
                        labels={"database": connection_status["database"]}
                    )
                ])
                
                # Average query time
                if perf_metrics["queries_executed"] > 0:
                    avg_query_time = perf_metrics["total_execution_time"] / perf_metrics["queries_executed"]
                    metrics.append(Metric(
                        name="neo4j_avg_query_time",
                        type=MetricType.GAUGE,
                        value=avg_query_time,
                        unit="seconds",
                        timestamp=timestamp,
                        labels={"database": connection_status["database"]}
                    ))
            
        except Exception as e:
            self.logger.error(f"Failed to collect connection metrics: {e}")
        
        return metrics
    
    async def _collect_query_performance_metrics(self) -> List[Metric]:
        """Collect query performance metrics"""
        
        metrics = []
        timestamp = datetime.now(timezone.utc)
        
        try:
            # Test query performance with different types of queries
            test_queries = [
                {
                    "name": "simple_query",
                    "query": "RETURN 1",
                    "category": "simple"
                },
                {
                    "name": "db_info_query", 
                    "query": "CALL db.info()",
                    "category": "system"
                },
                {
                    "name": "constraint_query",
                    "query": "SHOW CONSTRAINTS",
                    "category": "schema"
                }
            ]
            
            for test_query in test_queries:
                start_time = time.time()
                
                try:
                    result = await self.connection_manager.neo4j.execute_query(test_query["query"])
                    execution_time = time.time() - start_time
                    
                    metrics.append(Metric(
                        name="neo4j_query_execution_time",
                        type=MetricType.TIMER,
                        value=execution_time,
                        unit="seconds",
                        timestamp=timestamp,
                        labels={
                            "query_name": test_query["name"],
                            "query_category": test_query["category"],
                            "success": str(result.success)
                        },
                        metadata={
                            "records_returned": len(result.records) if result.success else 0,
                            "error": result.error if not result.success else None
                        }
                    ))
                    
                except Exception as query_error:
                    metrics.append(Metric(
                        name="neo4j_query_execution_time",
                        type=MetricType.TIMER,
                        value=time.time() - start_time,
                        unit="seconds",
                        timestamp=timestamp,
                        labels={
                            "query_name": test_query["name"],
                            "query_category": test_query["category"],
                            "success": "false"
                        },
                        metadata={"error": str(query_error)}
                    ))
        
        except Exception as e:
            self.logger.error(f"Failed to collect query performance metrics: {e}")
        
        return metrics
    
    async def _collect_schema_metrics(self) -> List[Metric]:
        """Collect schema validation metrics"""
        
        metrics = []
        timestamp = datetime.now(timezone.utc)
        
        try:
            if self.connection_manager.schema:
                validation_result = await self.connection_manager.schema.validate_schema()
                
                # Schema validity metric
                metrics.append(Metric(
                    name="neo4j_schema_valid",
                    type=MetricType.GAUGE,
                    value=1 if validation_result.valid else 0,
                    unit="boolean",
                    timestamp=timestamp,
                    metadata={
                        "missing_constraints": len(validation_result.missing_constraints),
                        "missing_indexes": len(validation_result.missing_indexes),
                        "missing_vector_indexes": len(validation_result.missing_vector_indexes),
                        "warnings": len(validation_result.warnings),
                        "errors": len(validation_result.errors)
                    }
                ))
                
                # Missing elements metrics
                metrics.extend([
                    Metric(
                        name="neo4j_missing_constraints",
                        type=MetricType.GAUGE,
                        value=len(validation_result.missing_constraints),
                        unit="count",
                        timestamp=timestamp
                    ),
                    Metric(
                        name="neo4j_missing_indexes", 
                        type=MetricType.GAUGE,
                        value=len(validation_result.missing_indexes),
                        unit="count",
                        timestamp=timestamp
                    ),
                    Metric(
                        name="neo4j_missing_vector_indexes",
                        type=MetricType.GAUGE,
                        value=len(validation_result.missing_vector_indexes),
                        unit="count",
                        timestamp=timestamp
                    )
                ])
            
        except Exception as e:
            self.logger.error(f"Failed to collect schema metrics: {e}")
        
        return metrics
    
    async def _collect_health_metrics(self) -> List[Metric]:
        """Collect overall health metrics"""
        
        metrics = []
        timestamp = datetime.now(timezone.utc)
        
        try:
            health_status = await self.connection_manager.health_check()
            
            # Overall health metric
            health_score = {
                "healthy": 1.0,
                "degraded": 0.5,
                "unhealthy": 0.0
            }.get(health_status["overall_status"], 0.0)
            
            metrics.append(Metric(
                name="neo4j_health_score",
                type=MetricType.GAUGE,
                value=health_score,
                unit="ratio",
                timestamp=timestamp,
                metadata={
                    "overall_status": health_status["overall_status"],
                    "components": list(health_status["components"].keys())
                }
            ))
            
            # Component-specific health metrics
            for component_name, component_health in health_status["components"].items():
                component_score = {
                    "healthy": 1.0,
                    "degraded": 0.5,
                    "unhealthy": 0.0,
                    "failed": 0.0
                }.get(component_health.get("status", "unhealthy"), 0.0)
                
                metrics.append(Metric(
                    name="neo4j_component_health",
                    type=MetricType.GAUGE,
                    value=component_score,
                    unit="ratio",
                    timestamp=timestamp,
                    labels={"component": component_name},
                    metadata=component_health
                ))
        
        except Exception as e:
            self.logger.error(f"Failed to collect health metrics: {e}")
        
        return metrics


class AlertManager:
    """Manages database alerts and notifications"""
    
    def __init__(self, metrics_collector: DatabaseMetricsCollector):
        """Initialize alert manager"""
        
        self.metrics_collector = metrics_collector
        self.logger = logging.getLogger(__name__)
        self.active_alerts: Dict[str, Alert] = {}
        
        # Alert thresholds
        self.thresholds = {
            "neo4j_avg_query_time": {"warning": 2.0, "critical": 5.0},
            "neo4j_connection_state": {"critical": 0},
            "neo4j_health_score": {"warning": 0.7, "critical": 0.3},
            "neo4j_schema_valid": {"critical": 0},
            "neo4j_missing_constraints": {"warning": 1, "critical": 3},
            "neo4j_missing_indexes": {"warning": 1, "critical": 3},
            "neo4j_missing_vector_indexes": {"warning": 1, "critical": 2}
        }
        
        # Alert callbacks
        self.alert_callbacks: List[Callable[[Alert], None]] = []
    
    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """Add callback function for alert notifications"""
        self.alert_callbacks.append(callback)
    
    async def evaluate_alerts(self, metrics: List[Metric]) -> List[Alert]:
        """Evaluate metrics against thresholds and generate alerts"""
        
        new_alerts = []
        current_time = datetime.now(timezone.utc)
        
        for metric in metrics:
            if metric.name in self.thresholds:
                threshold_config = self.thresholds[metric.name]
                alert_id = f"{metric.name}_{hash(str(metric.labels))}"
                
                # Check thresholds
                severity = None
                threshold_value = None
                
                if "critical" in threshold_config:
                    critical_threshold = threshold_config["critical"]
                    if self._check_threshold_breach(metric.value, critical_threshold):
                        severity = AlertSeverity.CRITICAL
                        threshold_value = critical_threshold
                
                elif "warning" in threshold_config:
                    warning_threshold = threshold_config["warning"] 
                    if self._check_threshold_breach(metric.value, warning_threshold):
                        severity = AlertSeverity.WARNING
                        threshold_value = warning_threshold
                
                # Create or resolve alert
                if severity:
                    if alert_id not in self.active_alerts:
                        # New alert
                        alert = Alert(
                            id=alert_id,
                            severity=severity,
                            component="neo4j",
                            metric=metric.name,
                            message=self._generate_alert_message(metric, severity, threshold_value),
                            value=metric.value,
                            threshold=threshold_value,
                            timestamp=current_time,
                            metadata={
                                "labels": metric.labels,
                                "metric_metadata": metric.metadata,
                                "unit": metric.unit
                            }
                        )
                        
                        self.active_alerts[alert_id] = alert
                        new_alerts.append(alert)
                        
                        # Notify callbacks
                        for callback in self.alert_callbacks:
                            try:
                                callback(alert)
                            except Exception as e:
                                self.logger.error(f"Alert callback failed: {e}")
                
                else:
                    # Resolve existing alert if present
                    if alert_id in self.active_alerts:
                        alert = self.active_alerts[alert_id]
                        alert.resolved = True
                        alert.resolved_at = current_time
                        
                        # Remove from active alerts
                        del self.active_alerts[alert_id]
                        
                        self.logger.info(f"Alert resolved: {alert.message}")
        
        return new_alerts
    
    def _check_threshold_breach(self, value: Any, threshold: Any) -> bool:
        """Check if metric value breaches threshold"""
        
        try:
            if isinstance(threshold, (int, float)) and isinstance(value, (int, float)):
                # For most metrics, breach occurs when value exceeds threshold
                # For boolean metrics (0/1), breach occurs when value equals threshold
                if threshold in [0, 1]:
                    return value == threshold
                else:
                    return value > threshold
            else:
                return False
        except Exception:
            return False
    
    def _generate_alert_message(self, metric: Metric, severity: AlertSeverity, threshold: Any) -> str:
        """Generate alert message"""
        
        if metric.name == "neo4j_connection_state" and metric.value == 0:
            return "Neo4j database connection is down"
        elif metric.name == "neo4j_avg_query_time":
            return f"Neo4j average query time ({metric.value:.2f}s) exceeds threshold ({threshold}s)"
        elif metric.name == "neo4j_health_score":
            return f"Neo4j health score ({metric.value:.2f}) below threshold ({threshold})"
        elif metric.name == "neo4j_schema_valid" and metric.value == 0:
            return "Neo4j database schema is invalid"
        elif metric.name.startswith("neo4j_missing_"):
            element_type = metric.name.replace("neo4j_missing_", "")
            return f"Neo4j database has {metric.value} missing {element_type}"
        else:
            return f"Neo4j metric {metric.name} ({metric.value}) breaches threshold ({threshold})"
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return list(self.active_alerts.values())


class DatabaseMonitor:
    """Main database monitoring coordinator"""
    
    def __init__(self, connection_manager: ConnectionManager):
        """Initialize database monitor"""
        
        self.connection_manager = connection_manager
        self.metrics_collector = DatabaseMetricsCollector(connection_manager)
        self.alert_manager = AlertManager(self.metrics_collector)
        self.logger = logging.getLogger(__name__)
        
        self._monitoring_active = False
        self._monitoring_task: Optional[asyncio.Task] = None
        
        # Setup logging for alerts
        self.alert_manager.add_alert_callback(self._log_alert)
    
    def _log_alert(self, alert: Alert):
        """Log alert to logging system"""
        
        log_level = {
            AlertSeverity.INFO: logging.INFO,
            AlertSeverity.WARNING: logging.WARNING,
            AlertSeverity.ERROR: logging.ERROR,
            AlertSeverity.CRITICAL: logging.CRITICAL
        }.get(alert.severity, logging.WARNING)
        
        self.logger.log(log_level, f"Database Alert [{alert.severity.value.upper()}]: {alert.message}")
    
    async def start_monitoring(self, interval: int = 60):
        """Start continuous monitoring"""
        
        if self._monitoring_active:
            self.logger.warning("Monitoring already active")
            return
        
        self.logger.info(f"Starting database monitoring with {interval}s interval")
        self._monitoring_active = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop(interval))
    
    async def stop_monitoring(self):
        """Stop continuous monitoring"""
        
        if not self._monitoring_active:
            return
        
        self.logger.info("Stopping database monitoring")
        self._monitoring_active = False
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            self._monitoring_task = None
    
    async def _monitoring_loop(self, interval: int):
        """Main monitoring loop"""
        
        while self._monitoring_active:
            try:
                # Collect metrics
                metric_results = await self.metrics_collector.collect_all_metrics()
                
                if "metrics" in metric_results:
                    # Convert dict metrics back to Metric objects for alert evaluation
                    metrics = []
                    for metric_dict in metric_results["metrics"]:
                        try:
                            metrics.append(Metric(
                                name=metric_dict["name"],
                                type=MetricType(metric_dict["type"]),
                                value=metric_dict["value"],
                                unit=metric_dict["unit"],
                                timestamp=datetime.fromisoformat(metric_dict["timestamp"]),
                                labels=metric_dict.get("labels"),
                                metadata=metric_dict.get("metadata")
                            ))
                        except Exception as e:
                            self.logger.error(f"Failed to reconstruct metric: {e}")
                    
                    # Evaluate alerts
                    await self.alert_manager.evaluate_alerts(metrics)
                
                # Wait for next interval
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(interval)
    
    async def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        
        # Get latest metrics
        metric_results = await self.metrics_collector.collect_all_metrics()
        
        # Get active alerts
        active_alerts = self.alert_manager.get_active_alerts()
        
        return {
            "monitoring_active": self._monitoring_active,
            "latest_metrics": metric_results,
            "active_alerts": [asdict(alert) for alert in active_alerts],
            "alert_count": len(active_alerts),
            "critical_alerts": len([a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]),
            "warning_alerts": len([a for a in active_alerts if a.severity == AlertSeverity.WARNING]),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def generate_monitoring_report(self, output_file: Optional[str] = None) -> Dict[str, Any]:
        """Generate comprehensive monitoring report"""
        
        self.logger.info("Generating monitoring report...")
        
        # Get monitoring status
        status = await self.get_monitoring_status()
        
        # Get connection manager health
        health_status = await self.connection_manager.health_check()
        
        report = {
            "report_generated_at": datetime.now(timezone.utc).isoformat(),
            "monitoring_status": status,
            "database_health": health_status,
            "alert_thresholds": self.alert_manager.thresholds,
            "summary": {
                "overall_health": health_status["overall_status"],
                "monitoring_active": self._monitoring_active,
                "total_alerts": len(status["active_alerts"]),
                "critical_alerts": status["critical_alerts"],
                "warning_alerts": status["warning_alerts"],
                "metrics_collected": status["latest_metrics"].get("total_metrics", 0)
            }
        }
        
        # Write to file if requested
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            self.logger.info(f"Monitoring report written to: {output_file}")
        
        return report


# Setup production logging configuration
def setup_production_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """Setup production-ready logging configuration"""
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    
    # Setup file handler if specified
    handlers = [console_handler]
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        handlers=handlers,
        force=True  # Override existing configuration
    )
    
    # Set specific logger levels
    logging.getLogger("neo4j").setLevel(logging.WARNING)  # Reduce driver noise
    logging.getLogger("urllib3").setLevel(logging.WARNING)  # Reduce HTTP noise


# Global monitor instance
_database_monitor: Optional[DatabaseMonitor] = None


async def get_database_monitor(connection_manager: ConnectionManager) -> DatabaseMonitor:
    """Get singleton database monitor instance"""
    global _database_monitor
    
    if _database_monitor is None:
        _database_monitor = DatabaseMonitor(connection_manager)
    
    return _database_monitor