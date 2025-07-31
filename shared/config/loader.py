# shared/config/loader.py
import watchdog.events
import yaml

class ConfigWatcher(watchdog.events.FileSystemEventHandler):
    def __init__(self, callback):
        self.callback = callback
        
    def on_modified(self, event):
        if event.src_path.endswith('.yaml'):
            self.callback(event.src_path)

# Enhanced ConfigManager
class ConfigManager:
    def __init__(self):
        self._callbacks = []
        self.load_configs()
        
    def register_callback(self, callback):
        self._callbacks.append(callback)
        
    def _notify_changes(self, changed_file):
        for callback in self._callbacks:
            callback(self, changed_file)
    
    def load_config():
    """Safe config reload that preserves existing connections"""
    new_config = yaml.safe_load(open("configs/integration.yaml"))
    for key in current_config:
        if key in new_config:
            current_config[key].update(new_config[key])