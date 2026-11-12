"""
ui/main_window.py
─────────────────
Ventana Principal de AudioLab — Estudio de Síntesis Matemática y Efectos Procedurales.
Diseño moderno Bento Grid / Media Hub Theme.
Incluye:
- Visualizador multi-espectro (Onda, Barras FFT, Radar Cósmico, Cinta Waterfall continua).
- Modo de reproducción infinita sin límite de tiempo (Live Stream continuo).
- Bloqueo visual e informativo para no exportar audio ilimitado.
- Presets de Bytebeat y efectos procedurales SFX.
"""

import os
import sys
import tempfile
import threading
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QPlainTextEdit, QComboBox, QSlider, QSpinBox, QFileDialog, QMessageBox,
    QTabWidget, QFrame, QGridLayout, QScrollArea, QCheckBox
)
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import Qt, QTimer

from core.synth_engine import SynthEngine
from core.presets import BYTEBEAT_PRESETS, SFX_PRESETS
from core.live_streamer import LiveStreamManager
from ui.wave_visualizer import WaveVisualizer


class AudioLabWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AudioLab — Laboratorio de Sonido y Fórmulas Matemáticas")
        self.resize(1080, 740)
        self.setMinimumSize(980, 660)

        # Buffer activo
        self.current_samples = []
        self.current_sample_rate = 44100
        self.temp_wav_path = os.path.join(tempfile.gettempdir(), "audiolab_preview.wav")

        # Gestor de streaming continuo (Sin límite)
        self.stream_manager = LiveStreamManager(self)
        self.stream_manager.samples_generated.connect(self._on_live_samples_received)
        self.stream_manager.streaming_error.connect(self._on_streaming_error)

        self._setup_icon()
        self.init_ui()
        self._apply_dark_theme()

        # Cargar preset inicial
        self._load_bytebeat_preset(0)

    def _setup_icon(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(base_dir, "assets", "hub", "Media-Hub.ico")
        if os.path.isfile(icon_path):
            self.setWindowIcon(QIcon(icon_path))

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(28, 20, 28, 20)
        root_layout.setSpacing(14)

        # ── 1. Header Bento ───────────────────────────────────────────────────
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        title_lbl = QLabel("AudioLab")
        title_lbl.setStyleSheet("font-size: 20pt; font-weight: 800; color: #FFFFFF;")
        subtitle_lbl = QLabel("Generador algorítmico de audio, fórmulas Bytebeat y efectos procedurales SFX")
        subtitle_lbl.setStyleSheet("font-size: 10pt; color: #94A3B8;")

        title_box.addWidget(title_lbl)
        title_box.addWidget(subtitle_lbl)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        # Botón Detener Todo
        self.btn_stop = QPushButton("⏹ Detener")
        self.btn_stop.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_stop.setFixedHeight(38)
        self.btn_stop.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: #F8FAFC;
                font-weight: 700;
                font-size: 9.5pt;
                padding: 0 16px;
                border-radius: 8px;
                border: 1px solid #475569;
            }
            QPushButton:hover { background-color: #475569; }
        """)
        self.btn_stop.clicked.connect(self._stop_playback)
        header_layout.addWidget(self.btn_stop)

        # Botón Exportar WAV
        self.btn_export = QPushButton("Exportar .WAV")
        self.btn_export.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_export.setFixedHeight(38)
        self.btn_export.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: #FFFFFF;
                font-weight: 700;
                font-size: 9.5pt;
                padding: 0 20px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover { background-color: #1D4ED8; }
            QPushButton:disabled {
                background-color: #1E293B;
                color: #64748B;
                border: 1px solid #334155;
            }
        """)
        self.btn_export.clicked.connect(self._export_wav)
        header_layout.addWidget(self.btn_export)

        root_layout.addLayout(header_layout)

        # ── 2. Visualizador Multi-Espectro ───────────────────────────────────
        self.visualizer = WaveVisualizer(self)
        root_layout.addWidget(self.visualizer)

        # ── 3. Tabs de Creación (Fórmulas vs SFX) ─────────────────────────────
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #1E293B;
                background-color: #0F172A;
                border-radius: 12px;
                padding: 12px;
            }
            QTabBar::tab {
                background-color: #1E293B;
                color: #94A3B8;
                padding: 10px 22px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: 600;
                font-size: 9.5pt;
            }
            QTabBar::tab:selected {
                background-color: #2563EB;
                color: #FFFFFF;
            }
        """)

        # Tab 1: Fórmulas Bytebeat
        self.tab_bytebeat = QWidget()
        self._init_bytebeat_tab()
        self.tabs.addTab(self.tab_bytebeat, "Fórmulas Bytebeat (Live Code)")

        # Tab 2: Efectos Procedurales SFX
        self.tab_sfx = QWidget()
        self._init_sfx_tab()
        self.tabs.addTab(self.tab_sfx, "Efectos Procedurales (SFX Generator)")

        root_layout.addWidget(self.tabs, 1)

    def _init_bytebeat_tab(self):
        layout = QVBoxLayout(self.tab_bytebeat)
        layout.setSpacing(10)

        # Selector de Presets
        row_preset = QHBoxLayout()
        lbl_p = QLabel("Presets de Fórmulas:")
        lbl_p.setStyleSheet("color: #E2E8F0; font-weight: 600;")
        self.combo_presets = QComboBox()
        for p in BYTEBEAT_PRESETS:
            self.combo_presets.addItem(f"{p['name']} — {p['author']}")
        self.combo_presets.currentIndexChanged.connect(self._on_preset_changed)
        row_preset.addWidget(lbl_p)
        row_preset.addWidget(self.combo_presets, 1)
        layout.addLayout(row_preset)

        # Editor de Fórmula
        self.txt_formula = QPlainTextEdit()
        font = QFont("Consolas", 12)
        self.txt_formula.setFont(font)
        self.txt_formula.setStyleSheet("""
            QPlainTextEdit {
                background-color: #0B0F19;
                color: #38BDF8;
                border: 1px solid #1E293B;
                border-radius: 8px;
                padding: 10px;
                font-family: Consolas, monospace;
            }
        """)
        self.txt_formula.setFixedHeight(70)
        layout.addWidget(self.txt_formula)

        self.lbl_desc = QLabel()
        self.lbl_desc.setStyleSheet("color: #94A3B8; font-style: italic;")
        layout.addWidget(self.lbl_desc)

        # Controles de Parámetros y Reproducción
        controls_row = QHBoxLayout()
        controls_row.setSpacing(14)

        lbl_dur = QLabel("Duración (s):")
        lbl_dur.setStyleSheet("color: #CBD5E1;")
        self.spin_duration = QSpinBox()
        self.spin_duration.setRange(1, 60)
        self.spin_duration.setValue(5)

        lbl_rate = QLabel("Frecuencia Muestreo:")
        lbl_rate.setStyleSheet("color: #CBD5E1;")
        self.combo_rate = QComboBox()
        self.combo_rate.addItems(["8000 Hz (Clásico)", "11025 Hz", "16000 Hz", "22050 Hz", "44100 Hz (HQ)"])

        controls_row.addWidget(lbl_dur)
        controls_row.addWidget(self.spin_duration)
        controls_row.addWidget(lbl_rate)
        controls_row.addWidget(self.combo_rate)
        controls_row.addStretch()

        # Botón 1: Sintetizar y Reproducir Finito
        self.btn_play_bytebeat = QPushButton("▶ Sintetizar y Reproducir")
        self.btn_play_bytebeat.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_play_bytebeat.setFixedHeight(40)
        self.btn_play_bytebeat.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: #FFFFFF;
                font-weight: 700;
                font-size: 10pt;
                padding: 0 20px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover { background-color: #059669; }
        """)
        self.btn_play_bytebeat.clicked.connect(self._run_bytebeat)
        controls_row.addWidget(self.btn_play_bytebeat)

        # Botón 2: Reproducción Continua Sin Límite
        self.btn_infinite = QPushButton("♾️ Reproducir Sin Límite")
        self.btn_infinite.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_infinite.setFixedHeight(40)
        self.btn_infinite.setStyleSheet("""
            QPushButton {
                background-color: #8B5CF6;
                color: #FFFFFF;
                font-weight: 700;
                font-size: 10pt;
                padding: 0 20px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover { background-color: #7C3AED; }
        """)
        self.btn_infinite.clicked.connect(self._toggle_infinite_stream)
        controls_row.addWidget(self.btn_infinite)

        layout.addLayout(controls_row)

        # Barra informativa sobre el modo sin límite
        self.lbl_infinite_notice = QLabel("💡 Modo 'Sin Límite': reproduce continuamente en tiempo real. En este modo no se descarga el archivo ya que no tiene duración fija.")
        self.lbl_infinite_notice.setStyleSheet("color: #A78BFA; font-size: 8.5pt; font-style: italic;")
        layout.addWidget(self.lbl_infinite_notice)

    def _init_sfx_tab(self):
        layout = QVBoxLayout(self.tab_sfx)
        layout.setSpacing(14)

        lbl_grid = QLabel("Efectos Rápidos Anti-estrés y Videojuegos:")
        lbl_grid.setStyleSheet("color: #E2E8F0; font-weight: 700; font-size: 10.5pt;")
        layout.addWidget(lbl_grid)

        grid = QGridLayout()
        grid.setSpacing(10)

        for i, p in enumerate(SFX_PRESETS):
            btn = QPushButton(f"🔊  {p['name']}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(44)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #1E293B;
                    color: #F8FAFC;
                    border: 1px solid #334155;
                    border-radius: 9px;
                    font-weight: 600;
                    font-size: 9.5pt;
                    padding-left: 14px;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #2563EB;
                    border-color: #3B82F6;
                }
            """)
            btn.clicked.connect(lambda checked, preset=p: self._trigger_sfx(preset))
            r = i // 3
            c = i % 3
            grid.addWidget(btn, r, c)

        layout.addLayout(grid)
        layout.addStretch()

    def _on_preset_changed(self, idx: int):
        self._load_bytebeat_preset(idx)

    def _load_bytebeat_preset(self, idx: int):
        if 0 <= idx < len(BYTEBEAT_PRESETS):
            p = BYTEBEAT_PRESETS[idx]
            self.txt_formula.setPlainText(p["formula"])
            self.lbl_desc.setText(f"{p['description']} (Autor: {p['author']})")
            self.spin_duration.setValue(int(p["duration"]))

    def _get_selected_rate(self) -> int:
        rate_map = {0: 8000, 1: 11025, 2: 16000, 3: 22050, 4: 44100}
        return rate_map.get(self.combo_rate.currentIndex(), 8000)

    def _toggle_infinite_stream(self):
        if self.stream_manager.is_running():
            self._stop_playback()
            return

        formula = self.txt_formula.toPlainText().strip()
        if not formula:
            QMessageBox.warning(self, "AudioLab", "Por favor ingresa una fórmula matemática para escuchar.")
            return

        # Detener cualquier sonido previo
        self._stop_playback()

        rate = self._get_selected_rate()
        started = self.stream_manager.start_infinite_stream(formula, sample_rate=rate)
        if started:
            self.btn_infinite.setText("⏹ Detener Sin Límite")
            self.btn_infinite.setStyleSheet("""
                QPushButton {
                    background-color: #DC2626;
                    color: #FFFFFF;
                    font-weight: 700;
                    font-size: 10pt;
                    padding: 0 20px;
                    border-radius: 8px;
                    border: none;
                }
                QPushButton:hover { background-color: #B91C1C; }
            """)
            self.btn_export.setEnabled(False)
            self.btn_export.setToolTip("La exportación está deshabilitada en el modo sin límite de tiempo (flujo continuo infinito).")
            self.visualizer.set_live_mode(True)

    def _on_live_samples_received(self, samples_chunk: list):
        self.visualizer.push_live_samples(samples_chunk)

    def _on_streaming_error(self, err_msg: str):
        self._stop_playback()
        QMessageBox.critical(self, "Error de Reproducción Continua", err_msg)

    def _run_bytebeat(self):
        self._stop_playback()

        formula = self.txt_formula.toPlainText().strip()
        if not formula:
            return

        rate = self._get_selected_rate()
        dur = float(self.spin_duration.value())

        try:
            samples = SynthEngine.evaluate_bytebeat(formula, duration_sec=dur, sample_rate=rate)
            self.current_samples = samples
            self.current_sample_rate = rate
            self.btn_export.setEnabled(True)
            self.btn_export.setToolTip("Exportar pista completa a archivo .WAV")
            self.visualizer.set_live_mode(False)
            self.visualizer.set_samples(samples)
            self._play_current_samples()
        except Exception as e:
            QMessageBox.critical(self, "Error de Síntesis", f"No se pudo evaluar la fórmula:\n{e}")

    def _trigger_sfx(self, preset: dict):
        self._stop_playback()

        rate = 44100
        samples = SynthEngine.generate_sfx(
            sfx_type=preset["type"],
            base_freq=preset["freq"],
            duration=preset["duration"],
            wave_type=preset["wave"],
            sample_rate=rate
        )
        self.current_samples = samples
        self.current_sample_rate = rate
        self.btn_export.setEnabled(True)
        self.btn_export.setToolTip("Exportar efecto de sonido a archivo .WAV")
        self.visualizer.set_live_mode(False)
        self.visualizer.set_samples(samples)
        self._play_current_samples()

    def _play_current_samples(self):
        if not self.current_samples:
            return

        SynthEngine.save_wav_file(self.temp_wav_path, self.current_samples, self.current_sample_rate)

        def _worker():
            try:
                import winsound
                winsound.PlaySound(self.temp_wav_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            except Exception:
                pass

        threading.Thread(target=_worker, daemon=True).start()

    def _stop_playback(self):
        # Detener streaming infinito si está activo
        if self.stream_manager.is_running():
            self.stream_manager.stop_stream()
            self.btn_infinite.setText("♾️ Reproducir Sin Límite")
            self.btn_infinite.setStyleSheet("""
                QPushButton {
                    background-color: #8B5CF6;
                    color: #FFFFFF;
                    font-weight: 700;
                    font-size: 10pt;
                    padding: 0 20px;
                    border-radius: 8px;
                    border: none;
                }
                QPushButton:hover { background-color: #7C3AED; }
            """)
            self.btn_export.setEnabled(True if self.current_samples else False)
            self.visualizer.set_live_mode(False)

        # Detener winsound
        try:
            import winsound
            winsound.PlaySound(None, winsound.SND_PURGE)
        except Exception:
            pass

    def _export_wav(self):
        if self.stream_manager.is_running():
            QMessageBox.information(
                self, "Exportación no disponible",
                "El modo 'Sin Límite' reproduce un flujo infinito continuo y no tiene un tamaño o duración definidos para descargar.\n\n"
                "Para exportar un archivo .WAV, usa el botón 'Sintetizar y Reproducir' con una duración definida."
            )
            return

        if not self.current_samples:
            QMessageBox.information(self, "AudioLab", "Primero sintetiza una fórmula o genera un efecto para exportar.")
            return

        out_path, _ = QFileDialog.getSaveFileName(
            self, "Exportar Archivo de Audio WAV",
            os.path.join(os.environ.get("USERPROFILE") or os.path.expanduser("~"), "Downloads", "AudioLab_Sound.wav"),
            "Archivos WAV (*.wav)"
        )
        if out_path:
            try:
                SynthEngine.save_wav_file(out_path, self.current_samples, self.current_sample_rate)
                QMessageBox.information(self, "Exportación Exitosa", f"Archivo de audio guardado en:\n{out_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error al Exportar", f"No se pudo guardar el archivo:\n{e}")

    def closeEvent(self, event):
        self._stop_playback()
        super().closeEvent(event)

    def _apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0F172A;
            }
            QLabel {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            }
            QComboBox, QSpinBox {
                background-color: #1E293B;
                color: #F8FAFC;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 9.5pt;
            }
        """)
