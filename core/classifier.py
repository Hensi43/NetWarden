import statistics
from .monitor import ProcessMetric

class TrafficClassifier:
    def __init__(self, policy_manager):
        self.policy = policy_manager

    def classify(self, metric: ProcessMetric) -> str:
        """
        Returns 'high', 'medium', or 'low'.
        Priority:
        1. Explicit Config Rules (Keywords)
        2. Heuristic Analysis (Traffic Patterns)
        """
        name = metric.name.lower()
        
        # 1. Config Rules
        high_cfg = self.policy.get_class_config('high')
        for kw in high_cfg.get('keywords', []):
            if kw in name: return 'high'

        low_cfg = self.policy.get_class_config('low')
        for kw in low_cfg.get('keywords', []):
            if kw in name: return 'low'
            
        mid_cfg = self.policy.get_class_config('medium')
        for kw in mid_cfg.get('keywords', []):
            if kw in name: return 'medium'

        # 2. Heuristic Analysis (The "Smart" Part)
        return self._heuristic_analysis(metric)

    def _heuristic_analysis(self, metric: ProcessMetric) -> str:
        history = metric.history_in
        if len(history) < 5:
            return 'medium' # Not enough data, assume normal

        try:
            mean_rate = statistics.mean(history)
            
            # If idle (< 10KB/s), just ignore/medium
            if mean_rate < 10 * 1024:
                return 'medium'

            stdev = statistics.stdev(history)
            cv = stdev / mean_rate if mean_rate > 0 else 0
            
            # PATTERN 1: STEADY FLOW (Low Variance)
            # Typical of: File Downloads, Video Streaming, VoIP
            if cv < 0.6:
                # Differentiate by VOLUME
                # Bulk Download: Usually maximizes connection -> Very High Speed
                # Streaming/VoIP: Governed by bitrate -> Moderate Speed
                
                # Threshold: 3 MB/s (approx 24 Mbps)
                # If sustaining > 3 MB/s steadily, it's likely a file download.
                # Zoom/4K Stream usually caps around 1-2 MB/s.
                if mean_rate > 3 * 1024 * 1024:
                    return 'low' # Bulk Download
                else:
                    return 'high' # Likely Streaming/VoIP

            # PATTERN 2: BURSTY FLOW (High Variance)
            # Typical of: Web Browsing, Loading screens
            else:
                return 'medium'
                
        except Exception:
            return 'medium'
