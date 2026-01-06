import yaml
import logging

logger = logging.getLogger("Policy")

class PolicyManager:
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = {}
        self.reload()

    def reload(self):
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            logger.info("Policy loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load policy: {e}")
            self.config = {}

    def get_interface(self):
        return self.config.get('system', {}).get('interface', 'en0')

    def get_class_config(self, class_name):
        return self.config.get('classes', {}).get(class_name, {})

    def get_hog_threshold(self):
        return self.config.get('fairness', {}).get('hog_threshold_mbps', 5.0) * 1024 * 1024 / 8  # Convert mbps to bytes/sec
