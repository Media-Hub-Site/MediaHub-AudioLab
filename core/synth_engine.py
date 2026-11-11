"""
core/synth_engine.py
────────────────────
Motor de síntesis matemática y algorítmica para AudioLab.
Soporta:
1. Expresiones Bytebeat (matemáticas modulares sobre variable de tiempo 't').
2. Generador procedural de efectos SFX (Pop/Burbuja, Láser, Moneda/Éxito, Salto, Explosión, Campana).
3. Exportación a archivo estándar WAV PCM de 16 bits.
"""

import math
import random
import struct
import wave
import io


class SynthEngine:
    @staticmethod
    def evaluate_bytebeat(formula_str: str, duration_sec: float = 4.0, sample_rate: int = 8000) -> list[float]:
        """
        Evalúa de forma segura una expresión matemática Bytebeat sobre 't' (0..N).
        Las fórmulas Bytebeat clásicas devuelven enteros entre 0 y 255.
        Se normalizan a flotantes en el rango [-1.0, 1.0].
        """
        total_samples = int(duration_sec * sample_rate)
        samples = []

        # Entorno seguro con funciones matemáticas disponibles
        safe_dict = {
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
            "random": random.random,
        }

        # Compilar la expresión una sola vez
        try:
            compiled = compile(formula_str, "<string>", "eval")
        except Exception as e:
            raise ValueError(f"Error de sintaxis en la fórmula: {e}")

        for t in range(total_samples):
            safe_dict["t"] = t
            try:
                val = eval(compiled, {"__builtins__": {}}, safe_dict)
                # Tomar byte bajo si es entero
                if isinstance(val, (int, float)):
                    byte_val = int(val) & 255
                    # Normalizar a rango [-1.0, 1.0]
                    norm = (byte_val - 128) / 128.0
                    samples.append(norm)
                else:
                    samples.append(0.0)
            except Exception:
                samples.append(0.0)

        return samples

    @staticmethod
    def generate_sfx(
        sfx_type: str,
        base_freq: float = 440.0,
        duration: float = 0.25,
        wave_type: str = "sine",
        sample_rate: int = 44100
    ) -> list[float]:
        """
        Genera efectos procedurales basados en síntesis por modulación y envolventes.
        Tipos de SFX: 'bubble', 'coin', 'laser', 'jump', 'explosion', 'bell'.
        """
        total_samples = int(duration * sample_rate)
        samples = []

        for i in range(total_samples):
            t = i / sample_rate
            progress = t / duration

            if sfx_type == "bubble":
                # Frecuencia desciende suavemente (tono cálido)
                freq = base_freq * (1.0 - progress * 0.5)
                env = math.exp(-t * 22.0)
                phase = 2.0 * math.pi * freq * t
                val = math.sin(phase) * env

            elif sfx_type == "coin":
                # Arpegio dos tonos armónicos (Frecuencia base -> 1.33x cuarta justa)
                t_switch = duration * 0.45
                if t < t_switch:
                    f = base_freq
                    env = math.exp(-t * 14.0)
                else:
                    f = base_freq * 1.334
                    env = math.exp(-(t - t_switch) * 10.0)
                val = (math.sin(2.0 * math.pi * f * t) * 0.8 +
                       math.sin(2.0 * math.pi * f * 2.0 * t) * 0.2) * env

            elif sfx_type == "laser":
                # Barrido de frecuencia descendente rápido exponencial
                freq = base_freq * math.exp(-progress * 4.5)
                phase = 2.0 * math.pi * freq * t
                env = max(0.0, 1.0 - progress)
                # Onda cuadrada o triangular para láser
                if wave_type == "square":
                    val = (1.0 if math.sin(phase) > 0 else -1.0) * env
                else:
                    val = (math.sin(phase) * 0.7 + math.sin(phase * 2) * 0.3) * env

            elif sfx_type == "jump":
                # Barrido de frecuencia ascendente
                freq = base_freq * (1.0 + progress * 2.2)
                phase = 2.0 * math.pi * freq * t
                env = math.sin(math.pi * progress) ** 0.5
                val = math.sin(phase) * env

            elif sfx_type == "explosion":
                # Ruido blanco modulado con filtro de decaimiento
                noise = (random.random() * 2.0 - 1.0)
                env = math.exp(-progress * 5.0)
                rumble = math.sin(2.0 * math.pi * (base_freq * 0.25) * t)
                val = (noise * 0.85 + rumble * 0.15) * env

            elif sfx_type == "bell":
                # Tono con múltiples armónicos no enteros metálicos
                f = base_freq
                env = math.exp(-progress * 3.5)
                val = (
                    math.sin(2.0 * math.pi * f * t) * 0.6 +
                    math.sin(2.0 * math.pi * f * 2.76 * t) * 0.25 +
                    math.sin(2.0 * math.pi * f * 5.4 * t) * 0.15
                ) * env

            else:
                # Tono senoidal puro por defecto
                val = math.sin(2.0 * math.pi * base_freq * t) * max(0.0, 1.0 - progress)

            # Clamping suave
            clamped = max(-1.0, min(1.0, val * 0.75))
            samples.append(clamped)

        return samples

    @staticmethod
    def samples_to_wav_bytes(samples: list[float], sample_rate: int = 44100) -> bytes:
        """Convierte una lista de muestras flotantes [-1.0, 1.0] en bytes WAV estándar PCM."""
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wf:
            wf.setnchannels(1)  # Mono
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(sample_rate)
            raw = bytearray()
            for s in samples:
                val = int(max(-32767, min(32767, s * 32767)))
                raw.extend(struct.pack("<h", val))
            wf.writeframes(raw)
        return buffer.getvalue()

    @staticmethod
    def save_wav_file(filepath: str, samples: list[float], sample_rate: int = 44100):
        """Guarda la pista de audio directamente a un archivo .wav en disco."""
        wav_bytes = SynthEngine.samples_to_wav_bytes(samples, sample_rate)
        with open(filepath, "wb") as f:
            f.write(wav_bytes)
