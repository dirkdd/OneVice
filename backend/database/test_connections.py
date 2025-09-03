#!/usr/bin/env python3
"""
OneVice Database Connection Testing Utility

Comprehensive testing utility to validate database connections,
schema integrity, and system health for the OneVice platform.

Usage:
    python test_connections.py [--config-file CONFIG] [--include-performance] [--verbose]

Features:
    - Connection validation for Neo4j
    - Schema integrity validation  
    - Performance benchmarking
    - Health monitoring
    - Comprehensive reporting
"""

import os
import sys
import json
import time
import asyncio
import argparse
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass, asdict

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from database.connection_manager import ConnectionManager, get_connection_manager
from database.neo4j_client import ConnectionConfig, Neo4jClient
from database.schema_manager import SchemaManager


@dataclass
class TestResult:
    """Test result data structure"""
    test_name: str
    success: bool
    execution_time: float
    message: str
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    metric_name: str
    value: float
    unit: str
    threshold: Optional[float] = None
    status: str = "unknown"  # pass, warning, fail


class DatabaseTester:
    """Comprehensive database testing utility"""
    
    def __init__(self, config: ConnectionConfig, verbose: bool = False):
        """Initialize database tester"""
        
        self.config = config
        self.verbose = verbose
        self.connection_manager: Optional[ConnectionManager] = None
        self.test_results: List[TestResult] = []
        self.performance_metrics: List[PerformanceMetric] = []
        
        # Setup logging
        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    async def run_all_tests(self, include_performance: bool = False) -> Dict[str, Any]:
        """Run comprehensive test suite"""
        
        self.logger.info("🧪 Starting OneVice database test suite...")
        start_time = time.time()
        
        try:
            # Basic connection tests
            await self._test_neo4j_connection()
            await self._test_connection_manager_initialization()
            
            # Schema tests
            await self._test_schema_validation()
            await self._test_schema_completeness()
            
            # Functional tests
            await self._test_basic_queries()
            await self._test_transaction_support()
            
            # Health monitoring tests
            await self._test_health_checks()
            
            # Performance tests (if requested)
            if include_performance:
                await self._run_performance_tests()
            
            # Generate comprehensive report
            total_time = time.time() - start_time
            return self._generate_test_report(total_time)
            
        except Exception as e:
            self.logger.error(f"Test suite failed with unexpected error: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time
            }
        
        finally:
            # Cleanup
            if self.connection_manager:
                await self.connection_manager.close()
    
    async def _test_neo4j_connection(self):
        """Test direct Neo4j connection"""
        
        self.logger.info("Testing Neo4j connection...")
        start_time = time.time()
        
        try:
            neo4j_client = Neo4jClient(self.config)
            connected = await neo4j_client.connect()
            
            execution_time = time.time() - start_time
            
            if connected:
                # Test basic query
                result = await neo4j_client.execute_query("RETURN 1 as test_value")
                
                if result.success and result.records:
                    self.test_results.append(TestResult(
                        test_name="neo4j_direct_connection",
                        success=True,
                        execution_time=execution_time,
                        message="Neo4j direct connection successful",
                        details={
                            "database": self.config.database,
                            "uri": self.config.uri,
                            "query_time": result.execution_time,
                            "test_value": result.records[0].get("test_value")
                        }
                    ))
                else:
                    self.test_results.append(TestResult(
                        test_name="neo4j_direct_connection",
                        success=False,
                        execution_time=execution_time,
                        message="Neo4j connection established but query failed",
                        error=result.error
                    ))
            else:
                self.test_results.append(TestResult(
                    test_name="neo4j_direct_connection", 
                    success=False,
                    execution_time=execution_time,
                    message="Failed to establish Neo4j connection",
                    error="Connection failed"
                ))
            
            await neo4j_client.disconnect()
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="neo4j_direct_connection",
                success=False,
                execution_time=execution_time,
                message="Neo4j connection test failed with exception",
                error=str(e)
            ))
    
    async def _test_connection_manager_initialization(self):
        """Test connection manager initialization"""
        
        self.logger.info("Testing connection manager initialization...")
        start_time = time.time()
        
        try:
            self.connection_manager = ConnectionManager(self.config)
            init_result = await self.connection_manager.initialize()
            
            execution_time = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name="connection_manager_init",
                success=init_result["success"],
                execution_time=execution_time,
                message="Connection manager initialization completed",
                details={
                    "neo4j_connected": init_result["neo4j_connected"],
                    "schema_valid": init_result["schema_valid"],
                    "initialization_time": init_result["initialization_time"],
                    "errors": init_result.get("errors", [])
                }
            ))
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="connection_manager_init",
                success=False,
                execution_time=execution_time,
                message="Connection manager initialization failed",
                error=str(e)
            ))
    
    async def _test_schema_validation(self):
        """Test schema validation functionality"""
        
        if not self.connection_manager or not self.connection_manager.is_initialized:
            self.test_results.append(TestResult(
                test_name="schema_validation",
                success=False,
                execution_time=0,
                message="Schema validation skipped - connection manager not available",
                error="Connection manager not initialized"
            ))
            return
        
        self.logger.info("Testing schema validation...")
        start_time = time.time()
        
        try:
            validation_result = await self.connection_manager.schema.validate_schema()
            execution_time = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name="schema_validation",
                success=True,  # Test succeeded even if schema is invalid
                execution_time=execution_time,
                message=f"Schema validation completed - Valid: {validation_result.valid}",
                details={
                    "schema_valid": validation_result.valid,
                    "missing_constraints": validation_result.missing_constraints,
                    "missing_indexes": validation_result.missing_indexes,
                    "missing_vector_indexes": validation_result.missing_vector_indexes,
                    "extra_constraints": validation_result.extra_constraints,
                    "extra_indexes": validation_result.extra_indexes,
                    "warnings": validation_result.warnings,
                    "errors": validation_result.errors
                }
            ))
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="schema_validation",
                success=False,
                execution_time=execution_time,
                message="Schema validation failed with exception",
                error=str(e)
            ))
    
    async def _test_schema_completeness(self):
        """Test schema completeness and creation if needed"""
        
        if not self.connection_manager or not self.connection_manager.is_initialized:
            self.test_results.append(TestResult(
                test_name="schema_completeness",
                success=False,
                execution_time=0,
                message="Schema completeness test skipped",
                error="Connection manager not initialized"
            ))
            return
        
        self.logger.info("Testing schema completeness...")
        start_time = time.time()
        
        try:
            schema_result = await self.connection_manager.ensure_schema()
            execution_time = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name="schema_completeness",
                success=schema_result["schema_complete"],
                execution_time=execution_time,
                message=f"Schema completeness check - Complete: {schema_result['schema_complete']}",
                details={
                    "schema_complete": schema_result["schema_complete"],
                    "creation_required": schema_result["creation_required"],
                    "creation_result": schema_result.get("creation_result"),
                    "validation_result": schema_result["validation_result"]
                }
            ))
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="schema_completeness",
                success=False,
                execution_time=execution_time,
                message="Schema completeness test failed",
                error=str(e)
            ))
    
    async def _test_basic_queries(self):
        """Test basic database query functionality"""
        
        if not self.connection_manager or not self.connection_manager.is_initialized:
            self.test_results.append(TestResult(
                test_name="basic_queries",
                success=False,
                execution_time=0,
                message="Basic queries test skipped",
                error="Connection manager not initialized"
            ))
            return
        
        self.logger.info("Testing basic query functionality...")
        start_time = time.time()
        
        test_queries = [
            {
                "name": "simple_return",
                "query": "RETURN 42 as answer, 'Hello' as greeting",
                "expected_fields": ["answer", "greeting"]
            },
            {
                "name": "database_info",
                "query": "CALL db.info()",
                "expected_fields": ["id", "name", "creationDate"]
            },
            {
                "name": "constraint_list",
                "query": "SHOW CONSTRAINTS",
                "expected_fields": ["name", "type"]
            },
            {
                "name": "index_list", 
                "query": "SHOW INDEXES",
                "expected_fields": ["name", "state", "type"]
            }
        ]
        
        query_results = []
        all_passed = True
        
        try:
            for test_query in test_queries:
                query_start = time.time()
                result = await self.connection_manager.neo4j.execute_query(test_query["query"])
                query_time = time.time() - query_start
                
                if result.success:
                    # Verify expected fields are present
                    if result.records and test_query["expected_fields"]:
                        first_record = result.records[0]
                        missing_fields = [
                            field for field in test_query["expected_fields"] 
                            if field not in first_record
                        ]
                        
                        query_results.append({
                            "name": test_query["name"],
                            "success": len(missing_fields) == 0,
                            "execution_time": query_time,
                            "records_count": len(result.records),
                            "missing_fields": missing_fields
                        })
                        
                        if missing_fields:
                            all_passed = False
                    else:
                        query_results.append({
                            "name": test_query["name"],
                            "success": True,
                            "execution_time": query_time,
                            "records_count": len(result.records)
                        })
                else:
                    query_results.append({
                        "name": test_query["name"],
                        "success": False,
                        "execution_time": query_time,
                        "error": result.error
                    })
                    all_passed = False
            
            execution_time = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name="basic_queries",
                success=all_passed,
                execution_time=execution_time,
                message=f"Basic queries test completed - {len([r for r in query_results if r['success']])}/{len(query_results)} passed",
                details={"query_results": query_results}
            ))
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="basic_queries",
                success=False,
                execution_time=execution_time,
                message="Basic queries test failed with exception",
                error=str(e)
            ))
    
    async def _test_transaction_support(self):
        """Test transaction functionality"""
        
        if not self.connection_manager or not self.connection_manager.is_initialized:
            self.test_results.append(TestResult(
                test_name="transaction_support",
                success=False,
                execution_time=0,
                message="Transaction support test skipped",
                error="Connection manager not initialized"
            ))
            return
        
        self.logger.info("Testing transaction support...")
        start_time = time.time()
        
        try:
            # Test successful transaction
            queries = [
                {"query": "CREATE (n:TestNode {id: $id, name: $name})", "parameters": {"id": "test1", "name": "Test Node 1"}},
                {"query": "CREATE (n:TestNode {id: $id, name: $name})", "parameters": {"id": "test2", "name": "Test Node 2"}},
                {"query": "MATCH (n:TestNode) RETURN count(n) as count", "parameters": {}}
            ]
            
            transaction_result = await self.connection_manager.neo4j.execute_queries_in_transaction(queries)
            
            # Cleanup test nodes
            await self.connection_manager.neo4j.execute_query("MATCH (n:TestNode) DELETE n")
            
            execution_time = time.time() - start_time
            
            all_successful = all(result.success for result in transaction_result)
            
            self.test_results.append(TestResult(
                test_name="transaction_support",
                success=all_successful,
                execution_time=execution_time,
                message=f"Transaction support test completed - Success: {all_successful}",
                details={
                    "queries_executed": len(queries),
                    "successful_queries": sum(1 for result in transaction_result if result.success),
                    "transaction_results": [
                        {
                            "query": result.query[:50] + "..." if len(result.query) > 50 else result.query,
                            "success": result.success,
                            "execution_time": result.execution_time,
                            "records_count": len(result.records),
                            "error": result.error
                        }
                        for result in transaction_result
                    ]
                }
            ))
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="transaction_support",
                success=False,
                execution_time=execution_time,
                message="Transaction support test failed",
                error=str(e)
            ))
    
    async def _test_health_checks(self):
        """Test health monitoring functionality"""
        
        if not self.connection_manager:
            self.test_results.append(TestResult(
                test_name="health_checks",
                success=False,
                execution_time=0,
                message="Health checks test skipped",
                error="Connection manager not available"
            ))
            return
        
        self.logger.info("Testing health monitoring...")
        start_time = time.time()
        
        try:
            # Test connection manager health check
            health_status = await self.connection_manager.health_check()
            
            # Test Neo4j client health check
            neo4j_health = await self.connection_manager.neo4j.health_check()
            
            execution_time = time.time() - start_time
            
            overall_healthy = (
                health_status["overall_status"] in ["healthy", "degraded"] and
                neo4j_health["status"] == "healthy"
            )
            
            self.test_results.append(TestResult(
                test_name="health_checks",
                success=overall_healthy,
                execution_time=execution_time,
                message=f"Health checks completed - Overall: {health_status['overall_status']}, Neo4j: {neo4j_health['status']}",
                details={
                    "connection_manager_health": health_status,
                    "neo4j_health": neo4j_health
                }
            ))
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="health_checks",
                success=False,
                execution_time=execution_time,
                message="Health checks test failed",
                error=str(e)
            ))
    
    async def _run_performance_tests(self):
        """Run performance benchmarking tests"""
        
        if not self.connection_manager or not self.connection_manager.is_initialized:
            return
        
        self.logger.info("Running performance tests...")
        
        # Connection performance test
        await self._test_connection_performance()
        
        # Query performance test
        await self._test_query_performance()
        
        # Concurrent connection test
        await self._test_concurrent_performance()
    
    async def _test_connection_performance(self):
        """Test connection establishment performance"""
        
        connection_times = []
        
        for i in range(5):  # Test 5 connections
            start_time = time.time()
            
            try:
                client = Neo4jClient(self.config)
                connected = await client.connect()
                
                if connected:
                    await client.disconnect()
                    connection_time = time.time() - start_time
                    connection_times.append(connection_time)
                
            except Exception:
                pass  # Skip failed connections for performance metrics
        
        if connection_times:
            avg_connection_time = sum(connection_times) / len(connection_times)
            max_connection_time = max(connection_times)
            
            self.performance_metrics.extend([
                PerformanceMetric(
                    metric_name="avg_connection_time",
                    value=avg_connection_time,
                    unit="seconds",
                    threshold=2.0,
                    status="pass" if avg_connection_time < 2.0 else "warning"
                ),
                PerformanceMetric(
                    metric_name="max_connection_time", 
                    value=max_connection_time,
                    unit="seconds",
                    threshold=5.0,
                    status="pass" if max_connection_time < 5.0 else "fail"
                )
            ])
    
    async def _test_query_performance(self):
        """Test query execution performance"""
        
        test_queries = [
            "RETURN 1",
            "CALL db.info()",
            "SHOW CONSTRAINTS",
            "SHOW INDEXES"
        ]
        
        query_times = []
        
        for query in test_queries:
            start_time = time.time()
            
            try:
                result = await self.connection_manager.neo4j.execute_query(query)
                
                if result.success:
                    query_time = time.time() - start_time
                    query_times.append(query_time)
                    
            except Exception:
                pass  # Skip failed queries
        
        if query_times:
            avg_query_time = sum(query_times) / len(query_times)
            max_query_time = max(query_times)
            
            self.performance_metrics.extend([
                PerformanceMetric(
                    metric_name="avg_query_time",
                    value=avg_query_time,
                    unit="seconds",
                    threshold=1.0,
                    status="pass" if avg_query_time < 1.0 else "warning"
                ),
                PerformanceMetric(
                    metric_name="max_query_time",
                    value=max_query_time,
                    unit="seconds", 
                    threshold=5.0,
                    status="pass" if max_query_time < 5.0 else "fail"
                )
            ])
    
    async def _test_concurrent_performance(self):
        """Test concurrent connection performance"""
        
        async def single_query():
            try:
                result = await self.connection_manager.neo4j.execute_query("RETURN rand() as random_value")
                return result.success
            except Exception:
                return False
        
        start_time = time.time()
        
        # Run 10 concurrent queries
        tasks = [single_query() for _ in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        execution_time = time.time() - start_time
        successful_queries = sum(1 for result in results if result is True)
        
        self.performance_metrics.extend([
            PerformanceMetric(
                metric_name="concurrent_query_time",
                value=execution_time,
                unit="seconds",
                threshold=10.0,
                status="pass" if execution_time < 10.0 else "fail"
            ),
            PerformanceMetric(
                metric_name="concurrent_success_rate",
                value=successful_queries / len(tasks),
                unit="ratio",
                threshold=0.9,
                status="pass" if (successful_queries / len(tasks)) >= 0.9 else "fail"
            )
        ])
    
    def _generate_test_report(self, total_execution_time: float) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        
        successful_tests = [test for test in self.test_results if test.success]
        failed_tests = [test for test in self.test_results if not test.success]
        
        # Performance metrics summary
        performance_summary = {}
        if self.performance_metrics:
            performance_summary = {
                "total_metrics": len(self.performance_metrics),
                "passed_metrics": len([m for m in self.performance_metrics if m.status == "pass"]),
                "warning_metrics": len([m for m in self.performance_metrics if m.status == "warning"]),
                "failed_metrics": len([m for m in self.performance_metrics if m.status == "fail"]),
                "metrics": [asdict(metric) for metric in self.performance_metrics]
            }
        
        report = {
            "test_summary": {
                "total_tests": len(self.test_results),
                "successful_tests": len(successful_tests),
                "failed_tests": len(failed_tests),
                "success_rate": len(successful_tests) / len(self.test_results) if self.test_results else 0,
                "total_execution_time": total_execution_time
            },
            "test_results": [asdict(test) for test in self.test_results],
            "performance_metrics": performance_summary,
            "database_config": {
                "uri": self.config.uri,
                "database": self.config.database,
                "username": self.config.username,
                "encrypted": self.config.encrypted,
                "max_connection_pool_size": self.config.max_connection_pool_size,
                "connection_timeout": self.config.connection_timeout
            },
            "overall_status": "PASS" if len(failed_tests) == 0 else "FAIL",
            "recommendations": self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        
        recommendations = []
        
        # Check for failed tests
        failed_tests = [test for test in self.test_results if not test.success]
        if failed_tests:
            recommendations.append(f"Address {len(failed_tests)} failed tests before production deployment")
        
        # Check performance metrics
        if self.performance_metrics:
            failed_metrics = [m for m in self.performance_metrics if m.status == "fail"]
            if failed_metrics:
                recommendations.append("Investigate performance issues with database connections or queries")
            
            warning_metrics = [m for m in self.performance_metrics if m.status == "warning"]
            if warning_metrics:
                recommendations.append("Consider optimizing database configuration for better performance")
        
        # Schema-specific recommendations
        schema_test = next((test for test in self.test_results if test.test_name == "schema_completeness"), None)
        if schema_test and schema_test.details:
            if not schema_test.details.get("schema_complete", True):
                recommendations.append("Run schema creation to ensure database is production-ready")
        
        return recommendations


def load_config_from_env() -> ConnectionConfig:
    """Load database configuration from environment variables"""
    
    return ConnectionConfig(
        uri=os.getenv("NEO4J_URI", "neo4j://localhost:7687"),
        username=os.getenv("NEO4J_USERNAME", "neo4j"),
        password=os.getenv("NEO4J_PASSWORD", "password"),
        database=os.getenv("NEO4J_DATABASE", "neo4j"),
        max_connection_lifetime=int(os.getenv("NEO4J_MAX_CONNECTION_LIFETIME", "3600")),
        max_connection_pool_size=int(os.getenv("NEO4J_MAX_CONNECTION_POOL_SIZE", "100")),
        connection_timeout=int(os.getenv("NEO4J_CONNECTION_TIMEOUT", "30")),
        encrypted=os.getenv("NEO4J_ENCRYPTED", "true").lower() == "true"
    )


def load_config_from_file(config_file: str) -> ConnectionConfig:
    """Load database configuration from JSON file"""
    
    with open(config_file, 'r') as f:
        config_data = json.load(f)
    
    return ConnectionConfig(
        uri=config_data.get("uri", "neo4j://localhost:7687"),
        username=config_data.get("username", "neo4j"),
        password=config_data.get("password", "password"),
        database=config_data.get("database", "neo4j"),
        max_connection_lifetime=config_data.get("max_connection_lifetime", 3600),
        max_connection_pool_size=config_data.get("max_connection_pool_size", 100),
        connection_timeout=config_data.get("connection_timeout", 30),
        encrypted=config_data.get("encrypted", True)
    )


async def main():
    """Main testing function"""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="OneVice Database Connection Testing")
    parser.add_argument("--config-file", type=str, help="Path to JSON configuration file")
    parser.add_argument("--include-performance", action="store_true", help="Include performance benchmarking")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--output-file", type=str, help="Save test report to JSON file")
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        if args.config_file:
            config = load_config_from_file(args.config_file)
        else:
            config = load_config_from_env()
        
        # Initialize tester
        tester = DatabaseTester(config, args.verbose)
        
        # Run tests
        report = await tester.run_all_tests(args.include_performance)
        
        # Display results
        print("\n" + "="*80)
        print("OneVice Database Test Results")
        print("="*80)
        print(f"Overall Status: {report['overall_status']}")
        print(f"Total Tests: {report['test_summary']['total_tests']}")
        print(f"Successful: {report['test_summary']['successful_tests']}")
        print(f"Failed: {report['test_summary']['failed_tests']}")
        print(f"Success Rate: {report['test_summary']['success_rate']:.1%}")
        print(f"Execution Time: {report['test_summary']['total_execution_time']:.2f}s")
        
        # Show failed tests
        if report['test_summary']['failed_tests'] > 0:
            print("\nFailed Tests:")
            for test in report['test_results']:
                if not test['success']:
                    print(f"  ❌ {test['test_name']}: {test['message']}")
                    if test.get('error'):
                        print(f"     Error: {test['error']}")
        
        # Show recommendations
        if report['recommendations']:
            print("\nRecommendations:")
            for rec in report['recommendations']:
                print(f"  • {rec}")
        
        # Save report if requested
        if args.output_file:
            with open(args.output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"\nDetailed report saved to: {args.output_file}")
        
        # Exit with appropriate code
        sys.exit(0 if report['overall_status'] == 'PASS' else 1)
        
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())