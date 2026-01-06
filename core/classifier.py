from .monitor import ProcessMetric

class TrafficClassifier:
    def __init__(self, policy_manager):
        self.policy = policy_manager

    def classify(self, metric: ProcessMetric) -> str:
        """
        Returns 'high', 'medium', or 'low' based on process name/cmdline.
        """
        name = metric.name.lower()
        
        # Check High
        high_cfg = self.policy.get_class_config('high')
        for kw in high_cfg.get('keywords', []):
            if kw in name:
                return 'high'

        # Check Medium
        mid_cfg = self.policy.get_class_config('medium')
        for kw in mid_cfg.get('keywords', []):
            if kw in name:
                return 'medium'

        # Check Low
        low_cfg = self.policy.get_class_config('low')
        for kw in low_cfg.get('keywords', []):
            if kw in name:
                return 'low'

        # Default to Low if unknown and consuming bandwidth? 
        # Or Medium? Let's default to Medium for safety.
        return 'medium'
