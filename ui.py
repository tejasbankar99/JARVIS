"""
ui.py — JARVIS Iron Man HUD Interface
======================================
A sleek dark-themed PyQt5 desktop UI with:
  - Circular waveform / pulse animation (like MCU HUD)
  - Scrollable conversation transcript
  - Status indicators and system info
  - Command input field
  - Animated arc reactor core
"""

import sys
import math
import time
import random
import threading
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QScrollArea, QFrame, QSizePolicy,
    QGraphicsDropShadowEffect
)
from PyQt5.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QPropertyAnimation,
    QEasingCurve, QPointF, QRectF, pyqtProperty
)
from PyQt5.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QFontDatabase,
    QLinearGradient, QRadialGradient, QPainterPath, QPixmap
)


# ── Color Palette (Iron Man HUD) ──────────────────────────────────────────────
COLORS = {
    "bg":           "#050a0f",
    "bg_panel":     "#080e15",
    "accent":       "#00d4ff",      # Cyan/blue — primary
    "accent2":      "#0066cc",      # Deep blue
    "accent_glow":  "#00aaff",
    "gold":         "#c8922a",      # Iron Man gold
    "gold_light":   "#ffcc44",
    "text":         "#e0f4ff",
    "text_dim":     "#4a7a99",
    "success":      "#00ff88",
    "warning":      "#ffaa00",
    "error":        "#ff3355",
    "user_bubble":  "#0d1f2e",
    "jarvis_bubble":"#060d14",
    "border":       "#112233",
}


# ── Worker Thread for JARVIS Processing ───────────────────────────────────────

class JarvisWorker(QThread):
    """Runs JARVIS command processing in a background thread to keep UI responsive."""
    response_ready = pyqtSignal(str)
    status_changed = pyqtSignal(str)

    def __init__(self, command: str, jarvis_instance):
        super().__init__()
        self.command = command
        self.jarvis = jarvis_instance

    def run(self):
        self.status_changed.emit("processing")
        try:
            response = self.jarvis.process_command(self.command)
            self.response_ready.emit(response)
        except Exception as e:
            self.response_ready.emit(f"Processing error: {e}")
        self.status_changed.emit("idle")


# ── Arc Reactor Widget ─────────────────────────────────────────────────────────

