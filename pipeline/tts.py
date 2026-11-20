"""Generate voice-over per line with Kokoro, write vo.wav + timing.json."""
import json
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

# (spoken text, caption text)
LINES = [
    ("This portfolio builds itself, right in front of you.",
     "This portfolio BUILDS ITSELF, right in front of you."),
    ("And it's just one HTML file. No React. No framework.",
     "And it's just ONE HTML file. No React. No framework."),
    ("Here's how it looks on a phone. Dark mode, and an animated server log.",
     "Here's how it looks on a phone. DARK MODE, and an animated server log."),
    ("A flagship project with an interactive pipeline, and every project linked to its code.",
     "A FLAGSHIP project with an interactive pipeline, and every project linked to its CODE."),
    ("Want the same one? Ayaz put the full code on GitHub, for free.",
     "Want the same one? Ayaz put the full code on GITHUB, for FREE."),
    ("Fork the repo, and change the name, projects, and links to yours.",
     "FORK the repo, and change the name, projects, and links to YOURS."),
    ("Then turn on GitHub Pages, and your portfolio is live. Free hosting.",
     "Then turn on GitHub PAGES, and your portfolio is LIVE. Free hosting."),
    ("Comment portfolio, and I'll send you the repo. And subscribe to Study with Ayaz!",
     "Comment PORTFOLIO, and I'll send you the repo. And subscribe to Study with Ayaz!"),
]
GAP = 0.45  # pause between lines (s)
SR = 24000

k = Kokoro("models/kokoro-v1.0.onnx", "models/voices-v1.0.bin")
chunks, timing, t = [], [], 0.35
chunks.append(np.zeros(int(0.35 * SR), dtype=np.float32))
for spoken, cap in LINES:
    if "Ayaz" in spoken:
        ph = k.tokenizer.phonemize(spoken, "en-us").replace("ˈaɪæz", "ɐjˈɑːz")
        audio, sr = k.create(ph, voice="af_heart", speed=0.92, is_phonemes=True)
    else:
        audio, sr = k.create(spoken, voice="af_heart", speed=0.92, lang="en-us")
    assert sr == SR
    # trim leading/trailing silence
    idx = np.where(np.abs(audio) > 0.01)[0]
    audio = audio[max(idx[0] - 240, 0): idx[-1] + 480]
    dur = len(audio) / SR
    timing.append({"start": round(t, 3), "end": round(t + dur, 3), "caption": cap})
    chunks += [audio.astype(np.float32), np.zeros(int(GAP * SR), dtype=np.float32)]
    t += dur + GAP
vo = np.concatenate(chunks)
sf.write("vo.wav", vo, SR)
json.dump({"lines": timing, "total": round(len(vo) / SR + 0.9, 3)}, open("timing.json", "w"), indent=1)
print(json.dumps(timing, indent=1), len(vo) / SR)
