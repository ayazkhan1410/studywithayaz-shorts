"""v2 audio: energetic original track (supersaw chords, sidechain pump, hook melody)
plus satisfying SFX (clicks, pops, counting ticks, cha-ching). All synthesized here,
so it is free of licensing issues. Writes mix.wav (stereo, 48 kHz)."""
import json
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt, fftconvolve

SR = 48000
tm = json.load(open("timing.json"))
sfx = json.load(open("sfx.json"))
T = tm["total"]
N = int(T * SR)
rng = np.random.default_rng(11)
L = tm["lines"]

def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)

def env(n, a=0.003, r=0.2):
    t = np.arange(n) / SR
    return np.minimum(t / max(a, 1e-6), 1) * np.exp(-t / r)

def lp(x, fc, order=2):
    return sosfilt(butter(order, min(fc, SR * 0.45), "low", fs=SR, output="sos"), x)

def hp(x, fc, order=2):
    return sosfilt(butter(order, fc, "high", fs=SR, output="sos"), x)

def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, min(hi, SR * 0.45)], "band", fs=SR, output="sos"), x)

def add(buf, x, at, gain=1.0):
    i = int(at * SR)
    if i < 0 or i >= buf.shape[0]:
        return
    x = x[: buf.shape[0] - i]
    if buf.ndim == 2 and x.ndim == 1:
        x = np.stack([x, x], 1)
    buf[i: i + len(x)] += x * gain

def saw(f, n, phase=0.0):
    t = np.arange(n) / SR
    return 2 * ((f * t + phase) % 1.0) - 1

def reverb(x, secs=1.4, mix=0.25):
    n = int(secs * SR)
    t = np.arange(n) / SR
    out = np.zeros_like(x)
    for ch in range(2):
        ir = rng.standard_normal(n) * np.exp(-t / (secs / 5))
        ir = lp(ir, 6000)
        ir /= np.sqrt(np.sum(ir ** 2))
        out[:, ch] = fftconvolve(x[:, ch], ir)[: len(x)]
    return x + out * mix

# ---------------- music ----------------
BPM = 124
beat = 60 / BPM
bar = 4 * beat
drop = L[3]["start"] - 0.05
music = np.zeros((N, 2))
send = np.zeros((N, 2))  # reverb send

prog = [(57, [69, 72, 76]), (53, [65, 69, 72]), (60, [67, 72, 76]), (55, [67, 71, 74])]  # Am F C G

# sidechain pump curve (on every beat)
tt = np.arange(N) / SR
ph = (tt % beat) / beat
pump = 0.25 + 0.75 * np.minimum(1, (ph / 0.42) ** 1.6)

# supersaw chords per bar, stereo detune, filter opens through intro
chords = np.zeros((N, 2))
nbars = int(T / bar) + 1
for b in range(nbars):
    t0 = b * bar
    n = int(bar * SR)
    root, tri = prog[b % 4]
    for ch in range(2):
        x = np.zeros(n)
        for m in tri:
            for d in np.linspace(-0.18, 0.18, 5):
                x += saw(hz(m + d + (0.03 if ch else -0.03)), n, rng.random())
        x *= np.minimum(np.arange(n) / (0.02 * SR), 1) * np.minimum((n - np.arange(n)) / (0.05 * SR), 1)
        cutoff = 900 + 5000 * min(1, max(0, t0 / drop)) if t0 < drop else 6500
        x = lp(x, cutoff, 2) * 0.035
        add(chords[:, ch], x, t0)
chords *= pump[:, None]
music += chords * 0.9
send += chords * 0.4

# bass: saw + sub, offbeat 8ths after the drop, whole notes before
bassbuf = np.zeros(N)
for b in range(nbars):
    root = prog[b % 4][0] - 24
    for k in range(8):
        t0 = b * bar + k * beat / 2
        if t0 < drop and k % 2 == 0:
            continue
        n = int(beat / 2 * 0.9 * SR)
        x = 0.6 * saw(hz(root), n) + np.sin(2 * np.pi * hz(root) * np.arange(n) / SR)
        x = lp(x, 900) * env(n, 0.004, 0.22) * 0.32
        add(bassbuf, x, t0)
bassbuf *= pump
music += np.stack([bassbuf, bassbuf], 1)

# drums
def kick():
    n = int(0.4 * SR); t = np.arange(n) / SR
    f = 48 + 140 * np.exp(-t * 35)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.001, 0.16)
    click = hp(rng.standard_normal(n), 3000) * env(n, 0.0005, 0.004) * 0.4
    return np.tanh((body + click) * 1.6) * 0.9

