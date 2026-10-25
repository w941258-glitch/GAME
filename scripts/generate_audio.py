"""Original synthesized music and UI sounds, no external samples."""
from pathlib import Path
import math
import struct
import wave

ROOT = Path(__file__).resolve().parents[1] / "client/assets/audio"
RATE = 22050

def write(name, length, sound):
    with wave.open(str(ROOT / name), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(RATE)
        out.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, sound(i / RATE))) * 32767)) for i in range(int(RATE * length))))

def music(t):
    chords = [(220, 261.63, 329.63), (174.61, 220, 261.63), (196, 246.94, 293.66), (164.81, 196, 246.94)]
    chord = chords[int(t // 4) % 4]
    phase = t % 4
    envelope = min(1, phase / 0.25) * min(1, (4 - phase) / 0.8)
    pad = sum(math.sin(2 * math.pi * f * t) for f in chord) / 3
    note = chord[int(phase * 2) % 3] * 2
    bell = math.sin(2 * math.pi * note * t) * math.exp(-7 * (t % 0.5))
    return envelope * (pad * 0.16 + bell * 0.06)

ROOT.mkdir(parents=True, exist_ok=True)
write("city_evening.wav", 16, music)
write("click.wav", 0.09, lambda t: 0.2 * math.sin(2 * math.pi * (600 + t * 2000) * t) * math.exp(-55 * t))
write("success.wav", 0.45, lambda t: 0.18 * math.sin(2 * math.pi * (660 if t < 0.18 else 880) * t) * math.sin(math.pi * t / 0.45))
write("error.wav", 0.22, lambda t: 0.12 * math.sin(2 * math.pi * 180 * t) * math.sin(math.pi * t / 0.22))
print("Generated 4 original PCM audio assets")
