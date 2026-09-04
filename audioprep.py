"""
audioprep.py  --  turn whatever ffmpeg can decode into small, ASR-ready audio.

Marko's ask: the file picker should accept anything ffmpeg can process --
every audio format, every video format -- and this module should find the
audio, strip everything else, and land on a size that neither starves the
transcription engine nor pays for bytes it does not need.

THE TARGET, and why it is this one:

    16 kHz, mono, Opus, ~32 kbps VBR, "voip" tuning

AssemblyAI resamples everything to 16 kHz internally regardless of what is
sent, so sending 16 kHz already matches their own pipeline -- a higher rate
buys nothing, it only pays for bytes that get thrown away downstream. Mono
is the same argument for channels: a single spoken voice has no stereo
information worth the second channel's bytes.

Opus at 32 kbps, tuned for voip rather than music, is the codec speech
codecs are actually built for: it is what carries a phone call or a Discord
voice channel at a bitrate MP3 cannot approach without audible artefacts.
Going lower (16-24 kbps) starts to cost intelligibility on noisier
recordings; going higher (64 kbps+) is the overhead half of the ask, paying
for fidelity a transcription model never uses. 32 kbps sits in the middle of
where every speech codec comparison puts the "transparent enough to
transcribe, small enough to matter" range.

A ONE-HOUR VIDEO IN, ONE-HOUR VOICE MEMO OUT: a two-hour 1080p phone video
(gigabytes) becomes a same-length mono Opus file typically under 20 MB.
That is the whole point of doing this server-side rather than uploading the
original to a phone's AssemblyAI ring.
"""

import os
import shutil
import subprocess
import tempfile
import time

FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")

# tuned for speech, not music -- see the module docstring for why these
TARGET_RATE = 16000
TARGET_CHANNELS = 1
TARGET_BITRATE = "32k"
TARGET_CODEC = "libopus"

# a local conversion of a multi-hour recording still finishes in seconds to
# low minutes; this is a backstop against a corrupt file that hangs ffmpeg,
# not a limit anyone doing ordinary work should ever hit
TIMEOUT_SECONDS = 900

MAX_UPLOAD_BYTES = 2 * 1024 * 1024 * 1024   # 2 GB, generous for a phone video


class AudioPrepError(Exception):
    """Raised with a message safe to show directly to the person."""


def available():
    return FFMPEG is not None


def probe_duration(path):
    """Seconds, or None if ffprobe cannot say -- never raises."""
    if not FFPROBE:
        return None
    try:
        out = subprocess.run(
            [FFPROBE, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, timeout=30)
        return float(out.stdout.strip())
    except Exception:
        return None


def optimize(input_bytes, original_name=""):
    """Convert input_bytes (any format ffmpeg can read) to small mono Opus.

    Returns (output_bytes, meta) where meta has the sizes, the duration if
    known, and how long the conversion itself took. Raises AudioPrepError
    with a message meant to be shown as-is if ffmpeg is missing or the
    input cannot be decoded.
    """
    if not available():
        raise AudioPrepError(
            "ffmpeg is not installed on this machine, so the file picker "
            "cannot optimize audio or read video. Install it and restart "
            "transcribe: Termux `pkg install ffmpeg`, macOS `brew install "
            "ffmpeg`, Debian/Ubuntu `apt install ffmpeg`.")

    if len(input_bytes) > MAX_UPLOAD_BYTES:
        raise AudioPrepError(
            f"that file is {len(input_bytes) / 1048576:.0f} MB, over the "
            f"{MAX_UPLOAD_BYTES // 1048576} MB limit for local conversion.")

    # keep the original extension when there is one; ffmpeg mostly probes by
    # content, but a handful of containers (notably raw formats) need the hint
    suffix = os.path.splitext(original_name)[1][:8] if original_name else ""
    if not suffix or any(c in suffix for c in ("/", "\\", "\x00")):
        suffix = ".input"

    workdir = tempfile.mkdtemp(prefix="mahaprep_")
    in_path = os.path.join(workdir, "in" + suffix)
    out_path = os.path.join(workdir, "out.ogg")
    try:
        with open(in_path, "wb") as fh:
            fh.write(input_bytes)

        duration = probe_duration(in_path)

        t0 = time.time()
        proc = subprocess.run(
            [FFMPEG, "-y", "-i", in_path,
             "-vn",                              # audio only, drop any video stream
             "-ac", str(TARGET_CHANNELS),
             "-ar", str(TARGET_RATE),
             "-c:a", TARGET_CODEC,
             "-b:a", TARGET_BITRATE,
             "-application", "voip",             # opus tuned for speech, not music
             "-f", "ogg",
             out_path],
            capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
        took = time.time() - t0

        if proc.returncode != 0 or not os.path.exists(out_path):
            # prefer the line that actually names the problem with the INPUT
            # over whatever generic line happens to be last -- "Invalid
            # data found when processing input" is far more useful than
            # "Error opening output files: Invalid argument", which is what
            # ffmpeg says about the same failure from the far end of the pipe
            lines = [l.strip() for l in (proc.stderr or "").splitlines() if l.strip()]
            reason = next(
                (l for l in reversed(lines)
                 if "invalid data found" in l.lower()
                 or "error opening input" in l.lower()
                 or "does not contain any stream" in l.lower()
                 or "moov atom not found" in l.lower()),
                lines[-1] if lines else "unknown ffmpeg error")
            raise AudioPrepError(
                f"could not read that file as audio or video: {reason}")

        with open(out_path, "rb") as fh:
            out_bytes = fh.read()

        if len(out_bytes) == 0:
            raise AudioPrepError(
                "the conversion produced an empty file -- the source may "
                "have no audio track.")

        return out_bytes, {
            "original_bytes": len(input_bytes),
            "optimized_bytes": len(out_bytes),
            "duration_seconds": duration,
            "convert_seconds": round(took, 2),
        }
    except subprocess.TimeoutExpired:
        raise AudioPrepError(
            f"conversion did not finish within {TIMEOUT_SECONDS}s, the "
            f"file may be corrupt or unusually long.")
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
