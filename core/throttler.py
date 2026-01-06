import subprocess
import sys
import logging
import os

logger = logging.getLogger("Throttler")

class SystemThrottler:
    def __init__(self, interface="en0"):
        self.interface = interface
        self.platform = sys.platform
        self.active_rules = {} # key: pid, value: {'limit': str, 'ports': [], 'pipe_id': int}
        self.pipe_counter = 1000  # Start pipes at 1000 to avoid conflicts

    def setup(self):
        """Prepare the system for throttling (flush existing rules)."""
        self.reset()
        if self.platform == "darwin":
            self._setup_mac()
        else:
            self._setup_linux()

    def reset(self):
        """Flush all throttling rules."""
        logger.info("Flushing all traffic control rules...")
        self.active_rules = {}
        if self.platform == "darwin":
            # Flush dummynet pipes
            subprocess.run("sudo dnctl -f flush", shell=True, stderr=subprocess.DEVNULL)
            # Flush pf rules related to us (anchor)
            subprocess.run("sudo pfctl -a com.antigravity.throttler -F all", shell=True, stderr=subprocess.DEVNULL)
        else:
            # Linux cleanup (delete root qdisc)
            subprocess.run(f"sudo tc qdisc del dev {self.interface} root", shell=True, stderr=subprocess.DEVNULL)

    def throttle_pid(self, pid, ports, limit_str):
        """
        Apply bandwidth limit to a specific PID (via its ports).
        limit_str: e.g., "1mbit", "500kbit"
        """
        if not ports:
            return 
        
        # Check if already throttled with same settings
        if pid in self.active_rules:
            current = self.active_rules[pid]
            if current['limit'] == limit_str and set(current['ports']) == set(ports):
                return
            # If changed, we update. Pipe ID stays same if possible, or just overwrite.
            pipe_id = current['pipe_id']
        else:
            pipe_id = self.pipe_counter + (pid % 10000) # Simple collision avoidance
            
        logger.info(f"Throttling PID {pid} on ports {ports} to {limit_str}")
        
        self.active_rules[pid] = {
            'limit': limit_str,
            'ports': ports,
            'pipe_id': pipe_id
        }
        
        if self.platform == "darwin":
            self._sync_rules_mac()
        else:
            self._apply_linux_rule(pipe_id, ports, limit_str)

    def release_pid(self, pid):
        if pid in self.active_rules:
            logger.info(f"Releasing throttle for PID {pid}")
            entry = self.active_rules.pop(pid)
            
            if self.platform == "darwin":
                # For mac, we just re-sync the whole table.
                # Also cleanup the pipe
                subprocess.run(f"sudo dnctl pipe {entry['pipe_id']} delete", shell=True, stderr=subprocess.DEVNULL)
                self._sync_rules_mac()
            else:
                # Linux cleanup is more complex, leaving for future extension
                pass

    # --- macOS Implementation (pfctl + dnctl) ---
    def _setup_mac(self):
        # Enable pf if not enabled
        subprocess.run("sudo pfctl -e", shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

    def _sync_rules_mac(self):
        """
        Re-applies ALL active rules to the PF anchor.
        This handles add/update/delete by rewriting the whole anchor.
        """
        pf_rules = []
        
        for pid, info in self.active_rules.items():
            pipe_id = info['pipe_id']
            ports = info['ports']
            limit = info['limit']
            
            # 1. Configure pipe logic in dnctl
            subprocess.run(f"sudo dnctl pipe {pipe_id} config bw {limit}", shell=True)
            
            # 2. Build PF rule
            port_str = "{" + ",".join(map(str, ports)) + "}"
            # Add rules for both directions
            pf_rules.append(f"dummynet out proto tcp from any to any port {port_str} pipe {pipe_id}")
            pf_rules.append(f"dummynet in proto tcp from any to any port {port_str} pipe {pipe_id}")

        # Join all rules
        rules_text = "\n".join(pf_rules) + "\n"
        
        # Feed to pfctl anchor via stdin
        try:
            p = subprocess.Popen(
                ["sudo", "pfctl", "-a", "com.antigravity.throttler", "-f", "-"],
                stdin=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            _, stderr = p.communicate(input=rules_text.encode())
            if p.returncode != 0:
                logger.error(f"Failed to apply PF rules: {stderr.decode()}")
        except Exception as e:
            logger.error(f"Error syncing mac rules: {e}")

    # --- Linux Implementation (tc) ---
    def _setup_linux(self):
        # Root qdisc
        subprocess.run(f"sudo tc qdisc add dev {self.interface} root handle 1: htb default 10", shell=True)
        # Default class (unthrottled)
        subprocess.run(f"sudo tc class add dev {self.interface} parent 1: classid 1:10 htb rate 1gbit", shell=True)

    def _apply_linux_rule(self, class_id, ports, limit):
        # 1. Add class
        subprocess.run(f"sudo tc class add dev {self.interface} parent 1: classid 1:{class_id} htb rate {limit}", shell=True)
        
        # 2. Filter via iptables/u32 or simpler tc filter if possible
        for port in ports:
            # Match destination port (download)
            subprocess.run(f"sudo tc filter add dev {self.interface} protocol ip parent 1:0 prio 1 u32 match ip sport {port} 0xffff flowid 1:{class_id}", shell=True)
            # Match source port (upload)
            subprocess.run(f"sudo tc filter add dev {self.interface} protocol ip parent 1:0 prio 1 u32 match ip dport {port} 0xffff flowid 1:{class_id}", shell=True)