class ArcReactorWidget(QWidget):
    """
    Animated circular arc reactor — the centerpiece of the JARVIS HUD.
    Shows waveform animations when speaking, pulse when idle.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(220, 220)
        self._phase = 0.0
        self._wave_amp = 0.0          # 0=idle, 1=speaking/active
        self._target_amp = 0.0
        self._bars = [0.0] * 32      # Waveform bar heights
        self._status = "idle"         # idle | listening | processing | speaking

        # Animation timer
        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)
        self._timer.start(33)  # ~30fps

    def set_status(self, status: str):
        """Update animation mode: idle | listening | processing | speaking"""
        self._status = status
        self._target_amp = {
            "idle": 0.15,
            "listening": 0.8,
            "processing": 0.5,
            "speaking": 1.0,
        }.get(status, 0.15)

    def _tick(self):
        """Update animation state each frame."""
        self._phase += 0.08

        # Smooth amplitude transition
        diff = self._target_amp - self._wave_amp
        self._wave_amp += diff * 0.1

        # Update waveform bars
        for i in range(len(self._bars)):
            target = (math.sin(self._phase * 2 + i * 0.4) * 0.5 + 0.5) * self._wave_amp
            self._bars[i] += (target - self._bars[i]) * 0.25

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        cx, cy = self.width() / 2, self.height() / 2
        max_r = min(cx, cy) - 5

        # ── Background circle ─────────────────────────────────────────────────
        bg_grad = QRadialGradient(cx, cy, max_r)
        bg_grad.setColorAt(0, QColor("#0a1a2a"))
        bg_grad.setColorAt(1, QColor("#050a0f"))
        painter.setBrush(QBrush(bg_grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(cx - max_r, cy - max_r, max_r * 2, max_r * 2))

        # ── Outer ring (rotating dashes) ──────────────────────────────────────
        n_outer = 36
        for i in range(n_outer):
            angle = (i / n_outer) * 2 * math.pi + self._phase * 0.3
            brightness = (math.sin(angle * 3 + self._phase) + 1) / 2
            alpha = int(80 + brightness * 120)
            color = QColor(0, 180, 255, alpha)
            painter.setPen(QPen(color, 2.5))
            r_in  = max_r - 10
            r_out = max_r - (2 if i % 3 != 0 else 6)
            x1 = cx + r_in * math.cos(angle)
            y1 = cy + r_in * math.sin(angle)
            x2 = cx + r_out * math.cos(angle)
            y2 = cy + r_out * math.sin(angle)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        # ── Waveform ring ────────────────────────────────────────────────────
        n_bars = len(self._bars)
        r_base = max_r * 0.62
        for i, bar in enumerate(self._bars):
            angle = (i / n_bars) * 2 * math.pi - math.pi / 2
            bar_h = max_r * 0.25 * bar + 2
            r_in  = r_base
            r_out = r_base + bar_h
            color_val = int(100 + bar * 155)
            color = QColor(0, color_val, 255, 200)
            painter.setPen(QPen(color, 3, Qt.SolidLine, Qt.RoundCap))
            x1 = cx + r_in  * math.cos(angle)
            y1 = cy + r_in  * math.sin(angle)
            x2 = cx + r_out * math.cos(angle)
            y2 = cy + r_out * math.sin(angle)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        # ── Mid ring ─────────────────────────────────────────────────────────
        mid_pen = QPen(QColor(0, 100, 200, 100), 1)
        painter.setPen(mid_pen)
        painter.setBrush(Qt.NoBrush)
        r_mid = max_r * 0.55
        painter.drawEllipse(QRectF(cx - r_mid, cy - r_mid, r_mid * 2, r_mid * 2))

        # ── Inner glow core ───────────────────────────────────────────────────
        glow_size = max_r * 0.35 + math.sin(self._phase * 2) * max_r * 0.04 * self._wave_amp
        core_grad = QRadialGradient(cx, cy, glow_size)
        core_alpha = int(180 + self._wave_amp * 75)
        core_grad.setColorAt(0, QColor(100, 220, 255, core_alpha))
        core_grad.setColorAt(0.4, QColor(0, 140, 255, 140))
        core_grad.setColorAt(0.8, QColor(0, 60, 120, 60))
        core_grad.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(core_grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(cx - glow_size, cy - glow_size, glow_size * 2, glow_size * 2))

        # ── Status text in center ─────────────────────────────────────────────
        status_colors = {
            "idle": "#4a7a99", "listening": "#00ff88",
            "processing": "#ffaa00", "speaking": "#00d4ff"
        }
        status_labels = {
            "idle": "STANDBY", "listening": "LISTENING",
            "processing": "PROCESSING", "speaking": "SPEAKING"
        }
        text_color = QColor(status_colors.get(self._status, "#4a7a99"))
        painter.setPen(QPen(text_color))
        font = QFont("Courier New", 7, QFont.Bold)
        painter.setFont(font)
        label = status_labels.get(self._status, "STANDBY")
        painter.drawText(QRectF(cx - 40, cy - 8, 80, 16), Qt.AlignCenter, label)


# ── Chat Bubble Widget ────────────────────────────────────────────────────────

class ChatBubble(QFrame):
    """A styled chat bubble for displaying conversation turns."""

    def __init__(self, text: str, role: str, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.NoFrame)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        # Role label
        role_label = QLabel("YOU" if role == "user" else "JARVIS")
        role_label.setFont(QFont("Courier New", 8, QFont.Bold))
        role_color = COLORS["text_dim"] if role == "user" else COLORS["accent"]
        role_label.setStyleSheet(f"color: {role_color}; letter-spacing: 2px;")
        layout.addWidget(role_label)

        # Message text
        msg_label = QLabel(text)
        msg_label.setWordWrap(True)
        msg_label.setFont(QFont("Segoe UI", 10))
        msg_label.setStyleSheet(f"color: {COLORS['text']}; line-height: 1.4;")
        msg_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(msg_label)

        # Bubble styling
        bg = COLORS["user_bubble"] if role == "user" else COLORS["jarvis_bubble"]
        border = COLORS["text_dim"] if role == "user" else COLORS["accent2"]
        self.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border: 1px solid {border};
                border-radius: 8px;
                margin: 4px;
            }}
        """)

        # Glow effect for JARVIS messages
        if role == "assistant":
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(12)
            shadow.setColor(QColor(0, 150, 255, 60))
            shadow.setOffset(0, 0)
            self.setGraphicsEffect(shadow)


