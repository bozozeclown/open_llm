# core/analytics/dashboard.py
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pathlib import Path

class AnalyticsDashboard:
    def __init__(self, db_manager, redis_client):
        self.db_manager = db_manager
        self.redis_client = redis_client
        self.router = APIRouter(prefix="/analytics")
        self._setup_routes()
    
    def _setup_routes(self):
        @self.router.get("/dashboard", response_class=HTMLResponse)
        async def dashboard():
            """Main analytics dashboard"""
            return self._generate_dashboard_html()
        
        @self.router.get("/api/usage-stats")
        async def usage_stats():
            """Get usage statistics"""
            return await self._get_usage_statistics()
        
        @self.router.get("/api/performance-metrics")
        async def performance_metrics():
            """Get performance metrics"""
            return await self._get_performance_metrics()
        
        @self.router.get("/api/user-analytics")
        async def user_analytics():
            """Get user analytics"""
            return await self._get_user_analytics()
        
        @self.router.get("/api/code-quality-trends")
        async def code_quality_trends():
            """Get code quality trends"""
            return await self._get_code_quality_trends()
    
    def _generate_dashboard_html(self) -> str:
        """Generate dashboard HTML with embedded charts"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Open LLM Analytics Dashboard</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .dashboard-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }}
                .chart-container {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .full-width {{ grid-column: 1 / -1; }}
                .metric-card {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
                .metric-value {{ font-size: 24px; font-weight: bold; color: #007bff; }}
                .metric-label {{ color: #6c757d; }}
            </style>
        </head>
        <body>
            <h1>Open LLM Analytics Dashboard</h1>
            
            <div class="metric-cards">
                <div class="metric-card">
                    <div class="metric-label">Total Requests Today</div>
                    <div class="metric-value" id="total-requests">0</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Active Users</div>
                    <div class="metric-value" id="active-users">0</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Avg Response Time</div>
                    <div class="metric-value" id="avg-response-time">0ms</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Success Rate</div>
                    <div class="metric-value" id="success-rate">0%</div>
                </div>
            </div>
            
            <div class="dashboard-grid">
                <div class="chart-container">
                    <h3>Request Trends</h3>
                    <div id="request-trends-chart"></div>
                </div>
                
                <div class="chart-container">
                    <h3>Language Distribution</h3>
                    <div id="language-distribution-chart"></div>
                </div>
                
                <div class="chart-container">
                    <h3>Performance Metrics</h3>
                    <div id="performance-metrics-chart"></div>
                </div>
                
                <div class="chart-container">
                    <h3>User Activity</h3>
                    <div id="user-activity-chart"></div>
                </div>
            </div>
            
            <script>
                // Fetch data and render charts
                async function loadDashboardData() {{
                    try {{
                        // Load metrics
                        const metrics = await fetch('/analytics/api/usage-stats').then(r => r.json());
                        document.getElementById('total-requests').textContent = metrics.total_requests;
                        document.getElementById('active-users').textContent = metrics.active_users;
                        document.getElementById('avg-response-time').textContent = metrics.avg_response_time + 'ms';
                        document.getElementById('success-rate').textContent = metrics.success_rate + '%';
                        
                        // Load and render charts
                        await loadCharts();
                    }} catch (error) {{
                        console.error('Failed to load dashboard data:', error);
                    }}
                }}
                
                async function loadCharts() {{
                    // Request trends chart
                    const requestTrends = await fetch('/analytics/api/usage-stats').then(r => r.json());
                    const requestTrace = {{
                        x: requestTrends.hourly_requests.map(r => r.hour),
                        y: requestTrends.hourly_requests.map(r => r.count),
                        type: 'scatter',
                        mode: 'lines+markers',
                        name: 'Requests'
                    }};
                    
                    const requestLayout = {{
                        title: 'Request Trends (Last 24 Hours)',
                        xaxis: {{ title: 'Hour' }},
                        yaxis: {{ title: 'Requests' }}
                    }};
                    
                    Plotly.newPlot('request-trends-chart', [requestTrace], requestLayout);
                    
                    // Language distribution chart
                    const langData = await fetch('/analytics/api/code-quality-trends').then(r => r.json());
                    const langChart = {{
                        values: langData.language_distribution.map(d => d.count),
                        labels: langData.language_distribution.map(d => d.language),
                        type: 'pie'
                    }};
                    
                    const langLayout = {{
                        title: 'Language Distribution'
                    }};
                    
                    Plotly.newPlot('language-distribution-chart', [langChart], langLayout);
                    
                    // Performance metrics chart
                    const perfData = await fetch('/analytics/api/performance-metrics').then(r => r.json());
                    const perfTrace = {{
                        x: perfData.hourly_metrics.map(m => m.hour),
                        y: perfData.hourly_metrics.map(m => m.avg_latency),
                        type: 'bar',
                        name: 'Average Latency (ms)'
                    }};
                    
                    const perfLayout = {{
                        title: 'Performance Metrics',
                        xaxis: {{ title: 'Hour' }},
                        yaxis: {{ title: 'Latency (ms)' }}
                    }};
                    
                    Plotly.newPlot('performance-metrics-chart', [perfTrace], perfLayout);
                    
                    // User activity chart
                    const userData = await fetch('/analytics/api/user-analytics').then(r => r.json());
                    const userTrace = {{
                        x: userData.daily_activity.map(d => d.date),
                        y: userData.daily_activity.map(d => d.active_users),
                        type: 'scatter',
                        mode: 'lines+markers',
                        name: 'Active Users'
                    }};
                    
                    const userLayout = {{
                        title: 'User Activity (Last 30 Days)',
                        xaxis: {{ title: 'Date' }},
                        yaxis: {{ title: 'Active Users' }}
                    }};
                    
                    Plotly.newPlot('user-activity-chart', [userTrace], userLayout);
                }}
                
                // Load dashboard on page load
                loadDashboardData();
                
                // Refresh every 30 seconds
                setInterval(loadDashboardData, 30000);
            </script>
        </body>
        </html>
        """
    
    async def _get_usage_statistics(self) -> Dict[str, Any]:
        """Get usage statistics"""
        # Get data from cache or database
        cache_key = "usage_stats:today"
        cached_data = await self.redis_client.get(cache_key)
        
        if cached_data:
            return json.loads(cached_data)
        
        # Calculate statistics
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        
        async with self.db_manager.get_postgres_connection() as conn:
            # Total requests today
            total_requests = await conn.fetchval(
                "SELECT COUNT(*) FROM requests WHERE request_timestamp >= $1 AND request_timestamp < $2",
                today, tomorrow
            )
            
            # Hourly distribution
            hourly_requests = await conn.fetch(
                """
                SELECT 
                    EXTRACT(HOUR FROM request_timestamp) as hour,
                    COUNT(*) as count
                FROM requests 
                WHERE request_timestamp >= $1 AND request_timestamp < $2
                GROUP BY EXTRACT(HOUR FROM request_timestamp)
                ORDER BY hour
                """,
                today, tomorrow
            )
            
            # Active users today
            active_users = await conn.fetchval(
                "SELECT COUNT(DISTINCT user_id) FROM requests WHERE request_timestamp >= $1 AND request_timestamp < $2",
                today, tomorrow
            )
            
            # Average response time
            avg_response_time = await conn.fetchval(
                "SELECT AVG(EXTRACT(EPOCH FROM (response_timestamp - request_timestamp)) * 1000) FROM requests WHERE request_timestamp >= $1 AND request_timestamp < $2",
                today, tomorrow
            ) or 0
            
            # Success rate
            success_rate_result = await conn.fetch(
                """
                SELECT 
                    SUM(CASE WHEN status_code < 400 THEN 1 ELSE 0 END) as success,
                    COUNT(*) as total
                FROM requests 
                WHERE request_timestamp >= $1 AND request_timestamp < $2
                """,
                today, tomorrow
            )
            
            success_rate = (success_rate_result[0]['success'] / success_rate_result[0]['total'] * 100) if success_rate_result[0]['total'] > 0 else 0
        
        result = {
            "total_requests": total_requests,
            "active_users": active_users,
            "avg_response_time": round(avg_response_time, 2),
            "success_rate": round(success_rate, 2),
            "hourly_requests": [
                {"hour": int(row["hour"]), "count": row["count"]}
                for row in hourly_requests
            ]
        }
        
        # Cache for 5 minutes
        await self.redis_client.setex(cache_key, 300, json.dumps(result))
        
        return result
    
    async def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        cache_key = "performance_metrics:24h"
        cached_data = await self.redis_client.get(cache_key)
        
        if cached_data:
            return json.loads(cached_data)
        
        # Get last 24 hours of performance data
        start_time = datetime.now() - timedelta(hours=24)
        
        async with self.db_manager.get_postgres_connection() as conn:
            hourly_metrics = await conn.fetch(
                """
                SELECT 
                    EXTRACT(HOUR FROM request_timestamp) as hour,
                    AVG(EXTRACT(EPOCH FROM (response_timestamp - request_timestamp)) * 1000) as avg_latency,
                    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (response_timestamp - request_timestamp) * 1000)) as p95_latency,
                    COUNT(*) as request_count
                FROM requests 
                WHERE request_timestamp >= $1
                GROUP BY EXTRACT(HOUR FROM request_timestamp)
                ORDER BY hour
                """,
                start_time
            )
        
        result = {
            "hourly_metrics": [
                {
                    "hour": int(row["hour"]),
                    "avg_latency": round(row["avg_latency"], 2),
                    "p95_latency": round(row["p95_latency"], 2),
                    "request_count": row["request_count"]
                }
                for row in hourly_metrics
            ]
        }
        
        # Cache for 10 minutes
        await self.redis_client.setex(cache_key, 600, json.dumps(result))
        
        return result
    
    async def _get_user_analytics(self) -> Dict[str, Any]:
        """Get user analytics"""
        cache_key = "user_analytics:30d"
        cached_data = await self.redis_client.get(cache_key)
        
        if cached_data:
            return json.loads(cached_data)
        
        # Get last 30 days of user activity
        start_time = datetime.now() - timedelta(days=30)
        
        async with self.db_manager.get_postgres_connection() as conn:
            daily_activity = await conn.fetch(
                """
                SELECT 
                    DATE(request_timestamp) as date,
                    COUNT(DISTINCT user_id) as active_users,
                    COUNT(*) as total_requests
                FROM requests 
                WHERE request_timestamp >= $1
                GROUP BY DATE(request_timestamp)
                ORDER BY date
                """,
                start_time
            )
            
            # Top users by request count
            top_users = await conn.fetch(
                """
                SELECT 
                    user_id,
                    COUNT(*) as request_count,
                    AVG(EXTRACT(EPOCH FROM (response_timestamp - request_timestamp)) * 1000) as avg_response_time
                FROM requests 
                WHERE request_timestamp >= $1
                GROUP BY user_id
                ORDER BY request_count DESC
                LIMIT 10
                """,
                start_time
            )
        
        result = {
            "daily_activity": [
                {
                    "date": row["date"].isoformat(),
                    "active_users": row["active_users"],
                    "total_requests": row["total_requests"]
                }
                for row in daily_activity
            ],
            "top_users": [
                {
                    "user_id": row["user_id"],
                    "request_count": row["request_count"],
                    "avg_response_time": round(row["avg_response_time"], 2)
                }
                for row in top_users
            ]
        }
        
        # Cache for 1 hour
        await self.redis_client.setex(cache_key, 3600, json.dumps(result))
        
        return result
    
    async def _get_code_quality_trends(self) -> Dict[str, Any]:
        """Get code quality trends"""
        cache_key = "code_quality_trends:7d"
        cached_data = await self.redis_client.get(cache_key)
        
        if cached_data:
            return json.loads(cached_data)
        
        # Get last 7 days of code quality data
        start_time = datetime.now() - timedelta(days=7)
        
        async with self.db_manager.get_postgres_connection() as conn:
            # Language distribution
            language_distribution = await conn.fetch(
                """
                SELECT 
                    metadata->>'language' as language,
                    COUNT(*) as count
                FROM requests 
                WHERE request_timestamp >= $1
                AND metadata->>'language' IS NOT NULL
                GROUP BY metadata->>'language'
                ORDER BY count DESC
                """,
                start_time
            )
            
            # Refactoring trends
            refactoring_trends = await conn.fetch(
                """
                SELECT 
                    DATE(request_timestamp) as date,
                    COUNT(*) as refactoring_count
                FROM requests 
                WHERE request_timestamp >= $1
                AND endpoint = '/refactor/analyze'
                GROUP BY DATE(request_timestamp)
                ORDER BY date
                """,
                start_time
            )
            
            # Quality metrics
            quality_metrics = await conn.fetch(
                """
                SELECT 
                    DATE(request_timestamp) as date,
                    AVG(CAST(metadata->>'quality_score' AS FLOAT)) as avg_quality_score,
                    COUNT(CASE WHEN metadata->>'validation_passed' = 'true' THEN 1 END) * 100.0 / COUNT(*) as success_rate
                FROM requests 
                WHERE request_timestamp >= $1
                AND metadata->>'quality_score' IS NOT NULL
                GROUP BY DATE(request_timestamp)
                ORDER BY date
                """,
                start_time
            )
        
        result = {
            "language_distribution": [
                {"language": row["language"], "count": row["count"]}
                for row in language_distribution
            ],
            "refactoring_trends": [
                {
                    "date": row["date"].isoformat(),
                    "refactoring_count": row["refactoring_count"]
                }
                for row in refactoring_trends
            ],
            "quality_metrics": [
                {
                    "date": row["date"].isoformat(),
                    "avg_quality_score": round(row["avg_quality_score"], 2),
                    "success_rate": round(row["success_rate"], 2)
                }
                for row in quality_metrics
            ]
        }
        
        # Cache for 1 hour
        await self.redis_client.setex(cache_key, 3600, json.dumps(result))
        
        return result