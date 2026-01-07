import logging
import asyncio
import sys
import threading
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json

from core.monitor import NetworkMonitor
from core.policy import PolicyManager
from core.classifier import TrafficClassifier
from core.throttler import SystemThrottler
from core.scheduler import Scheduler

# --- Global State ---
monitor: NetworkMonitor = None
throttler: SystemThrottler = None
classifier: TrafficClassifier = None
scheduler: Scheduler = None
policy_mgr: PolicyManager = None

# --- Logger Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("API")

# --- App Lifecycle ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global monitor, throttler, classifier, scheduler, policy_mgr
    
    logger.info("Initializing NetWarden Backend...")
    try:
        policy_mgr = PolicyManager("configs/policy.yaml")
        interface = policy_mgr.get_interface()
        
        monitor = NetworkMonitor(interface=interface)
        throttler = SystemThrottler(interface=interface)
        classifier = TrafficClassifier(policy_mgr)
        scheduler = Scheduler(monitor, throttler, classifier)
        
        # Setup Throttler (Requires Root!)
        throttler.setup()
        
        # Start Threads
        monitor.start()
        scheduler.start()
        
        yield
    except Exception as e:
        logger.error(f"Startup Failed: {e}")
        yield
    finally:
        # Shutdown
        logger.info("Shutting down...")
        if monitor: monitor.stop()
        if scheduler: scheduler.stop()
        if throttler: throttler.reset()

app = FastAPI(lifespan=lifespan)

# Allow CORS for React Dev Server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routes ---

@app.get("/api/status")
def get_status():
    if not scheduler:
        return {"status": "off", "strict_mode": False}
    return {
        "status": "running" if scheduler.running else "stopped",
        "strict_mode": scheduler.strict_mode,
        "penalty_count": len(scheduler.penalty_box)
    }

@app.post("/api/control/strict")
def set_strict_mode(enabled: bool):
    # This is a bit hacky as scheduler calculates strict mode dynamically usually,
    # but we can force it or adjust thresholds. 
    # For now, let's just interpret this as a toggle for manual override 
    # (requires modifying logic in scheduler if we want manual override).
    # Since existing logic is purely automatic, we might just acknowledge.
    return {"message": "NetWarden runs in automatic mode. Strict mode is triggered dynamically based on High Priority load."}

@app.get("/api/processes")
def get_processes():
    if not monitor: return []
    consumers = monitor.get_top_consumers(limit=50) # more data for UI
    
    data = []
    for m in consumers:
        mbps = (m.io_rate_in + m.io_rate_out) * 8 / (1024 * 1024)
        cat = classifier.classify(m)
        is_penalized = m.pid in scheduler.penalty_box
        
        data.append({
            "pid": m.pid,
            "name": m.name,
            "mbps": round(mbps, 2),
            "upload_rate": m.io_rate_out,
            "download_rate": m.io_rate_in,
            "category": cat,
            "penalized": is_penalized
        })
    
    # Sort by speed
    data.sort(key=lambda x: x['mbps'], reverse=True)
    return data

# --- Websocket for Realtime Data ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            if monitor and scheduler:
                # Prepare payload
                consumers = monitor.get_top_consumers(limit=20)
                process_data = []
                for m in consumers:
                    mbps = (m.io_rate_in + m.io_rate_out) * 8 / (1024 * 1024)
                    cat = classifier.classify(m)
                    
                    process_data.append({
                        "pid": m.pid,
                        "name": m.name,
                        "mbps": round(mbps, 2),
                        "category": cat,
                        "penalized": m.pid in scheduler.penalty_box
                    })

                total_load = sum(p['mbps'] for p in process_data)
                
                payload = {
                    "timestamp": time.time(),
                    "system_status": {
                        "strict_mode": scheduler.strict_mode,
                        "total_bandwidth_mbps": round(total_load, 2),
                        "active_penalties": len(scheduler.penalty_box)
                    },
                    "processes": process_data
                }
                
                await websocket.send_text(json.dumps(payload))
            
            await asyncio.sleep(0.5) # Update 2x per second
    except WebSocketDisconnect:
        pass

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
