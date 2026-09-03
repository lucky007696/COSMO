import math
import random
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QFrame, QGraphicsDropShadowEffect, 
    QScrollArea, QSizePolicy, QListWidget, QAbstractItemView,
    QApplication, QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, QTimer, QPoint, QRect, Signal, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QRadialGradient, QLinearGradient, QIcon, QPainterPath

# --- SUPER ADVANCED HOLOGRAPHIC COLORS ---
COLOR_BG = "#03040b"       # Deep void
COLOR_GRID = "#0f1626"     # Subtle matrix grid
COLOR_ACCENT_1 = "#00f3ff"   # Holographic Cyan
COLOR_ACCENT_2 = "#bc13fe"   # Neon Purple
COLOR_USER_BOX = "#193557"
COLOR_AI_BOX = "#0a2626"
COLOR_TEXT = "#e2e8f0"

# ==========================================
# 1. LIVE NEURAL NETWORK BACKGROUND
# ==========================================
class Particle:
    def __init__(self, w, h):
        self.x = random.randint(0, w)
        self.y = random.randint(0, h)
        self.vx = (random.random() - 0.5) * 1.5
        self.vy = (random.random() - 0.5) * 1.5
        self.size = random.uniform(1.0, 3.0)
        self.alpha = random.randint(50, 200)

class AdvancedCyberBackground(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.offset = 0
        self.particles = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(16)

    def init_particles(self):
        if not self.particles and self.width() > 0:
            for _ in range(60):
                self.particles.append(Particle(self.width(), self.height()))

    def animate(self):
        self.offset += 0.3
        if self.offset > 40:
            self.offset = 0

        # Update particles
        for p in self.particles:
            p.x += p.vx
            p.y += p.vy
            if p.x < 0 or p.x > self.width(): p.vx *= -1
            if p.y < 0 or p.y > self.height(): p.vy *= -1

        self.update()

    def paintEvent(self, event):
        self.init_particles()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw dark gradient background
        bg_grad = QRadialGradient(self.width()/2, self.height()/2, self.width()/1.2)
        bg_grad.setColorAt(0, QColor(9, 14, 23))
        bg_grad.setColorAt(1, QColor(COLOR_BG))
        painter.fillRect(self.rect(), bg_grad)
        
        # Draw subtle cyber grid
        pen = QPen(QColor(COLOR_GRID), 1)
        painter.setPen(pen)
        grid_size = 40
        w, h = self.width(), self.height()
        
        for x in range(int(self.offset), w, grid_size):
            painter.drawLine(x, 0, x, h)
        for y in range(int(self.offset), h, grid_size):
            painter.drawLine(0, y, w, y)
            
        # Draw particles & network lines
        painter.setPen(Qt.NoPen)
        for p in self.particles:
            painter.setBrush(QColor(0, 243, 255, p.alpha))
            painter.drawEllipse(QPoint(int(p.x), int(p.y)), int(p.size), int(p.size))

        # Connect nearby particles
        for i, p1 in enumerate(self.particles):
            for j in range(i + 1, len(self.particles)):
                p2 = self.particles[j]
                dist = math.hypot(p1.x - p2.x, p1.y - p2.y)
                if dist < 120:
                    line_alpha = int(255 * (1 - dist / 120))
                    pen = QPen(QColor(188, 19, 254, line_alpha))
                    pen.setWidthF(0.5)
                    painter.setPen(pen)
                    painter.drawLine(QPoint(int(p1.x), int(p1.y)), QPoint(int(p2.x), int(p2.y)))

        # Scanline overlay
        painter.setPen(QPen(QColor(0, 0, 0, 40), 1))
        for y in range(0, h, 4):
            painter.drawLine(0, y, w, y)


# ==========================================
# 2. FUTURISTIC CHAT BUBBLES WITH ANIMATION
# ==========================================
class ChatBubble(QFrame):
    def __init__(self, text, is_user=False):
        super().__init__()
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet("background: transparent;")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 5, 10, 5)
        
        # Glowing container frame
        box = QFrame()
        box_layout = QVBoxLayout(box)
        box_layout.setContentsMargins(20, 15, 20, 18)
        
        # Header Label (Shows who is talking)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 5)
        
        icon_lbl = QLabel()
        icon_lbl.setFont(QFont("Consolas", 12))
        
        header = QLabel("USER // DIRECTIVE" if is_user else "COSMO // RESPONSE")
        header.setFont(QFont("Consolas", 9, QFont.Bold))
        header.setStyleSheet("letter-spacing: 1px;")
        
        header_layout.addWidget(icon_lbl)
        header_layout.addWidget(header)
        header_layout.addStretch()
        box_layout.addLayout(header_layout)
        
        # Message Text
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setFont(QFont("Segoe UI", 11))
        lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        if is_user:
            icon_lbl.setText("👤")
            header.setStyleSheet(f"color: {COLOR_ACCENT_1};")
            box.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(10, 20, 35, 200); 
                    border: 1px solid rgba(0, 243, 255, 0.4); 
                    border-right: 4px solid {COLOR_ACCENT_1};
                    border-radius: 6px;
                }}
            """)
            lbl.setStyleSheet(f"color: {COLOR_TEXT}; border: none; background: transparent;")
        else:
            icon_lbl.setText("🧿")
            header.setStyleSheet(f"color: {COLOR_ACCENT_2};")
            box.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(20, 10, 35, 200); 
                    border: 1px solid rgba(188, 19, 254, 0.4); 
                    border-left: 4px solid {COLOR_ACCENT_2}; 
                    border-radius: 6px;
                }}
            """)
            lbl.setStyleSheet(f"color: {COLOR_TEXT}; border: none; background: transparent;")

        box_layout.addWidget(lbl)
        main_layout.addWidget(box)


