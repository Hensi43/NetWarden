import logging
import signal
import sys
import time
from rich.live import Live
from rich.console import Console

from core.monitor import NetworkMonitor
from core.policy import PolicyManager
from core.classifier import TrafficClassifier
from core.throttler import SystemThrottler
from core.scheduler import Scheduler
from core.ui import QueueHandler, AppUI

# Console for initial messages
console = Console()

def main():
    # 1. Setup Logging for UI
    # Remove default handlers
    root_log = logging.getLogger()
    root_log.handlers = []
    
    # File Handler
    file_handler = logging.FileHandler("throttler.log")
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    # FIFO Handler for UI
    queue_handler = QueueHandler()
    
    logging.basicConfig(
        level="INFO",
        handlers=[file_handler, queue_handler]
    )
    
    logger = logging.getLogger("Main")

    # 2. Load Config
    try:
        policy_mgr = PolicyManager("configs/policy.yaml")
        interface = policy_mgr.get_interface()
    except Exception as e:
        console.print(f"[bold red]Config Error: {e}[/bold red]")
        sys.exit(1)

    # 3. Components
    monitor = NetworkMonitor(interface=interface)
    throttler = SystemThrottler(interface=interface)
    classifier = TrafficClassifier(policy_mgr)
    scheduler = Scheduler(monitor, throttler, classifier)
    ui = AppUI(monitor, scheduler, classifier)

    # 4. Setup cleanup
    def cleanup():
        monitor.stop()
        scheduler.stop() # Stops thread
        throttler.reset()
        sys.exit(0)

    def signal_handler(sig, frame):
        cleanup()

    signal.signal(signal.SIGINT, signal_handler)

    # 5. Start
    try:
        # Initial Reset
        throttler.setup()
        
        # Start Threads
        monitor.start() 
        scheduler.start() 
        
        # UI Loop (Blocking)
        with Live(ui.get_layout(), refresh_per_second=4, screen=True) as live:
            while True:
                live.update(ui.get_layout())
                time.sleep(0.25)
                
    except Exception as e:
        logger.exception(f"Critical Error: {e}")
        # Try to restore terminal if possible
        try:
            cleanup()
        except:
            pass

if __name__ == "__main__":
    main()
