import time
import threading
import logging
from .classifier import TrafficClassifier
from .throttler import SystemThrottler
from .monitor import NetworkMonitor

logger = logging.getLogger("Scheduler")

class Scheduler:
    def __init__(self, monitor: NetworkMonitor, throttler: SystemThrottler, classifier: TrafficClassifier):
        self.monitor = monitor
        self.throttler = throttler
        self.classifier = classifier
        self.running = False
        self.strict_mode = False # Exposed for UI
        self.thread = None
        
        # State tracking
        self.penalty_box = {} # pid -> remaining_ticks
        self.PENALTY_DURATION = 5 # ticks (approx 10-15s)

    def start(self):
        """Start the scheduler loop in a background thread."""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._loop, name="SchedulerThread", daemon=True)
        self.thread.start()
        logger.info("Scheduler background thread started.")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)

    def _loop(self):
        logger.info("Fairness Engine Active.")
        while self.running:
            try:
                self._tick()
            except Exception as e:
                logger.error(f"Scheduler tick error: {e}")
            time.sleep(2) 

    def _tick(self):
        # 1. Get Top Consumers
        consumers = self.monitor.get_top_consumers(limit=20)
        
        # 2. Group by Category & Calculate Totals
        classified = {'high': [], 'medium': [], 'low': []}
        
        for metric in consumers:
            cat = self.classifier.classify(metric)
            # Calculate Mbps
            mbps = (metric.io_rate_in + metric.io_rate_out) * 8 / (1024 * 1024)
            metric.mbps = mbps # Attach temporary attribute
            classified[cat].append(metric)

        # 3. Detect Congestion / High Priority Demand
        # "Fairness Logic": If High priority apps are active, squeeze everyone else.
        high_load = sum(m.mbps for m in classified['high'])
        self.strict_mode = high_load > 0.5 # If Zoom/Teams is pulling > 500kbps
        
        if self.strict_mode:
            logger.debug(f"Strict Mode Active (High Prio Load: {high_load:.2f} Mbps)")

        # 4. Apply Fairness Policies
        active_throttles = set()

        # --- LOW PRIORITY ---
        # Config: Max 1mbit usually. In Strict mode: 100kbit (crush it).
        low_limit_str = "100kbit" if self.strict_mode else "1mbit"
        low_limit_val = 0.1 if self.strict_mode else 1.0
        
        for m in classified['low']:
            # If exceeding limit OR already in penalty box
            if m.mbps > low_limit_val or m.pid in self.penalty_box:
                self._enforce_throttle(m, low_limit_str, active_throttles)

        # --- MEDIUM PRIORITY ---
        # Config: Max 20mbit. Strict: 5mbit.
        med_limit_str = "5mbit" if self.strict_mode else "20mbit"
        med_limit_val = 5.0 if self.strict_mode else 20.0
        
        for m in classified['medium']:
            if m.mbps > med_limit_val or m.pid in self.penalty_box:
                self._enforce_throttle(m, med_limit_str, active_throttles)
                
        # --- HIGH PRIORITY ---
        # Never throttle. Maybe log if they are huge?
        for m in classified['high']:
            if m.mbps > 50.0:
                logger.info(f"High Priority app {m.name} using lots of bandwidth ({m.mbps:.1f} Mbps)")

        # 5. Manage Penalty Box & Cleanups
        
        # List of all PIDs currently known to be managed by us
        managed_pids = list(self.penalty_box.keys())
        
        for pid in managed_pids:
            if pid in active_throttles:
                # Still offending or serving time, renew/decrement
                self.penalty_box[pid] = max(0, self.penalty_box[pid] - 1)
            else:
                self._release(pid)

    def _enforce_throttle(self, metric, limit_str, active_set):
        """Helper to apply throttle and update penalty"""
        # Add to penalty box with fresh timer if new offense
        if metric.pid not in self.penalty_box:
            logger.warning(f"Throttling {metric.name} ({metric.mbps:.2f} Mbps) -> {limit_str}")
            self.penalty_box[metric.pid] = self.PENALTY_DURATION
        
        self.throttler.throttle_pid(metric.pid, metric.ports, limit_str)
        active_set.add(metric.pid)

    def _release(self, pid):
        """Release a PID and remove from penalty box"""
        self.throttler.release_pid(pid)
        if pid in self.penalty_box:
            del self.penalty_box[pid]
