"""
ui/wave_visualizer.py
─────────────────────
Componente interactivo en PyQt6 para visualizar audio en tiempo real con 5 modos:
1. Onda (Forma de onda osciloscópica con gradiente neón)
2. Barrido (Estilo Bytebeat clásico: avanza de izquierda a derecha como barra de progreso y se reinicia)
3. Espectro Barras (Frecuencias en tiempo real con bandas estilo ecualizador)
4. Radar Cósmico (Reactivo radial de 360 grados)
5. Flujo Continuo (Cinta de audio continua)

Incluye controles de Zoom In (+) y Zoom Out (-) para ajustar la escala horizontal del barrido.
"""

import math
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame
)
from PyQt6.QtGui import (
    QPainter, QColor, QLinearGradient, QRadialGradient, QPen, QBrush, QPolygonF
)
from PyQt6.QtCore import Qt, QPointF, QTimer


class VisualizerCanvas(QWidget):
    ZOOM_LEVELS = [
        ("1/128", 128),
        ("1/64",  64),
        ("1/32",  32),
        ("1/16",  16),
        ("1/8",   8),
        ("1/4",   4),
        ("1/2",   2),
        ("1x",    1),
        ("2x",    0.5),
        ("4x",    0.25),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.samples = []
        self.mode = "sweep"  # "sweep", "wave", "bars", "radial", "waterfall"
        self.playhead_progress = 0.0
        self.is_live = False
        self.live_buffer = []
        self.max_live_samples = 2048
        self.scroll_offset = 0

        # Parámetros para modo Barrido (Sweep Bytebeat)
        self.zoom_idx = 2  # Por defecto 1/32 (32 muestras por pixel)
        self.sweep_buffer = []
        self.sweep_x = 0
        self.sweep_sample_accum = 0.0

        # Animación continua (~40 fps)
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._on_anim_tick)
        self.anim_timer.start(25)

        self.setMinimumHeight(175)
        self.setStyleSheet("background-color: #0A0D14; border-radius: 12px;")

    def set_mode(self, mode: str):
        self.mode = mode
        if mode == "sweep":
            self.reset_sweep()
        self.update()

    def get_zoom_label(self) -> str:
        return self.ZOOM_LEVELS[self.zoom_idx][0]

    def zoom_in(self) -> str:
        if self.zoom_idx < len(self.ZOOM_LEVELS) - 1:
            self.zoom_idx += 1
            self.reset_sweep()
        return self.get_zoom_label()

    def zoom_out(self) -> str:
        if self.zoom_idx > 0:
            self.zoom_idx -= 1
            self.reset_sweep()
        return self.get_zoom_label()

    def reset_sweep(self):
        w = max(10, self.width())
        self.sweep_buffer = [None] * w
        self.sweep_x = 0
        self.sweep_sample_accum = 0.0
        self.update()

    def set_samples(self, samples: list):
        """Buffer estático completo (para reproducciones con duración finita o vista estática)."""
        self.samples = samples
        self.playhead_progress = 0.0
        if samples:
            self.live_buffer = list(samples[:self.max_live_samples])
            # Poblar barrido estático con el zoom actual
            w = max(10, self.width())
            self.sweep_buffer = [None] * w
            s_per_px = self.ZOOM_LEVELS[self.zoom_idx][1]
            for i in range(w):
                idx = int(i * s_per_px)
                if idx < len(samples):
                    self.sweep_buffer[i] = samples[idx]
                else:
                    self.sweep_buffer[i] = None
            self.sweep_x = min(w, int(len(samples) / s_per_px))
        else:
            self.live_buffer = []
            self.reset_sweep()
        self.update()

    def set_playhead(self, progress: float):
        self.playhead_progress = max(0.0, min(1.0, progress))
        self.update()

    def push_live_samples(self, new_samples: list):
        """Alimenta muestras generadas en tiempo real."""
        if not new_samples:
            return

        self.live_buffer.extend(new_samples)
        if len(self.live_buffer) > self.max_live_samples:
            self.live_buffer = self.live_buffer[-self.max_live_samples:]

        # Alimentar barrido progresivo
        w = self.width()
        if w > 0:
            if len(self.sweep_buffer) != w:
                self.sweep_buffer = [None] * w
                self.sweep_x = 0
                self.sweep_sample_accum = 0.0

            s_per_px = self.ZOOM_LEVELS[self.zoom_idx][1]
            for s in new_samples:
                self.sweep_sample_accum += 1.0
                if self.sweep_sample_accum >= s_per_px:
                    self.sweep_sample_accum -= s_per_px
                    if self.sweep_x < len(self.sweep_buffer):
                        self.sweep_buffer[self.sweep_x] = s
                    self.sweep_x += 1
                    if self.sweep_x >= w:
                        # Se llenó la pantalla: reinicia desde la izquierda como barra de progreso
                        self.sweep_x = 0
                        self.sweep_buffer = [None] * w

        self.is_live = True
        self.update()

    def set_live(self, active: bool):
        self.is_live = active
        if not active:
            self.scroll_offset = 0
        self.update()

    def _on_anim_tick(self):
        if self.is_live or self.playhead_progress > 0.0:
            self.scroll_offset = (self.scroll_offset + 4) % 100000
            self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.reset_sweep()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # Fondo Bento oscuro
        painter.fillRect(0, 0, w, h, QColor("#0A0D14"))

        # Rejilla técnica de fondo
        self._draw_grid(painter, w, h)

        active_samples = self.live_buffer if (self.is_live and self.live_buffer) else self.samples

        if self.mode == "sweep":
            self._draw_sweep(painter, w, h)
        elif not active_samples:
            painter.setPen(QColor("#4B5563"))
            font = painter.font()
            font.setPointSize(10)
            painter.setFont(font)
            msg = "Presiona 'Reproducir' para escuchar y ver el espectro en tiempo real."
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, msg)
            return
        elif self.mode == "bars":
            self._draw_bars(painter, w, h, active_samples)
        elif self.mode == "radial":
            self._draw_radial(painter, w, h, active_samples)
        elif self.mode == "waterfall":
            self._draw_waterfall(painter, w, h, active_samples)
        else:
            self._draw_wave(painter, w, h, active_samples)

        # Indicador de Playhead para audio estático (no live)
        if not self.is_live and self.mode != "sweep" and self.playhead_progress > 0.0:
            x_head = int(self.playhead_progress * w)
            head_pen = QPen(QColor("#22C55E"), 2)
            painter.setPen(head_pen)
            painter.drawLine(x_head, 0, x_head, h)

    def _draw_grid(self, painter: QPainter, w: int, h: int):
        mid_y = h / 2.0
        pen_grid = QPen(QColor("#151B28"), 1)
        pen_grid.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen_grid)
        painter.drawLine(0, int(mid_y), w, int(mid_y))

        for x in range(0, w, 40):
            painter.drawLine(x, 0, x, h)

    # 1. Modo Barrido Bytebeat Clásico (Progreso horizontal con reinicio)
    def _draw_sweep(self, painter: QPainter, w: int, h: int):
        if not self.sweep_buffer:
            painter.setPen(QColor("#4B5563"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Presiona 'Reproducir' para iniciar el barrido en tiempo real.")
            return

        pen_cap = QPen(QColor("#FFFFFF"), 1.5)
        buf_len = min(w, len(self.sweep_buffer))

        # Dibujar columnas recorridas
        for x in range(buf_len):
            val = self.sweep_buffer[x]
            if val is None:
                continue

            val_norm = (val + 1.0) / 2.0
            val_norm = max(0.0, min(1.0, val_norm))
            y_sample = h - 6 - (val_norm * (h - 12))

            # Gradiente vertical de barra azul neón (estilo bytebeat clásico)
            grad = QLinearGradient(x, h, x, y_sample)
            grad.setColorAt(0.0, QColor("#172554"))  # Azul base
            grad.setColorAt(0.5, QColor("#1D4ED8"))  # Azul real
            grad.setColorAt(1.0, QColor("#38BDF8"))  # Cian neón brillante

            painter.setPen(QPen(QBrush(grad), 1.0))
            painter.drawLine(int(x), int(h - 4), int(x), int(y_sample))

            # Punto de cima blanco brillante
            painter.setPen(pen_cap)
            painter.drawPoint(int(x), int(y_sample))

        # Cabezal / Barra de progreso de barrido
        if 0 <= self.sweep_x < w:
            # Resplandor cian suave
            glow_pen = QPen(QColor(56, 189, 248, 70), 4)
            painter.setPen(glow_pen)
            painter.drawLine(self.sweep_x, 0, self.sweep_x, h)

            # Línea nítida del cabezal
            head_pen = QPen(QColor("#FFFFFF"), 2)
            painter.setPen(head_pen)
            painter.drawLine(self.sweep_x, 0, self.sweep_x, h)

    # 2. Modo Forma de Onda Clásica
    def _draw_wave(self, painter: QPainter, w: int, h: int, samples: list):
        mid_y = h / 2.0
        step = max(1, len(samples) // w)

        grad = QLinearGradient(0, 0, w, 0)
        grad.setColorAt(0.0, QColor("#38BDF8"))
        grad.setColorAt(0.5, QColor("#818CF8"))
        grad.setColorAt(1.0, QColor("#C084FC"))

        pen_wave = QPen(QBrush(grad), 2.2)
        painter.setPen(pen_wave)

        points = []
        for x_pixel in range(w):
            idx = x_pixel * step
            if idx < len(samples):
                val = samples[idx]
                y_pixel = mid_y - (val * (mid_y * 0.82))
                points.append(QPointF(x_pixel, y_pixel))

        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])

    # 3. Modo Espectro de Frecuencia / Barras Ecualizadoras
    def _draw_bars(self, painter: QPainter, w: int, h: int, samples: list):
        num_bars = min(48, max(16, w // 18))
        bar_w = (w - (num_bars * 4)) / num_bars
        chunk_size = max(1, len(samples) // num_bars)

        for i in range(num_bars):
            chunk = samples[i * chunk_size:(i + 1) * chunk_size]
            if not chunk:
                continue
            rms = math.sqrt(sum(s * s for s in chunk) / len(chunk))
            intensity = min(1.0, rms * 2.2)

            bar_h = max(6.0, intensity * (h * 0.85))
            x = i * (bar_w + 4) + 2
            y = h - bar_h - 10

            grad = QLinearGradient(x, h, x, y)
            grad.setColorAt(0.0, QColor("#06B6D4"))
            grad.setColorAt(0.6, QColor("#3B82F6"))
            grad.setColorAt(1.0, QColor("#EC4899"))

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(grad))
            painter.drawRoundedRect(int(x), int(y), int(bar_w), int(bar_h), 3, 3)

            painter.setBrush(QBrush(QColor("#F43F5E")))
            painter.drawRect(int(x), max(4, int(y - 5)), int(bar_w), 2)

    # 4. Modo Radar Radial / Espectro Circular
    def _draw_radial(self, painter: QPainter, w: int, h: int, samples: list):
        cx = w / 2.0
        cy = h / 2.0
        base_radius = min(cx, cy) * 0.42
        max_expand = min(cx, cy) * 0.45

        rad_grad = QRadialGradient(cx, cy, base_radius * 1.5)
        rad_grad.setColorAt(0.0, QColor(30, 41, 59, 80))
        rad_grad.setColorAt(0.7, QColor(56, 189, 248, 40))
        rad_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(rad_grad))
        painter.setPen(QPen(QColor("#1E293B"), 1))
        painter.drawEllipse(QPointF(cx, cy), base_radius, base_radius)

        points = []
        num_spokes = 90
        step = max(1, len(samples) // num_spokes)

        for i in range(num_spokes):
            angle = (2.0 * math.pi * i) / num_spokes
            idx = (i * step) % len(samples)
            amp = abs(samples[idx]) if idx < len(samples) else 0.0
            r = base_radius + (amp * max_expand)

            px = cx + r * math.cos(angle)
            py = cy + r * math.sin(angle)
            points.append(QPointF(px, py))

        if points:
            pen_rad = QPen(QColor("#38BDF8"), 2.0)
            painter.setPen(pen_rad)
            for i in range(len(points)):
                next_p = points[(i + 1) % len(points)]
                painter.drawLine(points[i], next_p)

                if i % 3 == 0:
                    in_x = cx + base_radius * 0.85 * math.cos((2.0 * math.pi * i) / num_spokes)
                    in_y = cy + base_radius * 0.85 * math.sin((2.0 * math.pi * i) / num_spokes)
                    ray_pen = QPen(QColor(129, 140, 248, 120), 1)
                    painter.setPen(ray_pen)
                    painter.drawLine(QPointF(in_x, in_y), points[i])
                    painter.setPen(pen_rad)

    # 5. Modo Flujo Continuo Horizontal
    def _draw_waterfall(self, painter: QPainter, w: int, h: int, samples: list):
        mid_y = h / 2.0
        step = max(1, len(samples) // w)

        grad = QLinearGradient(0, 0, w, 0)
        grad.setColorAt(0.0, QColor("#10B981"))
        grad.setColorAt(0.5, QColor("#38BDF8"))
        grad.setColorAt(1.0, QColor("#F59E0B"))

        pen_flow = QPen(QBrush(grad), 2.2)
        painter.setPen(pen_flow)

        offset = self.scroll_offset
        points = []
        for x in range(w):
            idx = ((x + offset) * step) % len(samples)
            val = samples[idx]
            y = mid_y - (val * (mid_y * 0.78))
            points.append(QPointF(x, y))

        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])

        poly = [QPointF(0, h)] + points + [QPointF(w, h)]
        fill_grad = QLinearGradient(0, mid_y, 0, h)
        fill_grad.setColorAt(0.0, QColor(56, 189, 248, 55))
        fill_grad.setColorAt(1.0, QColor(10, 13, 20, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(fill_grad))
        painter.drawPolygon(QPolygonF(poly))


class WaveVisualizer(QWidget):
    """
    Contenedor principal del visualizador que incluye la botonera de modos y controles de zoom:
    - Barrido (Progreso reiniciable estilo Bytebeat)
    - Onda
    - Espectro Barras
    - Radar Cósmico
    - Flujo Continuo
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Barra de control de modo de espectro y zoom
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(4, 0, 4, 0)
        top_bar.setSpacing(6)

        lbl_mode = QLabel("Modo:")
        lbl_mode.setStyleSheet("color: #94A3B8; font-size: 9pt; font-weight: 600;")
        top_bar.addWidget(lbl_mode)

        self.btn_sweep = self._create_mode_btn("Barrido", "sweep", active=True)
        self.btn_wave = self._create_mode_btn("Onda", "wave")
        self.btn_bars = self._create_mode_btn("Espectro Barras", "bars")
        self.btn_radial = self._create_mode_btn("Radar Cósmico", "radial")
        self.btn_flow = self._create_mode_btn("Flujo Continuo", "waterfall")

        self.mode_buttons = [self.btn_sweep, self.btn_wave, self.btn_bars, self.btn_radial, self.btn_flow]

        top_bar.addWidget(self.btn_sweep)
        top_bar.addWidget(self.btn_wave)
        top_bar.addWidget(self.btn_bars)
        top_bar.addWidget(self.btn_radial)
        top_bar.addWidget(self.btn_flow)

        top_bar.addSpacing(10)

        # Controles de Zoom para el modo Barrido
        self.zoom_box = QWidget()
        zoom_layout = QHBoxLayout(self.zoom_box)
        zoom_layout.setContentsMargins(0, 0, 0, 0)
        zoom_layout.setSpacing(4)

        self.btn_zoom_out = QPushButton("- Zoom")
        self.btn_zoom_out.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_zoom_out.setFixedHeight(26)
        self.btn_zoom_out.setStyleSheet("""
            QPushButton {
                background-color: #1E293B;
                color: #CBD5E1;
                font-weight: 600;
                font-size: 8pt;
                padding: 0 8px;
                border-radius: 5px;
                border: 1px solid #334155;
            }
            QPushButton:hover { background-color: #334155; color: #FFFFFF; }
        """)
        self.btn_zoom_out.clicked.connect(self._on_zoom_out)

        self.lbl_zoom = QLabel("1/32")
        self.lbl_zoom.setStyleSheet("""
            color: #38BDF8;
            font-weight: 700;
            font-size: 8.5pt;
            background-color: #0F172A;
            border: 1px solid #1E293B;
            border-radius: 5px;
            padding: 3px 8px;
        """)

        self.btn_zoom_in = QPushButton("+ Zoom")
        self.btn_zoom_in.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_zoom_in.setFixedHeight(26)
        self.btn_zoom_in.setStyleSheet("""
            QPushButton {
                background-color: #1E293B;
                color: #CBD5E1;
                font-weight: 600;
                font-size: 8pt;
                padding: 0 8px;
                border-radius: 5px;
                border: 1px solid #334155;
            }
            QPushButton:hover { background-color: #334155; color: #FFFFFF; }
        """)
        self.btn_zoom_in.clicked.connect(self._on_zoom_in)

        zoom_layout.addWidget(self.btn_zoom_out)
        zoom_layout.addWidget(self.lbl_zoom)
        zoom_layout.addWidget(self.btn_zoom_in)

        top_bar.addWidget(self.zoom_box)
        top_bar.addStretch()

        self.lbl_live_badge = QLabel("TIEMPO REAL")
        self.lbl_live_badge.setStyleSheet("""
            color: #10B981;
            font-size: 8.5pt;
            font-weight: 800;
            background-color: rgba(16, 185, 129, 0.15);
            border: 1px solid #10B981;
            border-radius: 6px;
            padding: 3px 8px;
        """)
        self.lbl_live_badge.setVisible(False)
        top_bar.addWidget(self.lbl_live_badge)

        layout.addLayout(top_bar)

        # Canvas gráfico
        self.canvas = VisualizerCanvas(self)
        layout.addWidget(self.canvas)

        # Inicializar etiqueta de zoom
        self.lbl_zoom.setText(self.canvas.get_zoom_label())

    def _create_mode_btn(self, text: str, mode_id: str, active: bool = False) -> QPushButton:
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(26)
        btn.setProperty("mode_id", mode_id)
        btn.clicked.connect(lambda: self._select_mode(mode_id))
        self._style_mode_btn(btn, active)
        return btn

    def _style_mode_btn(self, btn: QPushButton, active: bool):
        if active:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2563EB;
                    color: #FFFFFF;
                    font-weight: 700;
                    font-size: 8.5pt;
                    padding: 0 10px;
                    border-radius: 6px;
                    border: 1px solid #3B82F6;
                }
            """)
        else:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #1E293B;
                    color: #94A3B8;
                    font-weight: 600;
                    font-size: 8.5pt;
                    padding: 0 10px;
                    border-radius: 6px;
                    border: 1px solid #334155;
                }
                QPushButton:hover {
                    background-color: #334155;
                    color: #F8FAFC;
                }
            """)

    def _select_mode(self, selected_mode: str):
        for btn in self.mode_buttons:
            is_active = (btn.property("mode_id") == selected_mode)
            self._style_mode_btn(btn, is_active)
        self.canvas.set_mode(selected_mode)
        # Mostrar controles de Zoom únicamente cuando el modo Barrido esté activo
        self.zoom_box.setVisible(selected_mode == "sweep")

    def _on_zoom_in(self):
        new_label = self.canvas.zoom_in()
        self.lbl_zoom.setText(new_label)

    def _on_zoom_out(self):
        new_label = self.canvas.zoom_out()
        self.lbl_zoom.setText(new_label)

    def set_samples(self, samples: list):
        self.canvas.set_samples(samples)

    def set_playhead(self, progress: float):
        self.canvas.set_playhead(progress)

    def push_live_samples(self, new_samples: list):
        self.canvas.push_live_samples(new_samples)

    def set_live_mode(self, active: bool):
        self.lbl_live_badge.setVisible(active)
        self.canvas.set_live(active)