def clap():
    n = int(0.3 * SR); x = bp(rng.standard_normal(n), 900, 5000)
    e = np.zeros(n)
    for d in (0, 0.011, 0.022):
        i = int(d * SR); e[i:] += env(n - i, 0.0008, 0.012 if d < 0.02 else 0.09)
    return x * e * 0.55

def hat(open_=False):
    n = int((0.22 if open_ else 0.06) * SR)
    return hp(rng.standard_normal(n), 7000) * env(n, 0.0008, 0.07 if open_ else 0.016) * (0.22 if open_ else 0.16)

drums = np.zeros((N, 2))
nbeats = int(T / beat) + 1
for b in range(nbeats):
    t0 = b * beat
    full = t0 >= drop
    if t0 > T - 1.0:
        break
    add(drums, kick(), t0, 1.0 if full else 0.7)
    if (full and b % 2 == 1) or (not full and t0 > 5 and b % 2 == 1):
        c = clap(); add(drums, c, t0, 1.0 if full else 0.6); add(send, c, t0, 0.6)
    add(drums, hat(open_=full), t0 + beat / 2)
    if full:
        for q in (0.25, 0.75):
            add(drums, np.stack([hat() * 0.8, hat() * 0.5], 1) if rng.random() < 0.5 else hat(), t0 + q * beat)
# snare roll + riser into the drop
for i in range(16):
    tr = drop - 1.6 + i * 0.1
    add(drums, clap(), tr, 0.25 + 0.04 * i)
n = int(1.8 * SR); t = np.arange(n) / SR
riser = np.zeros(n)
for i in range(0, n, 2048):
    seg = rng.standard_normal(min(2048, n - i))
    riser[i:i + len(seg)] = bp(seg, 300 + 6000 * (i / n) ** 2, 9000 + 2000 * i / n)
riser *= (t / t[-1]) ** 2 * 0.35
add(send, riser, drop - 1.8, 0.5); add(music, riser, drop - 1.8)
# downlifter boom at the drop
n = int(1.0 * SR); t = np.arange(n) / SR
boom = np.sin(2 * np.pi * np.cumsum(30 + 60 * np.exp(-t * 6)) / SR) * env(n, 0.002, 0.35) * 0.7
add(music, boom, drop)
music += drums

# hook melody (pluck), after the drop; softer echo of it before
hook = [[76, None, 74, 76, None, 72, None, 74], [72, None, 69, 72, None, 74, None, 72],
        [72, None, 74, 76, None, 79, None, 76], [74, None, 72, 74, None, 71, None, 67]]
def pluck(m, dur):
    n = int(dur * SR); t = np.arange(n) / SR; f = hz(m)
    x = saw(f, n) + 0.5 * np.sign(np.sin(2 * np.pi * f * 2 * t))
    out = np.zeros(n)
    for i in range(0, n, 1024):  # filter envelope
        c = 500 + 7000 * np.exp(-(i / SR) / 0.08)
        seg = x[i:i + 1024]; out[i:i + len(seg)] = lp(seg, c)
    return out * env(n, 0.002, 0.16) * 0.12
lead = np.zeros((N, 2))
for b in range(nbars):
    t0 = b * bar
    if t0 < drop - 0.01 and t0 + bar <= drop:
        continue
    for k, m in enumerate(hook[b % 4]):
        tk = t0 + k * beat / 2
        if m is None or tk < drop:
            continue
        p = pluck(m, beat * 0.9)
        add(lead, np.stack([p * 0.9, p * 1.1], 1), tk)
        add(lead, np.stack([p * 0.35, p * 0.0], 1), tk + 3 * beat / 4)   # ping-pong echo
        add(lead, np.stack([p * 0.0, p * 0.3], 1), tk + 3 * beat / 2)
music += lead
send += lead * 0.5

music = music + reverb(send, 1.6, 0.35) - send
# master: gentle glue + fades
music = np.tanh(music * 1.3) / 1.3
fi = int(0.3 * SR); music[:fi] *= np.linspace(0, 1, fi)[:, None]
fo = int(1.4 * SR); music[-fo:] *= np.linspace(1, 0, fo)[:, None]

# ---------------- voice + ducking ----------------
vo, vsr = sf.read("vo.wav")
idx = np.arange(int(len(vo) * SR / vsr)) * vsr / SR
vo48 = np.interp(idx, np.arange(len(vo)), vo)
voice = np.zeros(N); voice[: min(N, len(vo48))] = vo48[:N]
voice = hp(voice, 80)
w = int(0.04 * SR)
e = np.convolve(np.abs(voice), np.ones(w) / w, "same") > 0.008
e = np.convolve(e.astype(float), np.ones(int(0.3 * SR)) / int(0.3 * SR), "same")
duck = 1 - 0.45 * np.clip(e * 1.5, 0, 1)
music *= duck[:, None]

