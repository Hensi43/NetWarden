# NetWarden
> **The intelligent local bandwidth arbiter.**

**NetWarden** is a smart, local traffic-shaping daemon that enforces a dynamic "Fair Use" policy on your machine. It monitors process-level bandwidth in real-time and automatically throttles background hogs (Steam, Torrents) to keep your critical streams (Zoom, SSH, Gaming) lag-free.

## 🎯 The Problem
In shared network environments (PGs, hostels, labs), a single specific activity can monopolize the entire bandwidth—often without the user knowing.
- **Scenario:** A background download starts while you are on a Zoom call.
- **Result:** Your call stutters and disconnects.
- **Solution:** A user-space daemon that enforces **Fairness**.

## 🧠 Architecture
> **Note:** This is a Production-Grade System Design implemented in Python + OS Native Tools (`nettop`, `dnctl`, `pfctl`, `tc`).

```ascii
+-------------------+       +----------------------+       +------------------+
| NETTOP / PSUTIL   | ----> |  TRAFFIC MONITOR     | ----> |   CLASSIFIER     |
| (OS Metrics)      |       |  (Process-level IO)  |       |  (Rule Engine)   |
+-------------------+       +----------------------+       +------------------+
                                        |                           |
                                        v                           v
                            +----------------------+       +------------------+
                            |   SCHEDULER LOOP     | <---- |  POLICY CONFIG   |
                            |  (Fairness Algo)     |       | (YAML Definitions)|
                            +----------------------+       +------------------+
                                        |
                                        v
                            +----------------------+
                            |  THROTTLER ENGINE    |
                            | (TC / PFCTL / DNCTL) |
                            +----------------------+
```

### Key Features
1.  **Monitor**: Real-time per-process socket statistics (supports macOS `nettop` in CSV mode).
2.  **Classifier**: Maps PIDs to High/Medium/Low priority based on process names.
3.  **Hysteresis Engine**: "Penalty Box" prevents throttling oscillation.
4.  **Strict Mode**: Automatically detects when High Priority apps (Zoom) are active and aggressively crushes background traffic.
5.  **TUI Dashboard**: Beautiful terminal logic via `rich`.

## 🚀 Setup & Usage

### Prerequisites
- Python 3.9+
- **macOS**: Requires sudo (for `dnctl`/`pfctl` access).
- **Linux**: Requires sudo (for `tc`).

### Installation
1.  Run the setup script (creates virtualenv and installs deps):
    ```bash
    chmod +x scripts/*.sh
    ./scripts/setup.sh
    ```

2.  Configure Policy (Optional):
    Edit `configs/policy.yaml` to define your keywords.

### Running
**WARNING**: This tool alters your network stack configuration.
```bash
sudo ./scripts/run.sh
```

### Stopping
Press `Ctrl+C`. The system attempts a clean shutdown.
If network issues persist, run:
```bash
./scripts/cleanup.sh
```

## ⚠️ Known Limitations
1.  **macOS SIP**: Detailed per-flow packet inspection is restricted on modern macOS. We use `nettop` parsing + `pfctl` anchors.
2.  **Linux**: Currently optimized for macOS; Linux `tc` support is present but less tested in this v2 revision.

---
*License: MIT*
