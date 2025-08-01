from core.plugin import PluginBase, PluginMetadata
from typing import Dict, Any
from core.monitoring.service import Monitoring

class Plugin(PluginBase):
    def __init__(self, config: Dict[str, Any], monitor: Monitoring):
        super().__init__(config)
        self.monitor = monitor

    def get_metadata(self):
        return PluginMetadata(
            name="manager",
            version="0.2.0",
            description="Enhanced plugin management with monitoring",
            required_config={}
        )

    @self.monitor.track_request('plugin_manager')
    def execute(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Monitored plugin management"""
        try:
            if command["action"] == "list_plugins":
                return self._list_plugins()
            elif command["action"] == "plugin_status":
                return self._plugin_status(command["plugin"])
            else:
                return {"error": "Unknown action"}
        except Exception as e:
            self.monitor.REQUEST_COUNT.labels('manager', 'failed').inc()
            raise

    def _list_plugins(self) -> Dict[str, Any]:
        return {
            "plugins": list(self.context.plugin_manager.plugins.keys()),
            "stats": {
                "ready": sum(1 for p in self.context.plugin_manager.plugins.values() if p.is_ready()),
                "total": len(self.context.plugin_manager.plugins)
            }
        }

    def _plugin_status(self, plugin_name: str) -> Dict[str, Any]:
        plugin = self.context.plugin_manager.get_plugin(plugin_name)
        return {
            "exists": plugin is not None,
            "ready": plugin.is_ready() if plugin else False,
            "metadata": plugin.metadata if plugin else None
        }