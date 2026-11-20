"""Generate voice-over per line with Kokoro, write vo.wav + timing.json."""
import json
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

# (spoken text, caption text)
LINES = [
    ("An AI just found a critical bug in one of the most used programming languages on Earth.",
     "An AI just found a CRITICAL bug in one of the most used programming languages on Earth."),
    ("And it took about one hour.", "And it took about ONE HOUR."),
    ("Banks, big companies, and millions of servers run on this language.",
     "Banks, big companies, and millions of servers run on this language."),
    ("It's Java.", "It's JAVA."),
    ("Researchers named it Java Four Shell. A memory bug in Java's Base sixty four decoder, that could let an attacker run code on a server, with no password.",
     "Researchers named it JAVA4SHELL. A memory bug in Java's Base64 decoder, that could let an attacker run code on a server, with NO PASSWORD."),
    ("The AI was OpenAI's Codex. And the whole hunt cost under two hundred dollars.",
     "The AI was OpenAI's CODEX. And the whole hunt cost under $200."),
    ("It only affects newer Intel and AMD chips, and the fix is already out.",
     "It only affects newer Intel and AMD chips, and the FIX is already out."),
    ("So if you run Java, update it today. Comment link for the full report, and subscribe to Study with Ayaz!",
     "So if you run Java, UPDATE it today. Comment LINK for the full report, and subscribe to Study with Ayaz!"),
]
GAP = 0.28  # pause between lines (s)
SR = 24000

k = Kokoro("models/kokoro-v1.0.onnx", "models/voices-v1.0.bin")
chunks, timing, t = [], [], 0.35
chunks.append(np.zeros(int(0.35 * SR), dtype=np.float32))
for spoken, cap in LINES:
    if "Ayaz" in spoken:
        ph = k.tokenizer.phonemize(spoken, "en-us").replace("ˈaɪæz", "ɐjˈɑːz")
        audio, sr = k.create(ph, voice="af_heart", speed=1.15, is_phonemes=True)
    else:
        audio, sr = k.create(spoken, voice="af_heart", speed=1.15, lang="en-us")
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
