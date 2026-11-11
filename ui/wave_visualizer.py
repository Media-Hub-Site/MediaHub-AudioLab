"""
ui/wave_visualizer.py
─────────────────────
Componente interactivo en PyQt6 para visualizar la forma de onda de audio
en tiempo real con gradiente neón estilo cian/púrpura.
"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QLinearGradient, QPen, QBrush
from PyQt6.QtCore import Qt, QPointF


class WaveVisualizer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.samples = []
        self.playhead_progress = 0.0
        self.setMinimumHeight(140)
        self.setStyleSheet("background-color: #0A0D14; border-radius: 12px;")

    def set_samples(self, samples: list[float]):
        """Actualiza el buffer de muestras y repinta el osciloscopio."""
        self.samples = samples
        self.playhead_progress = 0.0
        self.update()

    def set_playhead(self, progress: float):
        """Actualiza la barra de reproducción (0.0 a 1.0)."""
        self.playhead_progress = max(0.0, min(1.0, progress))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        mid_y = h / 2.0

        # Fondo con rejilla sutil
        painter.fillRect(0, 0, w, h, QColor("#0A0D14"))

        pen_grid = QPen(QColor("#151B28"), 1)
        pen_grid.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen_grid)
        painter.drawLine(0, int(mid_y), w, int(mid_y))

        for x in range(0, w, 40):
            painter.drawLine(x, 0, x, h)

        if not self.samples:
            # Texto guía si no hay audio
            painter.setPen(QColor("#4B5563"))
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "Escribe una fórmula o presiona un botón para generar y visualizar la onda sonora."
            )
            return

        # Dibujar forma de onda
        step = max(1, len(self.samples) // w)
        points = []

        grad = QLinearGradient(0, 0, w, 0)
        grad.setColorAt(0.0, QColor("#38BDF8"))  # Cian neón
        grad.setColorAt(0.5, QColor("#818CF8"))  # Azul índigo
        grad.setColorAt(1.0, QColor("#C084FC"))  # Púrpura eléctrico

        pen_wave = QPen(QBrush(grad), 2.2)
        painter.setPen(pen_wave)

        for x_pixel in range(w):
            idx = x_pixel * step
            if idx < len(self.samples):
                val = self.samples[idx]
                y_pixel = mid_y - (val * (mid_y * 0.85))
                points.append(QPointF(x_pixel, y_pixel))

        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])

        # Barra de Playhead si está activa
        if self.playhead_progress > 0.0:
            x_head = int(self.playhead_progress * w)
            head_pen = QPen(QColor("#22C55E"), 2)
            painter.setPen(head_pen)
            painter.drawLine(x_head, 0, x_head, h)