# ---------------- SFX ----------------
def s_pop():
    n = int(0.11 * SR); t = np.arange(n) / SR
    f = 320 + 1100 * (1 - np.exp(-t * 60))           # upward "bloop"
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.001, 0.035)
    return (x + hp(rng.standard_normal(n), 4000) * env(n, 0.0003, 0.002) * 0.3) * 0.55

def s_click():
    out = np.zeros(int(0.09 * SR))
    for d, g, f in ((0.0, 1.0, 3200), (0.045, 0.7, 2600)):    # click-clack
        n = int(0.025 * SR); t = np.arange(n) / SR
        x = bp(rng.standard_normal(n), 1500, 7000) * env(n, 0.0002, 0.003)
        x += np.sin(2 * np.pi * f * t) * env(n, 0.0002, 0.006) * 0.5
        add(out, x * g, d)
    return out * 0.8

def s_whoosh():
    n = int(0.42 * SR); t = np.arange(n) / SR
    x = rng.standard_normal(n); out = np.zeros(n)
    for i in range(0, n, 1024):
        u = i / n; c = 500 + 3500 * np.sin(np.pi * u)
        seg = x[i:i + 1024]; out[i:i + len(seg)] = bp(seg, c * 0.6, c * 1.6)
    return out * np.sin(np.pi * t / t[-1]) ** 2 * 0.45

def s_tick(k):
    n = int(0.04 * SR); t = np.arange(n) / SR
    f = 1800 * 2 ** (k / 30)                          # rises as the count climbs
    return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2.7 * f * t)) * env(n, 0.0003, 0.008) * 0.35

def s_cash():
    out = np.zeros(int(1.0 * SR))
    n = int(0.08 * SR); add(out, bp(rng.standard_normal(n), 2000, 9000) * env(n, 0.001, 0.02) * 0.5, 0)  # "cha"
    for d, f in ((0.07, 2093), (0.13, 2637)):         # "ching"
        n = int(0.8 * SR); t = np.arange(n) / SR
        x = sum(np.sin(2 * np.pi * f * h * t) / h for h in (1, 2.76, 5.4)) * env(n, 0.001, 0.25)
        add(out, x * 0.3, d)
    return out

def s_ding():
    n = int(0.7 * SR); t = np.arange(n) / SR
    return sum(np.sin(2 * np.pi * 1568 * h * t) / h for h in (1, 2.4, 4.1)) * env(n, 0.001, 0.22) * 0.22

def s_impact():
    n = int(0.9 * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * np.cumsum(38 + 100 * np.exp(-t * 14)) / SR) * env(n, 0.001, 0.3)
    x += lp(rng.standard_normal(n), 2500) * env(n, 0.001, 0.05) * 0.5
    return np.tanh(x * 1.5) * 0.6

def s_type():
    out = np.zeros(int(1.4 * SR))
    for j in range(16):
        n = int(0.03 * SR)
        x = bp(rng.standard_normal(n), 1200, 5000) * env(n, 0.0003, 0.005) * rng.uniform(0.25, 0.4)
        add(out, x, j * 0.075 + rng.uniform(0, 0.025))
    return out

fx = np.zeros((N, 2))
ticks = 0
for ev in sfx:
    k, at = ev["k"], ev["t"]
    if k == "tick":
        x = s_tick(ticks); ticks += 1
    else:
        x = {"pop": s_pop, "click": s_click, "whoosh": s_whoosh, "cash": s_cash,
             "ding": s_ding, "impact": s_impact, "type": s_type}[k]()
    add(fx, x, at)
fx = reverb(fx, 0.6, 0.12)

rv=lambda a: 20*np.log10(np.sqrt(np.mean(a**2))+1e-9)
sl=slice(int(L[4]["start"]*SR),int(L[4]["end"]*SR))
print("voice dB",round(rv(voice[sl]),1),"music-under-voice dB",round(rv(music[sl,0]*0.15),1),"music-after-drop-open dB",round(rv(music[int((L[7]["end"]+.1)*SR):int((L[7]["end"]+.6)*SR),0]*0.15),1))
mix = np.stack([voice, voice], 1) * 1.0 + music * 0.15 + fx * 0.5
mix /= max(1e-9, np.abs(mix).max()) / 0.9
sf.write("mix.wav", mix.astype(np.float32), SR)
print("mix.wav", round(T, 2), "s, sfx events:", len(sfx), "ticks:", ticks)
