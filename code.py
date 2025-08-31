# code.py
import os
import re
import io
import json
import math
from PIL import Image
from pathlib import Path
from typing import List, Tuple
from moviepy import ColorClip, vfx
from dotenv import load_dotenv
from pydub import AudioSegment
from pydub.utils import which
from moviepy import AudioFileClip, ImageClip, CompositeVideoClip
from moviepy import ColorClip 

# Ensure PyDub uses Homebrew ffmpeg (macOS) or system ffmpeg
AudioSegment.converter = which("ffmpeg")

# ========== CONFIG ==========
OUTPUT_DIR = Path("task06_output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SCRIPT_PATH = Path("Interview_script.md")           # Preferred script if present
NARRATIVE_PATH = Path("task05_narrative.txt")       # Fallback: Task 05 narrative text
BACKGROUND_IMAGE = Path("background.jpg")           # Optional; if missing, video step is skipped

INTERVIEW_TXT   = OUTPUT_DIR / "interview_script.md"
AUDIO_MP3       = OUTPUT_DIR / "deepfake_interview.mp3"
VIDEO_MP4       = OUTPUT_DIR / "deepfake_interview.mp4"

# OpenAI models
TEXT_MODEL = "gpt-4o-mini"
TTS_MODEL  = "gpt-4o-mini-tts"

# Voices exposed by your account (change if needed)
INTERVIEWER_VOICE = "alloy"
EXPERT_VOICE      = "verse"

# ========== HELPERS ==========

def ensure_openai():
    """Create an OpenAI client using API key from .env or environment."""
    load_dotenv()
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("Set OPENAI_API_KEY in a .env file or environment.")
    from openai import OpenAI
    return OpenAI(api_key=key)

def read_narrative() -> str:
    """Read Task 05 narrative text (only used if no script is provided)."""
    if NARRATIVE_PATH.exists():
        return NARRATIVE_PATH.read_text(encoding="utf-8").strip()
    return "PASTE YOUR TASK 05 NARRATIVE HERE if you don't want to read from file."

def call_llm_for_interview(narrative: str, minutes: int = 2) -> str:
    """Generate an interview script from the narrative using the LLM."""
    client = ensure_openai()

    sys = (
        "You are a helpful editor. Convert the provided narrative into a realistic, "
        "concise interview transcript usable for audio synthesis. Use alternating lines "
        "with speakers exactly labeled as 'Interviewer:' and 'Expert:'. Keep it natural, "
        f"~{minutes}-3 minutes when spoken, ~10-14 turns total. Avoid long paragraphs; 1-2 sentences per turn."
    )
    user = f"""Narrative (source):
{narrative}

Constraints:
- Keep it accurate to the source narrative (no hallucinations).
- Avoid numbers you cannot infer; speak qualitatively if needed.
- Start directly with dialogue, no intro/outro headers."""

    resp = client.chat.completions.create(
        model=TEXT_MODEL,
        messages=[{"role": "system", "content": sys},
                  {"role": "user", "content": user}],
        temperature=0.6,
    )
    script = resp.choices[0].message.content.strip()
    INTERVIEW_TXT.write_text(script, encoding="utf-8")
    return script

def get_script_text(narrative: str) -> str:
    """Use user-provided Interview_script.md if present; else reuse output; else generate."""
    if SCRIPT_PATH.exists():
        txt = SCRIPT_PATH.read_text(encoding="utf-8").strip()
        INTERVIEW_TXT.write_text(txt, encoding="utf-8")  # copy for tracking
        print(f"Using existing script: {SCRIPT_PATH}")
        return txt

    if INTERVIEW_TXT.exists():
        print(f"Using existing script: {INTERVIEW_TXT}")
        return INTERVIEW_TXT.read_text(encoding="utf-8").strip()

    print("No script found; generating from narrative...")
    return call_llm_for_interview(narrative, minutes=2)

def parse_dialogue(script_md: str) -> List[Tuple[str, str]]:
    """
    Parse lines like 'Interviewer: ...' or 'Expert: ...'
    Also accepts bold markdown labels like '**Interviewer:**'.
    """
    lines = [ln.strip() for ln in script_md.splitlines() if ln.strip()]
    dialogue = []
    pattern = re.compile(r"^\s*\*{0,2}(Interviewer|Expert)\*{0,2}\s*:\s*(.+)$", re.IGNORECASE)

    for ln in lines:
        m = pattern.match(ln)
        if m:
            speaker = "Interviewer" if m.group(1).lower().startswith("interviewer") else "Expert"
            text = m.group(2).strip()
            dialogue.append((speaker, text))

    if not dialogue:
        raise ValueError(
            "Could not parse any 'Interviewer:' / 'Expert:' lines from the script. "
            "Tip: ensure each line starts with 'Interviewer:' or 'Expert:' (bold **...** is ok)."
        )
    return dialogue

def synthesize_dual_voice_audio(dialogue: List[Tuple[str, str]], out_path: Path) -> Path:
    """
    Alternate voices by speaker label and concatenate to one MP3.
    """
    client = ensure_openai()

    master = AudioSegment.silent(duration=200)
    spacer = AudioSegment.silent(duration=250)

    for speaker, line in dialogue:
        voice = INTERVIEWER_VOICE if speaker == "Interviewer" else EXPERT_VOICE

        # New SDK: response_format + iter_bytes()
        audio_response = client.audio.speech.create(
            model=TTS_MODEL,
            voice=voice,
            input=line,
            response_format="mp3",
        )
        raw = b"".join(audio_response.iter_bytes())
        seg = AudioSegment.from_file(io.BytesIO(raw), format="mp3")

        master += seg + spacer

    master.export(out_path, format="mp3")
    return out_path

def render_video_simple(audio_path: Path, bg_image: Path, out_path: Path) -> Path:
    """
    Minimal static video with audio (v2-safe).
    Uses Pillow to letterbox the background to 1920x1080, then builds the video.
    """
    audio_clip = AudioFileClip(str(audio_path))
    duration = audio_clip.duration

    target_w, target_h = 1920, 1080
    tmp_img_path = OUTPUT_DIR / "_bg_resized_1920x1080.jpg"

    if bg_image.exists():
        # Letterbox the image to 1920x1080 with black bars (no ImageMagick needed)
        img = Image.open(bg_image).convert("RGB")
        src_w, src_h = img.size
        scale = min(target_w / src_w, target_h / src_h)
        new_w, new_h = int(src_w * scale), int(src_h * scale)
        img_resized = img.resize((new_w, new_h), Image.LANCZOS)

        canvas = Image.new("RGB", (target_w, target_h), (12, 12, 16))  # dark background
        offset = ((target_w - new_w) // 2, (target_h - new_h) // 2)
        canvas.paste(img_resized, offset)
        canvas.save(tmp_img_path, quality=95)

        clip = ImageClip(str(tmp_img_path), duration=duration)
        video = CompositeVideoClip([clip])
    else:
        # Fallback: solid background
        bg = ColorClip(size=(target_w, target_h), color=(12, 12, 16), duration=duration)
        video = CompositeVideoClip([bg])

    # Attach audio
    try:
        video = video.set_audio(audio_clip)
    except AttributeError:
        video = video.with_audio(audio_clip)

    video.write_videofile(str(out_path), fps=30, codec="libx264", audio_codec="aac")

    # Cleanup temp image
    try:
        if tmp_img_path.exists():
            tmp_img_path.unlink()
    except:
        pass

    return out_path

# ========== MAIN PIPELINE ==========

def main():
    narrative = read_narrative()
    script_md = get_script_text(narrative)

    print("Parsing dialogue...")
    dialogue = parse_dialogue(script_md)

    print("Synthesizing dual-voice audio...")
    audio_path = synthesize_dual_voice_audio(dialogue, AUDIO_MP3)
    print(f"Audio saved: {audio_path}")

    if BACKGROUND_IMAGE.exists():
        print("Rendering simple video...")
        render_video_simple(audio_path, BACKGROUND_IMAGE, VIDEO_MP4)
        print(f"Video saved: {VIDEO_MP4}")
    else:
        print("No background image provided. Skipping video render.")

if __name__ == "__main__":
    main()
