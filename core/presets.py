"""
core/presets.py
───────────────
Colección curada de fórmulas matemáticas Bytebeat y presets procedurales listos para usar en AudioLab.
"""

BYTEBEAT_PRESETS = [
    {
        "name": "Classic 42 Melody",
        "author": "viznut (2011)",
        "formula": "t * (((t >> 12) | (t >> 8)) & (63 & (t >> 4)))",
        "rate": 8000,
        "duration": 6.0,
        "description": "La legendaria fórmula chiptune que inició el movimiento Bytebeat.",
    },
    {
        "name": "Cyberpunk Arp",
        "author": "tejeez",
        "formula": "(t * 5 & t >> 7) | (t * 3 & t >> 10)",
        "rate": 8000,
        "duration": 5.0,
        "description": "Arpegio oscuro y rítmico estilo sintetizador analógico de 8 bits.",
    },
    {
        "name": "Space Siren",
        "author": "AudioLab",
        "formula": "(t * ((t >> 9 | t >> 13) & 15)) & 128",
        "rate": 11025,
        "duration": 4.5,
        "description": "Secuencia retro con modulación espacial ascendente.",
    },
    {
        "name": "Techno Beat",
        "author": "ryg",
        "formula": "((t * (t >> 8 | t >> 9) & 46 & t >> 8)) ^ (t & t >> 13 | t >> 6)",
        "rate": 8000,
        "duration": 6.0,
        "description": "Línea de bajo y percusión sintética generada puramente con bits.",
    },
    {
        "name": "Glitch Machine",
        "author": "AudioLab",
        "formula": "((t >> 6 | t | t >> (t >> 16)) * 10 + ((t >> 11) & 7)) & 128",
        "rate": 8000,
        "duration": 5.0,
        "description": "Texturas experimentales microtonales y caóticas.",
    },
    {
        "name": "Pure Sine Tone (Harmonic)",
        "author": "AudioLab",
        "formula": "int((sin(t * 0.05) + 1.0) * 127)",
        "rate": 8000,
        "duration": 3.0,
        "description": "Tono senoidal modulado matemáticamente.",
    },
]

SFX_PRESETS = [
    {
        "name": "Burbuja Relajante (Pop)",
        "type": "bubble",
        "freq": 520.0,
        "duration": 0.08,
        "wave": "sine",
        "desc": "Sonido sutil y gratificante para interfaces.",
    },
    {
        "name": "Moneda / Éxito (Chime)",
        "type": "coin",
        "freq": 660.0,
        "duration": 0.22,
        "wave": "sine",
        "desc": "Acorde doble armónico de recompensa.",
    },
    {
        "name": "Láser Arcade",
        "type": "laser",
        "freq": 980.0,
        "duration": 0.18,
        "wave": "square",
        "desc": "Disparo espacial retro con modulación exponencial.",
    },
    {
        "name": "Salto / Up",
        "type": "jump",
        "freq": 320.0,
        "duration": 0.16,
        "wave": "sine",
        "desc": "Deslizamiento ascendente estilo plataformas.",
    },
    {
        "name": "Explosión / Bomba",
        "type": "explosion",
        "freq": 160.0,
        "duration": 0.45,
        "wave": "noise",
        "desc": "Impacto de ruido filtrado y grave.",
    },
    {
        "name": "Campana Zen",
        "type": "bell",
        "freq": 587.33,
        "duration": 0.85,
        "wave": "sine",
        "desc": "Armónicos metálicos resonantes con decaimiento prolongado.",
    },
]