# ── Main JARVIS Window ─────────────────────────────────────────────────────────

class JarvisWindow(QMainWindow):
    """
    The main JARVIS HUD window.
    Integrates arc reactor animation, chat transcript, and command input.
    """

    def __init__(self, jarvis_instance):
        super().__init__()
        self.jarvis = jarvis_instance
        self._worker = None

        self.setWindowTitle("J.A.R.V.I.S — Just A Rather Very Intelligent System")
        self.setMinimumSize(900, 680)
        self.resize(1100, 750)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        # Dark background
        self.setStyleSheet(f"""
            QMainWindow {{ background: {COLORS['bg']}; }}
        """)

        self._drag_pos = None
        self._build_ui()
        self._setup_clock_timer()

        # Startup greeting after short delay
        QTimer.singleShot(800, self._play_startup)

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Title bar
        root.addWidget(self._build_title_bar())

        # Main content area
        content = QHBoxLayout()
        content.setContentsMargins(16, 8, 16, 8)
        content.setSpacing(16)

        # Left panel: arc reactor + status
        content.addWidget(self._build_left_panel(), 0)

        # Right panel: chat + input
        content.addLayout(self._build_right_panel(), 1)

        root.addLayout(content)

    def _build_title_bar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(48)
        bar.setStyleSheet(f"""
            QWidget {{
                background: {COLORS['bg_panel']};
                border-bottom: 1px solid {COLORS['border']};
            }}
        """)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 0, 16, 0)

        # Logo text
        logo = QLabel("◈  J.A.R.V.I.S")
        logo.setFont(QFont("Courier New", 13, QFont.Bold))
        logo.setStyleSheet(f"color: {COLORS['accent']}; letter-spacing: 3px; background: transparent;")
        layout.addWidget(logo)

        layout.addStretch()

        # Clock label
        self._clock_label = QLabel()
        self._clock_label.setFont(QFont("Courier New", 10))
        self._clock_label.setStyleSheet(f"color: {COLORS['text_dim']}; background: transparent;")
        layout.addWidget(self._clock_label)

        layout.addSpacing(20)

        # Window controls
        for symbol, callback, color in [
            ("—", self.showMinimized, COLORS["text_dim"]),
            ("✕", self.close, COLORS["error"]),
        ]:
            btn = QPushButton(symbol)
            btn.setFixedSize(30, 30)
            btn.clicked.connect(callback)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {color};
                    border: 1px solid {COLORS['border']};
                    border-radius: 4px;
                    font-size: 14px;
                }}
                QPushButton:hover {{ background: rgba(255,255,255,0.08); }}
            """)
            layout.addWidget(btn)

        return bar

    def _build_left_panel(self) -> QWidget:
        panel = QWidget()
        panel.setFixedWidth(250)
        panel.setStyleSheet(f"""
            QWidget {{
                background: {COLORS['bg_panel']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(10)

        # Arc reactor
        self._reactor = ArcReactorWidget()
        layout.addWidget(self._reactor, alignment=Qt.AlignCenter)

        # Status indicator
        self._status_label = QLabel("● STANDBY")
        self._status_label.setFont(QFont("Courier New", 9, QFont.Bold))
        self._status_label.setAlignment(Qt.AlignCenter)
        self._status_label.setStyleSheet(f"color: {COLORS['text_dim']}; letter-spacing: 2px; background: transparent;")
        layout.addWidget(self._status_label)

        layout.addWidget(self._make_divider())

        # ── Live System Stats ────────────────────────────────────────────
        stats_title = QLabel("◈  SYSTEM TELEMETRY")
        stats_title.setFont(QFont("Courier New", 7, QFont.Bold))
        stats_title.setStyleSheet(f"color: {COLORS['accent']}; letter-spacing: 2px; background: transparent;")
        layout.addWidget(stats_title)

        self._stat_labels = {}
        self._stat_bars  = {}

        stat_configs = [
            ("CPU",  COLORS["accent"]),
            ("RAM",  COLORS["accent2"]),
            ("BATT", COLORS["success"]),
            ("NET",  COLORS["warning"]),
        ]

        for stat_key, bar_color in stat_configs:
            row = QVBoxLayout()
            row.setSpacing(2)

            # Label row
            lbl_row = QHBoxLayout()
            k_lbl = QLabel(stat_key)
            k_lbl.setFont(QFont("Courier New", 7))
            k_lbl.setStyleSheet(f"color: {COLORS['text_dim']}; background: transparent;")
            v_lbl = QLabel("--")
            v_lbl.setFont(QFont("Courier New", 7, QFont.Bold))
            v_lbl.setStyleSheet(f"color: {bar_color}; background: transparent;")
            v_lbl.setAlignment(Qt.AlignRight)
            lbl_row.addWidget(k_lbl)
            lbl_row.addWidget(v_lbl)
            row.addLayout(lbl_row)

            # Progress bar
            from PyQt5.QtWidgets import QProgressBar
            bar = QProgressBar()
            bar.setFixedHeight(4)
            bar.setRange(0, 100)
            bar.setValue(0)
            bar.setTextVisible(False)
            bar.setStyleSheet(f"""
                QProgressBar {{
                    background: {COLORS['border']};
                    border-radius: 2px;
                    border: none;
                }}
                QProgressBar::chunk {{
                    background: {bar_color};
                    border-radius: 2px;
                }}
            """)
            row.addWidget(bar)

            layout.addLayout(row)
            self._stat_labels[stat_key] = v_lbl
            self._stat_bars[stat_key]   = bar

        layout.addWidget(self._make_divider())

        # AI model info
        self._info_labels = {}
        from brain import get_active_provider
        info_items = [
            ("AI",    get_active_provider()[:22]),
            ("UPTIME", "--"),
        ]
        for key, val in info_items:
            row = QHBoxLayout()
            k_lbl = QLabel(key)
            k_lbl.setFont(QFont("Courier New", 7))
            k_lbl.setStyleSheet(f"color: {COLORS['text_dim']}; background: transparent;")
            v_lbl = QLabel(val)
            v_lbl.setFont(QFont("Courier New", 7, QFont.Bold))
            v_lbl.setStyleSheet(f"color: {COLORS['accent']}; background: transparent;")
            v_lbl.setAlignment(Qt.AlignRight)
            row.addWidget(k_lbl)
            row.addWidget(v_lbl)
            layout.addLayout(row)
            self._info_labels[key] = v_lbl

        layout.addStretch()

        # Voice toggle button — ON by default
        self._voice_btn = QPushButton("🎤  VOICE MODE")
        self._voice_btn.setCheckable(True)
        self._voice_btn.setChecked(True)
        self._voice_btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self._voice_btn.clicked.connect(self._toggle_voice)
        self._voice_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['bg']};
                color: {COLORS['text_dim']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 8px;
            }}
            QPushButton:checked {{
                background: rgba(0, 212, 255, 0.15);
                color: {COLORS['accent']};
                border-color: {COLORS['accent']};
            }}
            QPushButton:hover {{ background: rgba(0, 212, 255, 0.08); }}
        """)
        layout.addWidget(self._voice_btn)

        # Start live stats refresh timer
        self._stats_timer = QTimer()
        self._stats_timer.timeout.connect(self._refresh_stats)
        self._stats_timer.start(3000)   # every 3 seconds
        self._refresh_stats()           # immediate first draw

        return panel

    def _refresh_stats(self):
        """Pull latest system metrics and update the telemetry panel."""
        try:
            from system_monitor import get_all
            import time
            d = get_all()

            # CPU
            cpu = d.get("cpu_percent", 0)
            self._stat_labels["CPU"].setText(f"{cpu:.0f}%")
            self._stat_bars["CPU"].setValue(int(cpu))
            color_cpu = COLORS["error"] if cpu > 80 else COLORS["warning"] if cpu > 60 else COLORS["accent"]
            self._stat_labels["CPU"].setStyleSheet(f"color: {color_cpu}; background: transparent;")

            # RAM
            ram = d.get("ram")
            if ram:
                self._stat_labels["RAM"].setText(f"{ram.percent:.0f}%")
                self._stat_bars["RAM"].setValue(int(ram.percent))

            # Battery
            bat = d.get("battery")
            if bat:
                plug = "⚡" if bat.power_plugged else "🔋"
                self._stat_labels["BATT"].setText(f"{plug} {bat.percent:.0f}%")
                self._stat_bars["BATT"].setValue(int(bat.percent))
                color_bat = COLORS["error"] if bat.percent < 15 else COLORS["warning"] if bat.percent < 30 else COLORS["success"]
                self._stat_labels["BATT"].setStyleSheet(f"color: {color_bat}; background: transparent;")
            else:
                self._stat_labels["BATT"].setText("AC")
                self._stat_bars["BATT"].setValue(100)

            # Network
            dl = d.get("net_dl_kbps", 0)
            def fmt(k): return f"{k/1024:.1f}M" if k > 1024 else f"{k:.0f}K"
            self._stat_labels["NET"].setText(f"↓{fmt(dl)}")
            self._stat_bars["NET"].setValue(min(100, int(dl / 500)))

            # Uptime
            boot = d.get("boot_time", time.time())
            uptime = int(time.time() - boot)
            h, r = divmod(uptime, 3600)
            m = r // 60
            self._info_labels["UPTIME"].setText(f"{h}h {m}m")

        except Exception as e:
            pass   # Never crash the UI for stats

    def _build_right_panel(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Chat scroll area
        self._chat_area = QScrollArea()
        self._chat_area.setWidgetResizable(True)
        self._chat_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._chat_area.setStyleSheet(f"""
            QScrollArea {{
                background: {COLORS['bg_panel']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
            QScrollBar:vertical {{
                background: {COLORS['bg']};
                width: 6px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {COLORS['accent2']};
                border-radius: 3px;
            }}
        """)

        self._chat_container = QWidget()
        self._chat_container.setStyleSheet(f"background: {COLORS['bg_panel']};")
        self._chat_layout = QVBoxLayout(self._chat_container)
        self._chat_layout.setContentsMargins(8, 8, 8, 8)
        self._chat_layout.setSpacing(8)
        self._chat_layout.addStretch()

        self._chat_area.setWidget(self._chat_container)
        layout.addWidget(self._chat_area)

        # Input bar
        layout.addWidget(self._build_input_bar())

        return layout

    def _build_input_bar(self) -> QWidget:
        bar = QWidget()
        bar.setStyleSheet(f"""
            QWidget {{
                background: {COLORS['bg_panel']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        row = QHBoxLayout(bar)
        row.setContentsMargins(12, 8, 8, 8)
        row.setSpacing(8)

        prompt = QLabel("›")
        prompt.setFont(QFont("Courier New", 16, QFont.Bold))
        prompt.setStyleSheet(f"color: {COLORS['accent']}; background: transparent;")
        row.addWidget(prompt)

        self._input = QLineEdit()
        self._input.setPlaceholderText("Give me an order, sir…")
        self._input.setFont(QFont("Segoe UI", 11))
        self._input.returnPressed.connect(self._on_submit)
        self._input.setStyleSheet(f"""
            QLineEdit {{
                background: transparent;
                color: {COLORS['text']};
                border: none;
                padding: 4px;
            }}
            QLineEdit::placeholder {{ color: {COLORS['text_dim']}; }}
        """)
        row.addWidget(self._input)

        send_btn = QPushButton("SEND")
        send_btn.setFont(QFont("Courier New", 9, QFont.Bold))
        send_btn.setFixedSize(70, 36)
        send_btn.clicked.connect(self._on_submit)
        send_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0, 212, 255, 0.15);
                color: {COLORS['accent']};
                border: 1px solid {COLORS['accent2']};
                border-radius: 8px;
            }}
            QPushButton:hover {{ background: rgba(0, 212, 255, 0.3); }}
            QPushButton:pressed {{ background: rgba(0, 212, 255, 0.5); }}
        """)
        row.addWidget(send_btn)

        return bar

    def _make_divider(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"color: {COLORS['border']}; background: {COLORS['border']};")
        line.setFixedHeight(1)
        return line

    # ── Logic ─────────────────────────────────────────────────────────────────

    def _on_submit(self):
        text = self._input.text().strip()
        if not text or self._worker is not None:
            return
        self._input.clear()
        self.add_message(text, "user")
        self._run_command(text)

    def _run_command(self, command: str):
        self._set_status("processing")
        self._worker = JarvisWorker(command, self.jarvis)
        self._worker.response_ready.connect(self._on_response)
        self._worker.status_changed.connect(self._set_status)
        self._worker.finished.connect(self._on_worker_done)
        self._worker.start()

    def _on_response(self, response: str):
        self.add_message(response, "assistant")
        # Always speak the response (voice is ON by default)
        threading.Thread(
            target=lambda: self.jarvis.speak(response),
            daemon=True
        ).start()

    def _on_worker_done(self):
        self._worker = None

    def _set_status(self, status: str):
        self._reactor.set_status(status)
        labels = {
            "idle": ("● STANDBY", COLORS["text_dim"]),
            "listening": ("● LISTENING", COLORS["success"]),
            "processing": ("◌ PROCESSING", COLORS["warning"]),
            "speaking": ("◉ SPEAKING", COLORS["accent"]),
        }
        text, color = labels.get(status, ("● STANDBY", COLORS["text_dim"]))
        self._status_label.setText(text)
        self._status_label.setStyleSheet(f"color: {color}; letter-spacing: 2px; background: transparent;")

    def add_message(self, text: str, role: str):
        """Add a chat bubble to the conversation view."""
        bubble = ChatBubble(text, role)
        # Insert before the stretch spacer
        self._chat_layout.insertWidget(self._chat_layout.count() - 1, bubble)
        # Scroll to bottom
        QTimer.singleShot(50, lambda: self._chat_area.verticalScrollBar().setValue(
            self._chat_area.verticalScrollBar().maximum()
        ))

    def _toggle_voice(self, checked: bool):
        self.jarvis.voice_enabled = checked
        if checked:
            self._start_wake_word_listener()
        print(f"[UI] Voice mode {'ON' if checked else 'OFF'}")

    def _start_wake_word_listener(self):
        """Start background thread for wake word detection."""
        def listen_loop():
            from voice import listen_for_wake_word, listen
            while self.jarvis.voice_enabled:
                if listen_for_wake_word():
                    self._set_status("listening")
                    cmd = listen()
                    if cmd:
                        self.add_message(cmd, "user")
                        self._run_command(cmd)
        threading.Thread(target=listen_loop, daemon=True).start()

    def _setup_clock_timer(self):
        self._clock_timer = QTimer()
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)
        self._update_clock()

    def _update_clock(self):
        now = datetime.now().strftime("%a %d %b  %H:%M:%S")
        self._clock_label.setText(now)

    def _play_startup(self):
        """Show and SPEAK startup greeting."""
        hour = datetime.now().hour
        greeting = "morning" if hour < 12 else ("afternoon" if hour < 17 else "evening")
        msg = f"Good {greeting}, sir. All systems online. How may I be of service?"
        self.add_message(msg, "assistant")
        # Always speak the greeting
        threading.Thread(
            target=lambda: self.jarvis.speak(msg),
            daemon=True
        ).start()
        # Auto-start voice listener
        self._start_wake_word_listener()

        # Wire scheduler — reminders appear in chat + get spoken
        try:
            from scheduler import set_notification_callback
            def _on_reminder(message: str):
                self.add_message(message, "assistant")
                threading.Thread(
                    target=lambda: self.jarvis.speak(message),
                    daemon=True
                ).start()
            set_notification_callback(_on_reminder)
        except Exception:
            pass

        # Background battery alert monitor
        def _battery_watch():
            import time
            alerted = set()
            while True:
                try:
                    from system_monitor import check_battery_alert
                    alert = check_battery_alert()
                    if alert and alert not in alerted:
                        alerted.add(alert)
                        self.add_message(alert, "assistant")
                        threading.Thread(
                            target=lambda a=alert: self.jarvis.speak(a),
                            daemon=True
                        ).start()
                    elif not alert:
                        alerted.clear()   # Reset once battery is okay again
                except Exception:
                    pass
                time.sleep(60)   # Check every minute

        threading.Thread(target=_battery_watch, daemon=True).start()


    # ── Frameless window drag ─────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_pos:
            self.move(event.globalPos() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None


# ── App launcher ──────────────────────────────────────────────────────────────

def launch_ui(jarvis_instance) -> None:
    """Launch the JARVIS Qt application."""
    app = QApplication.instance() or QApplication(sys.argv)

    # Set application-wide font
    app.setFont(QFont("Segoe UI", 10))

    window = JarvisWindow(jarvis_instance)
    window.show()
    sys.exit(app.exec_())
