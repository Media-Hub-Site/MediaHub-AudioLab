"""
core/presets.py
───────────────
Colección curada de fórmulas matemáticas Bytebeat y presets procedurales listos para usar en AudioLab.
Incluye la serie legendaria Salinewin y clásicos de la demoscene.
"""

BYTEBEAT_PRESETS = [
    {
        "name": "Salinewin 1",
        "author": "Salinewin",
        "formula": "t & t >> 8",
        "rate": 8000,
        "duration": 5.0,
        "description": "Fórmula minimalista clásica Bytebeat por Salinewin.",
    },
    {
        "name": "Salinewin 2",
        "author": "Salinewin",
        "formula": "t >> 5 | (t >> 2) * (t >> 5)",
        "rate": 8000,
        "duration": 5.0,
        "description": "Arpegio armónico y rítmico multinivel por Salinewin.",
    },
    {
        "name": "Salinewin 3",
        "author": "Salinewin",
        "formula": "t * ((t / 2 >> 10 | t % 16 * t >> 8) & 8 * t >> 12 & 18) | -(t / 16) + 64",
        "rate": 8000,
        "duration": 6.0,
        "description": "Secuencia con bajo rítmico y modulación de bits por Salinewin.",
    },
    {
        "name": "Salinewin 4",
        "author": "Salinewin",
        "formula": "t * (t & 16384 ? 6 : 5) * (4 - (1 & t >> 8)) >> (3 & t >> 9) | (t | t * 3) >> 5",
        "rate": 8000,
        "duration": 6.0,
        "description": "Melodía chiptune estructurada con cambios de escala por Salinewin.",
    },
    {
        "name": "Salinewin 5",
        "author": "Salinewin",
        "formula": "t * ((t & 4096 ? 6 : 16) + (1 & (t + 16384) >> 14)) >> (3 & t >> 8) | t >> (t & 4096 ? 3 : 4)",
        "rate": 8000,
        "duration": 6.0,
        "description": "Patrón polifónico y armónico progresivo por Salinewin.",
    },
    {
        "name": "Salinewin 6",
        "author": "Salinewin",
        "formula": "t * ((t & 4096 ? t % 65536 < 59392 ? 7 : t & 4 : 16) ^ (1 & t >> 14)) >> (3 & -t >> (t & 2048 ? 2 : 10))",
        "rate": 8000,
        "duration": 7.0,
        "description": "Sinfonía matemática compleja con ternarios anidados por Salinewin.",
    },
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
        "desc": "Efecto retro de disparo sintetizado.",
    },
    {
        "name": "Salto Chiptune",
        "type": "jump",
        "freq": 320.0,
        "duration": 0.20,
        "wave": "sine",
        "desc": "Modulación rápida ascendente estilo plataformas.",
    },
    {
        "name": "Explosión / Impacto",
        "type": "explosion",
        "freq": 160.0,
        "duration": 0.45,
        "wave": "noise",
        "desc": "Ráfaga de ruido blanco con graves profundos.",
    },
    {
        "name": "Campana Zen",
        "type": "bell",
        "freq": 740.0,
        "duration": 0.90,
        "wave": "metallic",
        "desc": "Tono brillante con decaimiento armónico metálico.",
    },
]
