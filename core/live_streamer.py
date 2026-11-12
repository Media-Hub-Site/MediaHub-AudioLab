"""
core/live_streamer.py
─────────────────────
Generador y reproductor de audio continuo en tiempo real (modo sin límite de tiempo).
Utiliza QAudioSink en modo Push (con QTimer de alta frecuencia) para alimentar
el buffer del dispositivo de audio del sistema de manera ininterrumpida y sin cortes,
mientras actualiza las muestras reactivas para los visualizadores espectrales.
"""

import math
import struct
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtMultimedia import QAudioSink, QAudioFormat, QMediaDevices
from core.synth_engine import SynthEngine


class LiveStreamManager(QObject):
    """
    Controlador de streaming continuo en tiempo real para fórmulas Bytebeat.
    """
    samples_generated = pyqtSignal(list)
    streaming_error = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.audio_sink = None
        self.io_device = None
        self._is_running = False

        self.compiled_code = None
        self.formula_sample_rate = 8000
        self.device_sample_rate = 44100
        self.t_fraction = 0.0
        self.dt = 1.0

        self.current_volume = 0.7  # Volumen por defecto (70%)

        # Timer para alimentar el buffer de audio a intervalos regulares (~20ms)
        self.push_timer = QTimer(self)
        self.push_timer.setInterval(20)
        self.push_timer.timeout.connect(self._push_audio_chunk)

        # Variables disponibles para la fórmula
        self.eval_globals = {
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "sqrt": math.sqrt,
            "pi": math.pi,
            "floor": math.floor,
            "ceil": math.ceil,
            "abs": abs,
            "min": min,
            "max": max,
            "int": int,
            "t": 0,
        }

    def is_running(self) -> bool:
        return self._is_running

    def start_infinite_stream(self, formula: str, sample_rate: int = 8000) -> bool:
        self.stop_stream()

        # Compilar la fórmula Bytebeat
        try:
            self.compiled_code = SynthEngine.compile_formula(formula)
        except Exception as e:
            self.streaming_error.emit(f"Error en la fórmula matemática:\n{e}")
            return False

        self.formula_sample_rate = sample_rate

        dev = QMediaDevices.defaultAudioOutput()
        if not dev or dev.isNull():
            self.streaming_error.emit("No se detectó ningún dispositivo de salida de audio en el sistema.")
            return False

        # Configurar formato PCM 16-bit Mono compatible
        target_format = QAudioFormat()
        target_format.setSampleRate(44100)
        target_format.setChannelCount(1)
        target_format.setSampleFormat(QAudioFormat.SampleFormat.Int16)

        if not dev.isFormatSupported(target_format):
            # Usar formato preferido si 44100 Hz mono no estuviese soportado directamente
            pref = dev.preferredFormat()
            target_format.setSampleRate(pref.sampleRate())
            target_format.setChannelCount(1)
            target_format.setSampleFormat(QAudioFormat.SampleFormat.Int16)

        self.device_sample_rate = target_format.sampleRate()
        self.dt = float(self.formula_sample_rate) / float(self.device_sample_rate)
        self.t_fraction = 0.0

        try:
            self.audio_sink = QAudioSink(dev, target_format, self)
            self.audio_sink.setBufferSize(target_format.bytesForDuration(150000))  # 150ms buffer
            self.audio_sink.setVolume(self.current_volume)
            self.io_device = self.audio_sink.start()
        except Exception as e:
            self.streaming_error.emit(f"No se pudo inicializar la salida de audio:\n{e}")
            return False

        if not self.io_device:
            self.streaming_error.emit("El dispositivo de audio no admitió el flujo continuo.")
            return False

        self._is_running = True
        self.push_timer.start()

        # Forzar un primer push inmediato para llenar el buffer
        self._push_audio_chunk()
        return True

    def _push_audio_chunk(self):
        if not self._is_running or not self.audio_sink or not self.io_device:
            return

        free_bytes = self.audio_sink.bytesFree()
        if free_bytes < 512:
            return

        # Limitar el chunk máximo por tick para no sobrecargar el hilo UI (~40ms de audio)
        max_bytes = min(free_bytes, int(self.device_sample_rate * 0.05 * 2))
        samples_to_generate = max_bytes // 2
        if samples_to_generate <= 0:
            return

        out_raw = bytearray()
        float_samples = []

        code = self.compiled_code
        g = self.eval_globals
        t_f = self.t_fraction
        dt = self.dt

        # Paso de submuestreo para el visualizador (enviar ~128 puntos por chunk para fluidez)
        vis_step = max(1, samples_to_generate // 128)

        for i in range(samples_to_generate):
            t_int = int(t_f)
            g["t"] = t_int
            try:
                val = eval(code, {"__builtins__": {}}, g)
                byte_val = int(val) & 0xFF
            except Exception:
                byte_val = 128

            norm = (byte_val - 128) / 128.0
            pcm = max(-32768, min(32767, int(norm * 32767)))
            out_raw.extend(struct.pack("<h", pcm))

            if i % vis_step == 0:
                float_samples.append(norm)

            t_f += dt

        self.t_fraction = t_f

        try:
            self.io_device.write(bytes(out_raw))
        except Exception:
            pass

        if float_samples:
            self.samples_generated.emit(float_samples)

    def set_volume(self, volume: float):
        """Ajusta el volumen en tiempo real (0.0 a 1.0)."""
        self.current_volume = max(0.0, min(1.0, volume))
        if self.audio_sink:
            try:
                self.audio_sink.setVolume(self.current_volume)
            except Exception:
                pass

    def stop_stream(self):
        self._is_running = False
        if self.push_timer.isActive():
            self.push_timer.stop()

        if self.audio_sink:
            try:
                self.audio_sink.stop()
            except Exception:
                pass
            self.audio_sink = None
            self.io_device = None
