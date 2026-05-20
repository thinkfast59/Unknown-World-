import os
import random
import textwrap
import math
import requests
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import *
from moviepy.audio.AudioClip import AudioClip

# Fix for MoviePy + newer Pillow
if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

W, H = 1080, 1920
DURATION = 24

FULL_PAGE_NAME = "Unknown World | නොදන්නා ලෝකය"

BASE = Path(__file__).parent
OUTPUT = BASE / "output"
OUTPUT.mkdir(exist_ok=True)

PIXABAY_KEY = os.getenv("55948311-d474f36a1e037982880d2f139", "")
PEXELS_KEY = os.getenv("mmN5PuJPe4qSOn06yXutlRjITFCv1OltnBH85iu1H3KFKQM7QzHtApF2", "")

STORIES = [
    {
        "hook": "මේ ගෙදරට රෑ 12න් පස්සේ කවුරුත් යන්නේ නෑ...",
        "body": "ගමේ මිනිස්සු කියන්නේ හැම රෑම උඩ මාලයෙන් අමුතු ශබ්ද ඇහෙනවා කියලා.",
        "end": "ඔයා මෙතනට තනියම යයිද?"
    },
    {
        "hook": "CCTV එකට අහුවුණු අමුතුම දර්ශනයක්...",
        "body": "මුලින් කිසිම දෙයක් පේන්නෙ නෑ. ඒත් හොඳට බලද්දී පිටිපස්සේ සෙවණැල්ලක් චලනය වෙනවා.",
        "end": "ඔයාටත් ඒක පේනවද?"
    },
    {
        "hook": "මේ කැලේ ඇතුළට ගිය අය ආයෙත් ආවේ නෑ කියනවා...",
        "body": "රෑ වෙද්දී අමුතු හඬවල් ඇහෙනවා කියලා ගමේ අය අදටත් කියනවා.",
        "end": "මේක ඇත්තද?"
    },
    {
        "hook": "රෑ 3ට මේ පාරෙන් යන්න කවුරුත් කැමති නෑ...",
        "body": "සුදු ඇඳුම් ඇඳපු කෙනෙක් පාර අයිනේ හිටගෙන ඉන්නවා කියලා ගමේ අය කියනවා.",
        "end": "ඔයා මෙහෙම කතාවක් අහලා තියෙනවද?"
    },
    {
        "hook": "පරණ පාසලේ ජනේලය රෑට තනියම ඇරෙනවා කියනවා...",
        "body": "කාමරේ ඇතුළේ කවුරුත් නැති වෙලාවටත් පුටු ඇදෙන ශබ්දයක් ඇහෙනවා කියලා කියනවා.",
        "end": "මේක අභිරහසක්ද?"
    }
]

VIDEO_KEYWORDS = [
    "dark forest",
    "abandoned house",
    "scary hallway",
    "fog night",
    "rain night",
    "dark road",
    "moon night",
    "creepy house"
]

