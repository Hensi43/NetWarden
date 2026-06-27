import os
import sys
import time
import psutil
import subprocess
import threading
import json
import logging
from typing import Dict, List, Optional

# Setup logger
logger = logging.getLogger("Monitor")

class ProcessMetric:
    def __init__(self, pid, name, bytes_in, bytes_out):
        self.pid = pid
        self.name = name
        self.bytes_in = bytes_in
        self.bytes_out = bytes_out
        self.io_rate_in = 0.0
        self.io_rate_out = 0.0
        self.last_update = time.time()
        self.history_in = [] # List of float rates
        self.ports = []

    def update(self, bytes_in, bytes_out):
        now = time.time()
        delta = now - self.last_update
        if delta <= 0: return

        diff_in = bytes_in - self.bytes_in
        diff_out = bytes_out - self.bytes_out
        
        # Sockets closing can cause cumulative counters to decrease. Handle this gracefully.
        if diff_in < 0: diff_in = 0
        if diff_out < 0: diff_out = 0

        self.io_rate_in = diff_in / delta
        self.io_rate_out = diff_out / delta
        
        # Keep last 20 samples (~40 seconds of history)
        self.history_in.append(self.io_rate_in)
        if len(self.history_in) > 20:
            self.history_in.pop(0)
        
        self.bytes_in = bytes_in
        self.bytes_out = bytes_out
        self.last_update = now

class NetworkMonitor:
    def __init__(self, interface="en0"):
        self.interface = interface
        self.metrics: Dict[int, ProcessMetric] = {}
        self.running = False
        self.lock = threading.Lock()
        
    def start(self):
        self.running = True
        # Platform check
        if sys.platform == 'darwin':
            self.thread = threading.Thread(target=self._monitor_mac_nettop)
        else:
            self.thread = threading.Thread(target=self._monitor_linux_proc)
            
        self.thread.daemon = True
        self.thread.start()
        logger.info(f"Monitor started on interface {self.interface}")

    def stop(self):
        self.running = False

    def _monitor_mac_nettop(self):
        """
        Parses nettop output for real-time per-process stats.
        """
        while self.running:
            try:
                # IMPORTANT: nettop in non-interactive mode.
                # nettop -L 1 is the key.
                process = subprocess.Popen(
                    ["nettop", "-P", "-L", "1", "-n"], # -n: no dns resolution
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, _ = process.communicate()
                
                self._parse_nettop_output(stdout)
                
                # Fetch ports for active pids to help the throttler
                self._enrich_ports()
                
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                time.sleep(1)
            
            time.sleep(2) # Poll interval

    def _parse_nettop_output(self, output):
        lines = output.strip().split('\n')
        if len(lines) < 2: return

        # CSV Format based on debug:
        # 0:time 1:? 2:interface 3:state 4:bytes_in 5:bytes_out ...
        # Example: 13:43:54,Google Chrome H.79917,,,25867197,3471308,...
        
        with self.lock:
            poll_stats = {}
            for line in lines[1:]:
                # Split by comma
                parts = line.split(',')
                if len(parts) < 6: continue
                
                try:
                    proc_str = parts[1]
                    if '.' not in proc_str: continue
                    
                    name_part, pid_part = proc_str.rsplit('.', 1)
                    pid = int(pid_part)
                    
                    bytes_in = int(parts[4])
                    bytes_out = int(parts[5])
                    
                    if pid not in poll_stats:
                        poll_stats[pid] = {"name": name_part, "bytes_in": 0, "bytes_out": 0}
                    poll_stats[pid]["bytes_in"] += bytes_in
                    poll_stats[pid]["bytes_out"] += bytes_out
                        
                except Exception:
                    continue

            for pid, stats in poll_stats.items():
                if pid in self.metrics:
                    self.metrics[pid].update(stats["bytes_in"], stats["bytes_out"])
                else:
                    self.metrics[pid] = ProcessMetric(pid, stats["name"], stats["bytes_in"], stats["bytes_out"])

    def _monitor_linux_proc(self):
        # Fallback simpler monitor for Linux if nethogs not available
        while self.running:
            for proc in psutil.process_iter(['pid', 'name', 'io_counters']):
                try:
                    io = proc.info['io_counters']
                    pid = proc.info['pid']
                    name = proc.info['name']
                    if io:
                        pass
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            time.sleep(2)

    def _enrich_ports(self):
        # Identify open ports for the top consumers to allow port-based throttling
        with self.lock:
            # Sort by activity
            active_pids = [
                m for m in self.metrics.values() 
                if m.io_rate_in + m.io_rate_out > 1000 # Only care if doing > 1KB/s
            ]
            
            for metric in active_pids:
                try:
                    proc = psutil.Process(metric.pid)
                    connections = proc.net_connections(kind='inet')
                    ports = []
                    for conn in connections:
                        if conn.laddr:
                            ports.append(conn.laddr.port)
                    metric.ports = list(set(ports))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

    def get_top_consumers(self, limit=5):
        with self.lock:
            sorted_metrics = sorted(
                self.metrics.values(), 
                key=lambda x: x.io_rate_in + x.io_rate_out, 
                reverse=True
            )
            return sorted_metrics[:limit]
