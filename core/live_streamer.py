"""
core/live_streamer.py
─────────────────────
Generador y reproductor de audio continuo en tiempo real (modo sin límite de tiempo).
Utiliza QAudioSink y QIODevice de QtMultimedia para emitir audio de manera ininterrumpida
mientras evalúa la fórmula matemática (Bytebeat) en tiempo real y retroalimenta
al visualizador espectral.
"""

import math
import struct
from PyQt6.QtCore import QIODevice, QByteArray, pyqtSignal, QObject
from PyQt6.QtMultimedia import QAudioSink, QAudioFormat, QMediaDevices
from core.synth_engine import SynthEngine


class BytebeatAudioDevice(QIODevice):
    """
    Dispositivo QIODevice que genera muestras PCM en tiempo real on-demand
    para el QAudioSink.
    """
    def __init__(self, code_obj, sample_rate=8000, parent=None):
        super().__init__(parent)
        self.code_obj = code_obj
        self.sample_rate = sample_rate
        self.t = 0
        self.chunk_size = 1024
        self.on_samples_chunk = None  # Callback para visualizador

    def isSequential(self):
        return True

    def readData(self, maxlen):
        if maxlen <= 0 or not self.code_obj:
            return b""

        # 16-bit Mono PCM: 2 bytes por muestra
        samples_to_generate = maxlen // 2
        if samples_to_generate <= 0:
            return b""

        out_bytes = bytearray()
        float_samples = []

        code = self.code_obj
        g_vars = {"sin": math.sin, "cos": math.cos, "tan": math.tan, "pi": math.pi, "random": math.sin}

        t_curr = self.t
        for _ in range(samples_to_generate):
            try:
                g_vars["t"] = t_curr
                val = eval(code, g_vars)
                byte_val = int(val) & 0xFF
            except Exception:
                byte_val = 128

            # Convertir 0..255 bytebeat a 16-bit firmado
            norm_val = ((byte_val - 128) / 128.0)
            pcm_val = int(norm_val * 32767.0)
            pcm_val = max(-32768, min(32767, pcm_val))
            out_bytes.extend(struct.pack('<h', pcm_val))

            float_samples.append(norm_val)
            t_curr += 1

        self.t = t_curr

        if self.on_samples_chunk and float_samples:
            self.on_samples_chunk(float_samples)

        return bytes(out_bytes)

    def writeData(self, data):
        return 0


class LiveStreamManager(QObject):
    """
    Controlador de transmisión de audio infinita.
    """
    samples_generated = pyqtSignal(list)
    streaming_error = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.audio_sink = None
        self.audio_device = None
        self._is_running = False
        self.current_formula = ""
        self.current_sample_rate = 8000

    def is_running(self) -> bool:
        return self._is_running

    def start_infinite_stream(self, formula: str, sample_rate: int = 8000):
        self.stop_stream()

        # Compilar fórmula matemática con SynthEngine
        try:
            compiled_code = SynthEngine.compile_formula(formula)
        except Exception as e:
            self.streaming_error.emit(f"Error en la fórmula matemática:\n{e}")
            return False

        self.current_formula = formula
        self.current_sample_rate = sample_rate

        # Configurar formato de audio QAudioFormat
        format = QAudioFormat()
        format.setSampleRate(sample_rate)
        format.setChannelCount(1)
        format.setSampleFormat(QAudioFormat.SampleFormat.Int16)

        dev = QMediaDevices.defaultAudioOutput()
        if not dev or dev.isNull():
            self.streaming_error.emit("No se detectó ningún dispositivo de salida de audio en el sistema.")
            return False

        if not dev.isFormatSupported(format):
            format = dev.preferredFormat()

        self.audio_sink = QAudioSink(dev, format, self)
        self.audio_device = BytebeatAudioDevice(compiled_code, sample_rate=format.sampleRate(), parent=self)
        self.audio_device.on_samples_chunk = self._handle_chunk_generated

        if not self.audio_device.open(QIODevice.OpenModeFlag.ReadOnly):
            self.streaming_error.emit("No se pudo iniciar el buffer continuo de audio.")
            return False

        self.audio_sink.start(self.audio_device)
        self._is_running = True
        return True

    def _handle_chunk_generated(self, float_samples: list):
        self.samples_generated.emit(float_samples)

    def stop_stream(self):
        self._is_running = False
        if self.audio_sink:
            try:
                self.audio_sink.stop()
            except Exception:
                pass
            self.audio_sink = None

        if self.audio_device:
            try:
                self.audio_device.close()
            except Exception:
                pass
            self.audio_device = None
