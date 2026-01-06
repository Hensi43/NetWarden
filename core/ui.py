from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text
from rich.console import Group
from rich.align import Align
from rich.logging import RichHandler
from collections import deque
import logging
from datetime import datetime

# Setup a global deque for logs to show in UI
log_queue = deque(maxlen=20)

class QueueHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
            style = "white"
            if record.levelno >= logging.ERROR:
                style = "red bold"
            elif record.levelno >= logging.WARNING:
                style = "yellow"
            elif record.levelno == logging.INFO:
                style = "green"
            
            log_queue.append((datetime.now().strftime("%H:%M:%S"), msg, style))
        except Exception:
            self.handleError(record)

class AppUI:
    def __init__(self, monitor, scheduler, classifier):
        self.monitor = monitor
        self.scheduler = scheduler
        self.classifier = classifier
        
    def get_layout(self) -> Layout:
        layout = Layout()
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=10)
        )
        layout["header"].update(self._make_header())
        layout["main"].split_row(
            Layout(name="processes"),
            Layout(name="throttled", ratio=1)
        )
        layout["processes"].update(self._make_process_table())
        layout["throttled"].update(self._make_throttled_table())
        layout["footer"].update(self._make_log_panel())
        return layout

    def _make_header(self):
        status = "STRICT MODE" if self.scheduler.strict_mode else "NORMAL"
        color = "red bold" if self.scheduler.strict_mode else "green"
        text = Text(f"NetWarden • Status: ", style="bold white")
        text.append(status, style=color)
        return Panel(Align.center(text), style="blue")

    def _make_process_table(self):
        table = Table(title="Active Processes", expand=True, border_style="blue")
        table.add_column("PID", style="cyan", width=6)
        table.add_column("Name", style="green")
        table.add_column("D/L (Mbps)", justify="right")
        table.add_column("U/L (Mbps)", justify="right")
        table.add_column("Class", justify="center")

        try:
            # Check for empty metrics
            metrics = list(self.monitor.metrics.values())
            # Sort by total IO
            metrics.sort(key=lambda m: m.io_rate_in + m.io_rate_out, reverse=True)
            
            for m in metrics[:15]: # Show top 15
                dl_mbps = m.io_rate_in * 8 / (1024*1024)
                ul_mbps = m.io_rate_out * 8 / (1024*1024)
                
                # Filter out idle
                if dl_mbps < 0.01 and ul_mbps < 0.01:
                    continue

                cat = self.classifier.classify(m)
                cat_style = "white"
                if cat == 'high': cat_style = "green bold"
                elif cat == 'medium': cat_style = "yellow"
                elif cat == 'low': cat_style = "red"

                table.add_row(
                    str(m.pid),
                    m.name,
                    f"{dl_mbps:.2f}",
                    f"{ul_mbps:.2f}",
                    Text(cat.upper(), style=cat_style)
                )
        except Exception:
            pass
            
        return Panel(table, title="Network Consumers")

    def _make_throttled_table(self):
        table = Table(title="Penalty Box", expand=True, border_style="red")
        table.add_column("PID", style="cyan", width=6)
        table.add_column("Ticks Left", justify="right")
        table.add_column("Limit Appx", justify="right")

        for pid, ticks in self.scheduler.penalty_box.items():
            # Get limit from throttler active rules if possible?
            limit = "Unknown"
            if pid in self.scheduler.throttler.active_rules:
                limit = self.scheduler.throttler.active_rules[pid]['limit']
            
            table.add_row(str(pid), str(ticks), limit)

        if not self.scheduler.penalty_box:
            return Panel(Align.center("No Active Throttles"), title="Penalty Box", border_style="green")
            
        return Panel(table, title="Enforcement", border_style="red")

    def _make_log_panel(self):
        log_text = Text()
        for t, msg, style in log_queue:
            log_text.append(f"[{t}] ", style="dim")
            log_text.append(msg + "\n", style=style)
        return Panel(log_text, title="System Logs", border_style="white")
