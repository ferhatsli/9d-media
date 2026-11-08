"""Animatik için geçici ses: sentez müzik yatağı + kepenk/whoosh/pin SFX. (Final: ElevenLabs müzik + TR seslendirme)"""
import sys, wave
import numpy as np

SR, DUR = 44100, 30.0
N = int(SR * DUR); t = np.arange(N) / SR
rng = np.random.default_rng(7)
mix = np.zeros((N, 2))

def note(f): return 440.0 * 2 ** ((f - 69) / 12)
def env(n, a, r):
    e = np.ones(n); na, nr = int(a * SR), int(r * SR)
    e[:na] = np.linspace(0, 1, na); e[-nr:] *= np.linspace(1, 0, nr); return e
def lp(x, fc):
    a = np.exp(-2 * np.pi * fc / SR); y = np.empty_like(x); s = 0.0
    for i in range(len(x)): s = (1 - a) * x[i] + a * s; y[i] = s
    return y
def add(sig, start, gain=1.0, pan=0.0):
    i = int(start * SR); j = min(N, i + len(sig)); sig = sig[: j - i]
    mix[i:j, 0] += sig * gain * (1 - pan) ; mix[i:j, 1] += sig * gain * (1 + pan)

BPM = 96; beat = 60 / BPM; bar = 4 * beat
prog = [(57, 60, 64), (53, 57, 60), (48, 55, 64), (55, 59, 62)]  # Am F C G
# pad
for b in range(int(DUR / bar) + 1):
    ch = prog[(b // 1) % 4]; st = b * bar; n = int(bar * SR * 1.05)
    tt = np.arange(n) / SR; sig = np.zeros(n)
    for m in ch:
        for det in (-0.08, 0.0, 0.08):
            f = note(m + 12 * 0) * (1 + det / 100)
            sig += sum(np.sin(2 * np.pi * f * h * tt) / h ** 1.6 for h in (1, 2, 3, 4))
    sig *= env(n, 0.5, 0.6) / 14
    add(sig, st, 0.55 if st < 2.2 else 0.75)
# bas (sekizlikler)
for k in range(int(DUR / (beat / 2))):
    st = k * beat / 2
    if st < 2.2 or st > 29.0: continue
    m = prog[int(st // bar) % 4][0] - 24; n = int(beat / 2 * SR); tt = np.arange(n) / SR
    s = np.sin(2 * np.pi * note(m) * tt) + 0.3 * np.sin(2 * np.pi * 2 * note(m) * tt)
    add(s * env(n, 0.005, 0.12) * 0.22, st)
# kick + hat
for k in range(int(DUR / beat)):
    st = k * beat
    if st < 2.2 or st > 28.8: continue
    n = int(0.35 * SR); tt = np.arange(n) / SR
    f = 120 * np.exp(-tt * 18) + 45
    add(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 9) * 0.55, st)
    n2 = int(0.06 * SR); hat = rng.normal(0, 1, n2); hat = hat - lp(hat, 6000)
    add(hat * np.exp(-np.arange(n2) / SR * 60) * 0.10, st + beat / 2, pan=0.3)

# SFX: kepenk (metal panjur tıkırtısı)
n = int(1.0 * SR); tt = np.arange(n) / SR
noise = rng.normal(0, 1, n); band = lp(noise, 4200) - lp(noise, 900)
rattle = (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 22 * tt))) * band * np.exp(-tt * 1.2)
add(rattle * env(n, 0.02, 0.3) * 0.9, 0.0)
# whoosh'lar
def whoosh(at, length=0.7, g=0.5):
    n = int(length * SR); tt = np.arange(n) / SR; x = rng.normal(0, 1, n)
    x = lp(x, 2500) - lp(x, 300); e = np.sin(np.pi * tt / length) ** 2
    add(x * e * g, at - length * 0.6)
for at in (2.2, 4.8, 15.6, 23.9, 26.7): whoosh(at)
# pin "ding"
n = int(0.8 * SR); tt = np.arange(n) / SR
ding = (np.sin(2 * np.pi * 1318.5 * tt) + 0.5 * np.sin(2 * np.pi * 1975.5 * tt)) * np.exp(-tt * 5)
add(ding * 0.25, 24.55)
# genel fade
fade = np.ones(N); fade[-int(1.2 * SR):] = np.linspace(1, 0, int(1.2 * SR)); mix *= fade[:, None]
mix /= np.max(np.abs(mix)) * 1.12
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
