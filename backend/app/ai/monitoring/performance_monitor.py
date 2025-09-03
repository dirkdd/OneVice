"""
Performance Monitoring and Optimization

Real-time monitoring and optimization for the memory system
to ensure optimal performance and resource utilization.
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
import json

import redis.asyncio as redis
from redis.asyncio import Redis

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Performance metric data point"""
    name: str
    value: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PerformanceAlert:
    """Performance alert"""
    metric_name: str
    threshold: float
    current_value: float
    severity: str  # 'low', 'medium', 'high', 'critical'
    message: str
    timestamp: datetime

class PerformanceMonitor:
    """
    Real-time performance monitoring and optimization
    
    Features:
    - Real-time metric collection
    - Threshold-based alerting
    - Performance trend analysis
    - Automatic optimization recommendations
    - Resource usage tracking
    """
    
    def __init__(self, redis_client: Redis, config: Dict[str, Any]):
        self.redis_client = redis_client
        self.config = config
        
        # Monitoring state
        self.is_monitoring = False
        self.metrics_buffer: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.alert_handlers: List[Callable] = []
        
        # Performance thresholds
        self.thresholds = {
            'memory_search_latency': {'warning': 1.0, 'critical': 3.0},  # seconds
            'memory_extraction_latency': {'warning': 5.0, 'critical': 15.0},
            'background_queue_size': {'warning': 100, 'critical': 500},
            'neo4j_connection_time': {'warning': 2.0, 'critical': 5.0},
            'redis_latency': {'warning': 0.1, 'critical': 0.5},
            'memory_usage_mb': {'warning': 512, 'critical': 1024},
            'concurrent_operations': {'warning': 20, 'critical': 50},
            'error_rate': {'warning': 0.05, 'critical': 0.15}  # percentage
        }
        
        # Optimization strategies
        self.optimizations = {
            'cache_hit_rate': self._optimize_cache_strategy,
            'query_performance': self._optimize_query_patterns,
            'memory_consolidation': self._optimize_consolidation_frequency,
            'background_processing': self._optimize_background_processing
        }
        
        # Monitoring intervals
        self.collection_interval = 30  # seconds
        self.analysis_interval = 300  # seconds
        self.alert_cooldown = 600  # seconds
        
        # State tracking
        self.last_alerts: Dict[str, datetime] = {}
        self.performance_trends: Dict[str, List[float]] = defaultdict(list)
    
    async def start_monitoring(self):
        """Start performance monitoring"""
        if self.is_monitoring:
            logger.warning("Performance monitoring already active")
            return
        
        self.is_monitoring = True
        logger.info("Starting performance monitoring...")
        
        try:
            # Start monitoring tasks
            monitoring_tasks = [
                asyncio.create_task(self._collect_metrics_loop()),
                asyncio.create_task(self._analyze_performance_loop()),
                asyncio.create_task(self._cleanup_old_metrics_loop())
            ]
            
            await asyncio.gather(*monitoring_tasks)
            
        except Exception as e:
            logger.error(f"Performance monitoring error: {e}")
        finally:
            self.is_monitoring = False
            logger.info("Performance monitoring stopped")
    
    async def stop_monitoring(self):
        """Stop performance monitoring"""
        self.is_monitoring = False
        logger.info("Stopping performance monitoring...")
    
    def add_alert_handler(self, handler: Callable[[PerformanceAlert], None]):
        """Add alert handler"""
        self.alert_handlers.append(handler)
    
    async def record_metric(
        self,
        name: str,
        value: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Record a performance metric"""
        try:
            metric = PerformanceMetric(
                name=name,
                value=value,
                timestamp=datetime.utcnow(),
                metadata=metadata or {}
            )
            
            # Add to buffer
            self.metrics_buffer[name].append(metric)
            
            # Store in Redis for persistence
            metric_data = {
                'name': name,
                'value': value,
                'timestamp': metric.timestamp.isoformat(),
                'metadata': metadata or {}
            }
            
            await self.redis_client.lpush(
                f"performance:metrics:{name}",
                json.dumps(metric_data)
            )
            
            # Trim Redis list to prevent unbounded growth
            await self.redis_client.ltrim(f"performance:metrics:{name}", 0, 999)
            
            # Check thresholds
            await self._check_thresholds(metric)
            
        except Exception as e:
            logger.error(f"Failed to record metric {name}: {e}")
    
    async def time_operation(self, operation_name: str):
        """Context manager for timing operations"""
        return OperationTimer(self, operation_name)
    
    async def _collect_metrics_loop(self):
        """Main metrics collection loop"""
        while self.is_monitoring:
            try:
                await self._collect_system_metrics()
                await asyncio.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(self.collection_interval)
    
    async def _collect_system_metrics(self):
        """Collect system-level metrics"""
        try:
            # Redis performance
            start_time = time.time()
            await self.redis_client.ping()
            redis_latency = time.time() - start_time
            await self.record_metric('redis_latency', redis_latency)
            
            # Background queue size
            queue_size = await self.redis_client.zcard("memory:background_tasks")
            await self.record_metric('background_queue_size', queue_size)
            
            # Memory usage (simplified - would use psutil in production)
            # This is a placeholder - implement actual memory monitoring
            await self.record_metric('memory_usage_mb', 256)  # Placeholder
            
        except Exception as e:
            logger.error(f"System metrics collection failed: {e}")
    
    async def _analyze_performance_loop(self):
        """Performance analysis and optimization loop"""
        while self.is_monitoring:
            try:
                await self._analyze_trends()
                await self._suggest_optimizations()
                await asyncio.sleep(self.analysis_interval)
            except Exception as e:
                logger.error(f"Performance analysis error: {e}")
                await asyncio.sleep(self.analysis_interval)
    
    async def _analyze_trends(self):
        """Analyze performance trends"""
        try:
            for metric_name, metrics in self.metrics_buffer.items():
                if len(metrics) < 10:  # Need minimum data points
                    continue
                
                # Calculate trend
                recent_values = [m.value for m in list(metrics)[-10:]]
                trend = sum(recent_values) / len(recent_values)
                
                # Store trend
                self.performance_trends[metric_name].append(trend)
                if len(self.performance_trends[metric_name]) > 100:
                    self.performance_trends[metric_name] = self.performance_trends[metric_name][-100:]
                
        except Exception as e:
            logger.error(f"Trend analysis failed: {e}")
    
    async def _suggest_optimizations(self):
        """Suggest performance optimizations"""
        try:
            recommendations = []
            
            # Check cache hit rate
            if 'cache_hit_rate' in self.performance_trends:
                hit_rate = self.performance_trends['cache_hit_rate'][-1] if self.performance_trends['cache_hit_rate'] else 0
                if hit_rate < 0.7:  # Less than 70%
                    recommendations.append({
                        'type': 'caching',
                        'severity': 'medium',
                        'message': f'Cache hit rate is low ({hit_rate:.1%}). Consider increasing cache size or TTL.',
                        'action': 'optimize_cache_strategy'
                    })
            
            # Check query performance
            if 'memory_search_latency' in self.performance_trends:
                avg_latency = sum(self.performance_trends['memory_search_latency'][-10:]) / 10 if len(self.performance_trends['memory_search_latency']) >= 10 else 0
                if avg_latency > 0.5:
                    recommendations.append({
                        'type': 'query_optimization',
                        'severity': 'high',
                        'message': f'Average search latency is high ({avg_latency:.2f}s). Consider query optimization.',
                        'action': 'optimize_query_patterns'
                    })
            
            # Store recommendations
            if recommendations:
                await self.redis_client.setex(
                    "performance:recommendations",
                    3600,  # 1 hour TTL
                    json.dumps(recommendations)
                )
                
                logger.info(f"Generated {len(recommendations)} performance recommendations")
            
        except Exception as e:
            logger.error(f"Optimization suggestion failed: {e}")
    
    async def _check_thresholds(self, metric: PerformanceMetric):
        """Check if metric exceeds thresholds"""
        try:
            thresholds = self.thresholds.get(metric.name)
            if not thresholds:
                return
            
            # Determine severity
            severity = None
            if metric.value >= thresholds.get('critical', float('inf')):
                severity = 'critical'
            elif metric.value >= thresholds.get('warning', float('inf')):
                severity = 'warning'
            
            if not severity:
                return
            
            # Check alert cooldown
            last_alert = self.last_alerts.get(metric.name)
            if last_alert and (datetime.utcnow() - last_alert).total_seconds() < self.alert_cooldown:
                return
            
            # Create alert
            alert = PerformanceAlert(
                metric_name=metric.name,
                threshold=thresholds.get(severity, 0),
                current_value=metric.value,
                severity=severity,
                message=f"{metric.name} is {metric.value:.2f} (threshold: {thresholds[severity]})",
                timestamp=metric.timestamp
            )
            
            # Send alert
            await self._send_alert(alert)
            self.last_alerts[metric.name] = metric.timestamp
            
        except Exception as e:
            logger.error(f"Threshold check failed: {e}")
    
    async def _send_alert(self, alert: PerformanceAlert):
        """Send performance alert"""
        try:
            # Log alert
            logger.warning(f"Performance Alert [{alert.severity.upper()}]: {alert.message}")
            
            # Store alert in Redis
            alert_data = {
                'metric_name': alert.metric_name,
                'threshold': alert.threshold,
                'current_value': alert.current_value,
                'severity': alert.severity,
                'message': alert.message,
                'timestamp': alert.timestamp.isoformat()
            }
            
            await self.redis_client.lpush(
                "performance:alerts",
                json.dumps(alert_data)
            )
            await self.redis_client.ltrim("performance:alerts", 0, 99)  # Keep last 100 alerts
            
            # Call alert handlers
            for handler in self.alert_handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(alert)
                    else:
                        handler(alert)
                except Exception as e:
                    logger.error(f"Alert handler failed: {e}")
            
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
    
    async def _cleanup_old_metrics_loop(self):
        """Cleanup old metrics periodically"""
        while self.is_monitoring:
            try:
                await self._cleanup_old_metrics()
                await asyncio.sleep(3600)  # Run every hour
            except Exception as e:
                logger.error(f"Metrics cleanup error: {e}")
                await asyncio.sleep(3600)
    
    async def _cleanup_old_metrics(self):
        """Clean up old metrics from memory and Redis"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            # Clean memory buffers
            for metric_name, metrics in self.metrics_buffer.items():
                # Remove old metrics
                while metrics and metrics[0].timestamp < cutoff_time:
                    metrics.popleft()
            
            logger.debug("Cleaned up old performance metrics")
            
        except Exception as e:
            logger.error(f"Metrics cleanup failed: {e}")
    
    # Optimization strategies
    async def _optimize_cache_strategy(self):
        """Optimize caching strategy"""
        try:
            # Implementation would analyze cache patterns and adjust settings
            logger.info("Analyzing cache optimization opportunities...")
            
            # This would contain actual cache optimization logic
            recommendations = {
                'increase_cache_ttl': True,
                'expand_cache_size': True,
                'optimize_cache_keys': True
            }
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Cache optimization failed: {e}")
            return {}
    
    async def _optimize_query_patterns(self):
        """Optimize query patterns"""
        try:
            # Implementation would analyze query performance and suggest optimizations
            logger.info("Analyzing query optimization opportunities...")
            
            recommendations = {
                'add_indexes': ['memory_type', 'importance', 'user_id'],
                'optimize_vector_search': True,
                'batch_operations': True
            }
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Query optimization failed: {e}")
            return {}
    
    async def _optimize_consolidation_frequency(self):
        """Optimize memory consolidation frequency"""
        try:
            # Implementation would analyze consolidation patterns
            logger.info("Analyzing consolidation optimization opportunities...")
            
            recommendations = {
                'increase_frequency': False,
                'decrease_frequency': True,
                'optimize_batch_size': True
            }
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Consolidation optimization failed: {e}")
            return {}
    
    async def _optimize_background_processing(self):
        """Optimize background processing"""
        try:
            # Implementation would analyze background processing patterns
            logger.info("Analyzing background processing optimization opportunities...")
            
            recommendations = {
                'increase_workers': True,
                'optimize_batch_size': True,
                'adjust_priorities': True
            }
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Background processing optimization failed: {e}")
            return {}
    
    async def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        try:
            # Get recent alerts
            alerts_data = await self.redis_client.lrange("performance:alerts", 0, 9)  # Last 10 alerts
            alerts = [json.loads(alert) for alert in alerts_data]
            
            # Get recommendations
            recommendations_data = await self.redis_client.get("performance:recommendations")
            recommendations = json.loads(recommendations_data) if recommendations_data else []
            
            # Calculate summary statistics
            stats = {}
            for metric_name, metrics in self.metrics_buffer.items():
                if metrics:
                    values = [m.value for m in metrics]
                    stats[metric_name] = {
                        'avg': sum(values) / len(values),
                        'min': min(values),
                        'max': max(values),
                        'count': len(values),
                        'latest': values[-1] if values else 0
                    }
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'monitoring_status': 'active' if self.is_monitoring else 'inactive',
                'alerts': alerts,
                'recommendations': recommendations,
                'statistics': stats,
                'thresholds': self.thresholds
            }
            
        except Exception as e:
            logger.error(f"Failed to generate performance report: {e}")
            return {'error': str(e)}

class OperationTimer:
    """Context manager for timing operations"""
    
    def __init__(self, monitor: PerformanceMonitor, operation_name: str):
        self.monitor = monitor
        self.operation_name = operation_name
        self.start_time = None
    
    async def __aenter__(self):
        self.start_time = time.time()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            await self.monitor.record_metric(
                name=f"{self.operation_name}_latency",
                value=duration,
                metadata={
                    'operation': self.operation_name,
                    'success': exc_type is None
                }
            )