def font_path():
    paths = [
        "/usr/share/fonts/truetype/noto/NotoSansSinhala-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansSinhala-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSerifSinhala-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSerifSinhala-Regular.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    return None

FONT = font_path()

def download_file(url, path):
    r = requests.get(url, timeout=45)
    r.raise_for_status()
    path.write_bytes(r.content)
    return path

def get_pixabay_video():
    if not PIXABAY_KEY:
        return None

    q = random.choice(VIDEO_KEYWORDS)
    url = "https://pixabay.com/api/videos/"
    params = {
        "key": PIXABAY_KEY,
        "q": q,
        "orientation": "vertical",
        "per_page": 30,
        "safesearch": "true"
    }

    data = requests.get(url, params=params, timeout=30).json()
    hits = data.get("hits", [])
    if not hits:
        return None

    item = random.choice(hits)
    videos = item.get("videos", {})
    video_url = (
        videos.get("large", {}).get("url")
        or videos.get("medium", {}).get("url")
        or videos.get("small", {}).get("url")
    )

    if not video_url:
        return None

    return download_file(video_url, OUTPUT / "background.mp4")

def get_pexels_video():
    if not PEXELS_KEY:
        return None

    q = random.choice(VIDEO_KEYWORDS)
    url = "https://api.pexels.com/videos/search"
    headers = {"Authorization": PEXELS_KEY}
    params = {
        "query": q,
        "orientation": "portrait",
        "per_page": 15
    }

    data = requests.get(url, headers=headers, params=params, timeout=30).json()
    videos = data.get("videos", [])
    if not videos:
        return None

    item = random.choice(videos)
    files = sorted(
        item.get("video_files", []),
        key=lambda x: x.get("width", 0),
        reverse=True
    )

    if not files:
        return None

    return download_file(files[0]["link"], OUTPUT / "background.mp4")

def make_generated_horror_background():
    frames = []

    for frame in range(DURATION * 30):
        img = Image.new("RGB", (W, H), (3, 3, 8))
        draw = ImageDraw.Draw(img)

        # dark gradient
        for y in range(0, H, 24):
            shade = int(5 + (y / H) * 45)
            draw.rectangle(
                (0, y, W, y + 24),
                fill=(shade // 3, shade // 3, shade)
            )

        # moon
        mx = 800 + int(math.sin(frame / 60) * 15)
        my = 240
        draw.ellipse((mx, my, mx + 150, my + 150), fill=(150, 150, 165))

        # fog
        for i in range(8):
            fy = 880 + i * 90 + int(math.sin(frame / 20 + i) * 18)
            draw.rectangle((0, fy, W, fy + 22), fill=(28, 28, 38))

        # shadow figure
        x = 530 + int(math.sin(frame / 25) * 25)
        draw.ellipse((x - 45, 980, x + 45, 1080), fill=(0, 0, 0))
        draw.rectangle((x - 35, 1060, x + 35, 1320), fill=(0, 0, 0))

        # ground
        draw.rectangle((0, 1450, W, H), fill=(2, 2, 5))

        # lightning flash
        if frame % 160 in [0, 1, 2]:
            draw.rectangle((0, 0, W, H), fill=(110, 110, 130))

        frames.append(np.array(img))

    return ImageSequenceClip(frames, fps=30).set_duration(DURATION)

def make_text_png(story):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if FONT:
        title_font = ImageFont.truetype(FONT, 72)
        body_font = ImageFont.truetype(FONT, 56)
        small_font = ImageFont.truetype(FONT, 42)
        brand_font = ImageFont.truetype(FONT, 38)
    else:
        title_font = ImageFont.load_default()
        body_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
        brand_font = ImageFont.load_default()

    def center_text(text, y, font, fill, width):
        lines = []
        for part in text.split("\n"):
            lines.extend(textwrap.wrap(part, width=width))

        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            tw = bbox[2] - bbox[0]
            x = (W - tw) // 2

            # shadow
            draw.text((x + 5, y + 5), line, font=font, fill=(0, 0, 0, 235))
            # red glow
            draw.text((x + 2, y + 2), line, font=font, fill=(120, 0, 0, 170))
            # main
            draw.text((x, y), line, font=font, fill=fill)

            y += int(font.size * 1.35) if hasattr(font, "size") else 60

        return y

    center_text(FULL_PAGE_NAME, 80, brand_font, (255, 80, 80, 255), 28)
    center_text("⚠️ භයානක අභිරහසක්", 250, small_font, (255, 255, 255, 255), 22)

    y = 560
    y = center_text(story["hook"], y, title_font, (255, 255, 255, 255), 15)

    y += 90
    center_text(story["body"], y, body_font, (235, 235, 235, 255), 17)

    center_text(story["end"], 1570, small_font, (255, 80, 80, 255), 20)
    center_text("@Unknown World", 1760, brand_font, (180, 180, 180, 220), 25)

    path = OUTPUT / "text.png"
    img.save(path)
    return path

def generated_horror_audio():
    def make_sound(t):
        base = 0.10 * np.sin(2 * np.pi * 55 * t)
        pulse = 0.07 * np.sin(2 * np.pi * 0.7 * t)
        rumble = 0.04 * np.sin(2 * np.pi * 90 * t)
        return base + pulse + rumble

    return AudioClip(make_sound, duration=DURATION, fps=44100).volumex(0.45)

def prepare_background():
    video_path = None

    try:
        video_path = get_pixabay_video()
        if video_path:
            print("Using Pixabay video")
    except Exception as e:
        print("Pixabay failed:", e)

    if not video_path:
        try:
            video_path = get_pexels_video()
            if video_path:
                print("Using Pexels video")
        except Exception as e:
            print("Pexels failed:", e)

    if video_path:
        bg = VideoFileClip(str(video_path))
        bg = bg.resize(height=H)
        bg = bg.crop(
            x_center=bg.w / 2,
            y_center=bg.h / 2,
            width=W,
            height=H
        )

        if bg.duration > DURATION:
            start = random.uniform(0, max(0, bg.duration - DURATION))
            bg = bg.subclip(start, start + DURATION)
        else:
            bg = bg.loop(duration=DURATION)

        return bg

    print("No outside video found. Creating Python horror background.")
    return make_generated_horror_background()

def create_reel():
    story = random.choice(STORIES)

    bg = prepare_background()

    dark = ColorClip((W, H), color=(0, 0, 0), duration=DURATION).set_opacity(0.45)
    red = ColorClip((W, H), color=(60, 0, 0), duration=DURATION).set_opacity(0.12)

    text = ImageClip(str(make_text_png(story))).set_duration(DURATION)

    final = CompositeVideoClip([bg, dark, red, text], size=(W, H))
    final = final.set_duration(DURATION)
    final = final.set_audio(generated_horror_audio())

    out = OUTPUT / "unknown_world_reel.mp4"

    final.write_videofile(
        str(out),
        fps=30,
        codec="libx264",
        audio_codec="aac",
        threads=2,
        preset="medium"
    )

    caption = f"""🌍 {FULL_PAGE_NAME}

{story['hook']}

{story['body']}

{story['end']}

#UnknownWorld #නොදන්නාලෝකය #SinhalaHorror #MysterySinhala #HorrorReels #SinhalaReels"""

    (OUTPUT / "caption.txt").write_text(caption, encoding="utf-8")

    print("DONE:", out)
    print("Caption saved:", OUTPUT / "caption.txt")

if __name__ == "__main__":
    create_reel()
