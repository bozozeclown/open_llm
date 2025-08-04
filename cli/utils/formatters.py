# cli/utils/formatters.py
from typing import Dict, Any, List
from datetime import datetime
import json

class OutputFormatter:
    """Format CLI output in various formats."""
    
    @staticmethod
    def format_analysis_result(result: Dict[str, Any]) -> str:
        """Format code analysis results."""
        output = []
        
        if 'suggestions' in result:
            output.append("💡 Analysis Suggestions:")
            for i, suggestion in enumerate(result['suggestions'], 1):
                output.append(f"  {i}. {suggestion}")
        
        if 'metrics' in result:
            metrics = result['metrics']
            output.append("\n📊 Code Metrics:")
            output.append(f"  Complexity: {metrics.get('complexity', 'N/A')}")
            output.append(f"  Maintainability: {metrics.get('maintainability', 'N/A')}")
            output.append(f"  Security Score: {metrics.get('security_score', 'N/A')}")
        
        if 'issues' in result:
            issues = result['issues']
            if issues:
                output.append(f"\n⚠️  Issues Found ({len(issues)}):")
                for issue in issues[:5]:  # Show first 5 issues
                    output.append(f"  - {issue.get('description', 'Unknown issue')}")
        
        return '\n'.join(output)
    
    @staticmethod
    def format_session_info(session: Dict[str, Any]) -> str:
        """Format collaboration session information."""
        output = [
            f"📋 Session: {session.get('name', 'Unknown')}",
            f"🆔 ID: {session.get('id', 'Unknown')}",
            f"👥 Owner: {session.get('owner_id', 'Unknown')}",
            f"🔒 Public: {'Yes' if session.get('is_public', False) else 'No'}",
            f"📅 Created: {session.get('created_at', 'Unknown')}",
            f"👥 Collaborators: {len(session.get('collaborators', {}))}"
        ]
        
        if session.get('share_url'):
            output.append(f"🔗 Share URL: {session['share_url']}")
        
        return '\n'.join(output)
    
    @staticmethod
    def format_version_list(versions: List[Dict[str, Any]]) -> str:
        """Format knowledge graph version list."""
        if not versions:
            return "No versions found."
        
        output = ["📚 Knowledge Graph Versions:"]
        output.append("-" * 50)
        
        for version in versions:
            version_id = version.get('version_id', 'Unknown')[:8]
            description = version.get('description', 'No description')
            author = version.get('author', 'Unknown')
            timestamp = version.get('timestamp', 'Unknown')
            
            output.append(f"📋 {version_id}...")
            output.append(f"   📝 {description}")
            output.append(f"   👤 {author}")
            output.append(f"   📅 {timestamp}")
            
            if version.get('tags'):
                tags = ', '.join(version['tags'])
                output.append(f"   🏷️  {tags}")
            
            output.append()
        
        return '\n'.join(output)
    
    @staticmethod
    def format_error(message: str, details: str = None) -> str:
        """Format error messages."""
        output = [f"❌ {message}"]
        if details:
            output.append(f"   Details: {details}")
        return '\n'.join(output)
    
    @staticmethod
    def format_success(message: str, details: str = None) -> str:
        """Format success messages."""
        output = [f"✅ {message}"]
        if details:
            output.append(f"   {details}")
        return '\n'.join(output)
    
    @staticmethod
    def format_health_check(health_data: Dict[str, Any]) -> str:
        """Format health check results."""
        output = ["🏥 System Health Status:"]
        
        # Overall status
        status = health_data.get('status', 'unknown')
        status_icon = "🟢" if status == "healthy" else "🟡" if status == "degraded" else "🔴"
        output.append(f"{status_icon} Overall: {status.upper()}")
        
        # Components
        components = health_data.get('components', {})
        if components:
            output.append("\n📦 Components:")
            for component, comp_status in components.items():
                comp_icon = "🟢" if comp_status == "operational" else "🟡" if comp_status == "degraded" else "🔴"
                output.append(f"  {comp_icon} {component}: {comp_status}")
        
        return '\n'.join(output)
    
    @staticmethod
    def format_stats(stats: Dict[str, Any]) -> str:
        """Format usage statistics."""
        output = ["📊 Usage Statistics:"]
        
        # Basic stats
        output.append(f"📈 Total Requests: {stats.get('total_requests', 0)}")
        output.append(f"👥 Active Users: {stats.get('active_users', 0)}")
        output.append(f"⚡ Avg Response Time: {stats.get('avg_response_time', 0)}ms")
        output.append(f"✅ Success Rate: {stats.get('success_rate', 0)}%")
        
        # Hourly distribution
        hourly = stats.get('hourly_requests', [])
        if hourly:
            output.append("\n📅 Hourly Distribution:")
            for hour_data in hourly:
                output.append(f"  {hour_data['hour']:02d}:00 - {hour_data['count']} requests")
        
        return '\n'.join(output)