# ==========================================
# 3. AI QUANTUM CORE (MULTIPLE RINGS, ADVANCED ANIMATION)
# ==========================================
class AIQuantumCore(QWidget):
    clicked = Signal() 
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(80, 80) 
        self.setCursor(Qt.PointingHandCursor)
        self.state = "IDLE"
        self.angle_outer = 0
        self.angle_inner = 0
        self.pulse = 0
        self.pulse_dir = 1
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(16)

    def set_state(self, state):
        self.state = state
        self.update()

    def animate(self):
        if not self.isVisible(): return
        
        speed_mult = 3 if self.state != "IDLE" else 1
        
        self.angle_outer = (self.angle_outer + 1.5 * speed_mult) % 360
        self.angle_inner = (self.angle_inner - 2.5 * speed_mult) % 360
        
        self.pulse += 0.05 * self.pulse_dir * speed_mult
        if self.pulse > 1.0: 
            self.pulse = 1.0
            self.pulse_dir = -1
        elif self.pulse < 0.0:
            self.pulse = 0.0
            self.pulse_dir = 1
            
        self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton: self.clicked.emit()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        
        center = QPoint(40, 40)
        
        if self.state == "LISTEN": 
            color_core = QColor(255, 0, 85)
            color_ring = QColor(255, 0, 170)
        elif self.state == "THINK": 
            color_core = QColor(188, 19, 254)
            color_ring = QColor(120, 0, 255)
        else: 
            color_core = QColor(0, 243, 255)
            color_ring = QColor(0, 136, 255)

        # Draw outer glowing ring
        p.translate(center)
        p.rotate(self.angle_outer)
        
        pen_outer = QPen(QColor(color_ring.red(), color_ring.green(), color_ring.blue(), 150), 2)
        p.setPen(pen_outer)
        p.setBrush(Qt.NoBrush)
        p.drawArc(-34, -34, 68, 68, 0, 360 * 16 // 3)
        p.drawArc(-34, -34, 68, 68, 360 * 16 // 2, 360 * 16 // 3)

        # Draw inner segmented ring
        p.rotate(self.angle_inner - self.angle_outer)
        pen_inner = QPen(color_core, 3)
        p.setPen(pen_inner)
        for i in range(4):
            p.drawArc(-24, -24, 48, 48, i * 90 * 16 + 15 * 16, 60 * 16)
        p.translate(-center)

        # Core radial gradient pulse
        pulse_val = 15 + (5 * self.pulse)
        grad = QRadialGradient(40, 40, pulse_val)
        grad.setColorAt(0, QColor(255, 255, 255, 200))
        grad.setColorAt(0.4, color_core)
        grad.setColorAt(1, Qt.transparent)
        p.setBrush(grad)
        p.setPen(Qt.NoPen)
        p.drawEllipse(center, int(pulse_val * 1.5), int(pulse_val * 1.5))


# ==========================================
# 4. THE MAIN WINDOW
# ==========================================
class MainUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(1200, 800)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.old_pos = None

        # Container with neural network background
        self.container = AdvancedCyberBackground()
        self.container.setStyleSheet("border-radius: 12px; border: 1px solid rgba(0, 243, 255, 0.3);")
        self.setCentralWidget(self.container)
        
        self.main_layout = QHBoxLayout(self.container)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # --- MAIN CONTENT ---
        self.content_area = QWidget()
        self.content_area.setStyleSheet("background: transparent; border: none;")
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        # --- TOP NAV BAR ---
        self.top_bar = QFrame()
        self.top_bar.setFixedHeight(80)
        self.top_bar.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(0,0,0,180), stop:1 rgba(0,0,0,0)); 
            border: none;
        """)
        top_layout = QHBoxLayout(self.top_bar)
        top_layout.setContentsMargins(30, 10, 30, 10)
        
        title_box = QFrame()
        title_box.setStyleSheet("background: transparent; border: none;")
        tb_layout = QHBoxLayout(title_box)
        tb_layout.setContentsMargins(0,0,0,0)
        
        logo = QLabel("🌀")
        logo.setFont(QFont("Segoe UI", 24))
        logo.setStyleSheet("color: #00f3ff; margin-right: 10px;")
        
        title = QLabel("COSMO")
        title.setFont(QFont("Consolas", 18, QFont.Bold))
        title.setStyleSheet(f"color: {COLOR_ACCENT_1}; letter-spacing: 3px;")
        
        tb_layout.addWidget(logo)
        tb_layout.addWidget(title)

        # Profile button styling
        self.btn_profile = QPushButton("⎈")
        self.btn_profile.setFixedSize(44, 44)
        self.btn_profile.setCursor(Qt.PointingHandCursor)
        self.btn_profile.setStyleSheet(f"""
            QPushButton {{ 
                background: rgba(188, 19, 254, 0.1); color: {COLOR_ACCENT_2}; 
                border: 1px solid rgba(188, 19, 254, 0.5); border-radius: 22px; font-size: 20px; 
            }}
            QPushButton:hover {{ background: rgba(188, 19, 254, 0.4); border-color: #bc13fe; }}
        """)

        # --- WINDOW CONTROLS ---
        cmd_style = """
            QPushButton { color: #8B949E; background: transparent; border: none; font-weight: bold; font-size: 18px; }
            QPushButton:hover { color: #00f3ff; }
        """
        self.btn_min = QPushButton("━")
        self.btn_min.setFixedSize(35, 35)
        self.btn_min.clicked.connect(self.showMinimized)
        self.btn_min.setStyleSheet(cmd_style)
        self.btn_min.setCursor(Qt.PointingHandCursor)

        self.btn_max = QPushButton("▢")
        self.btn_max.setFixedSize(35, 35)
        self.btn_max.clicked.connect(self.toggle_maximize)
        self.btn_max.setStyleSheet(cmd_style)
        self.btn_max.setCursor(Qt.PointingHandCursor)

        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(35, 35)
        self.btn_close.clicked.connect(self.hide) 
        self.btn_close.setStyleSheet("QPushButton { color: #8B949E; background: transparent; border: none; font-size: 18px; font-weight: bold; } QPushButton:hover { color: #ff0055; background: rgba(255,0,85,0.2); border-radius:8px; }")
        self.btn_close.setCursor(Qt.PointingHandCursor)

        top_layout.addWidget(title_box)
        top_layout.addStretch()
        top_layout.addWidget(self.btn_profile)
        top_layout.addSpacing(30)
        top_layout.addWidget(self.btn_min)
        top_layout.addWidget(self.btn_max)
        top_layout.addWidget(self.btn_close)
        
        self.content_layout.addWidget(self.top_bar)

        # --- CHAT LOG AREA ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical { width: 8px; background: rgba(0,0,0,0.3); border-radius: 4px; }
            QScrollBar::handle:vertical { background: rgba(0, 243, 255, 0.4); border-radius: 4px; }
            QScrollBar::handle:vertical:hover { background: #00f3ff; }
        """)
        
        self.chat_container = QWidget()
        self.chat_container.setStyleSheet("background: transparent; border: none;")
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_layout.setContentsMargins(60, 20, 60, 30)
        self.chat_layout.setSpacing(18)
        
        self.scroll_area.setWidget(self.chat_container)
        self.content_layout.addWidget(self.scroll_area)

        # --- BOTTOM COMMAND INPUT ---
        self.bottom_bar = QFrame()
        self.bottom_bar.setFixedHeight(110) 
        self.bottom_bar.setStyleSheet("""
            background: qlineargradient(x1:0, y1:1, x2:0, y2:0, stop:0 rgba(0,0,0,180), stop:1 rgba(0,0,0,0)); 
            border: none;
        """)
        bottom_layout = QHBoxLayout(self.bottom_bar)
        bottom_layout.setContentsMargins(60, 10, 60, 30)

        self.inp_frame = QFrame()
        self.inp_frame.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(5, 10, 20, 220); 
                border: 1px solid rgba(0, 243, 255, 0.3);
                border-radius: 25px; 
            }}
            QFrame:hover {{
                border: 1px solid rgba(0, 243, 255, 0.8);
            }}
        """)
        
        inp_layout = QHBoxLayout(self.inp_frame)
        inp_layout.setContentsMargins(25, 5, 10, 5)

        self.inp = QLineEdit()
        self.inp.setPlaceholderText(">> Enter command sequence or initiate neural link...")
        self.inp.setFont(QFont("Consolas", 12))
        self.inp.setStyleSheet(f"background: transparent; color: {COLOR_TEXT}; border: none;")
        
        self.btn_send = QPushButton(">>")
        self.btn_send.setFixedSize(50, 38)
        self.btn_send.setCursor(Qt.PointingHandCursor)
        self.btn_send.setStyleSheet(f"""
            QPushButton {{
                background: rgba(188, 19, 254, 0.15); 
                border: 1px solid {COLOR_ACCENT_2}; 
                border-radius: 19px; color: {COLOR_ACCENT_2}; 
                font-weight: bold; font-family: Consolas; font-size: 16px;
            }}
            QPushButton:hover {{ 
                background: {COLOR_ACCENT_2}; color: white; 
                border-color: #bc13fe;
            }}
        """)

        inp_layout.addWidget(self.inp)
        inp_layout.addWidget(self.btn_send)

        # AI Button (Quantum Core)
        self.ai_btn = AIQuantumCore() 
        
        bottom_layout.addWidget(self.inp_frame, 1) 
        bottom_layout.addSpacing(25)
        bottom_layout.addWidget(self.ai_btn)

        self.content_layout.addWidget(self.bottom_bar)
        self.main_layout.addWidget(self.content_area)

    def toggle_maximize(self):
        if self.isMaximized(): self.showNormal()
        else: self.showMaximized()

    def mousePressEvent(self, e): 
        if e.button() == Qt.LeftButton: self.old_pos = e.globalPosition().toPoint()

    def mouseMoveEvent(self, e):
        if self.old_pos: 
            delta = QPoint(e.globalPosition().toPoint() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = e.globalPosition().toPoint()

    def mouseReleaseEvent(self, e): 
        self.old_pos = None