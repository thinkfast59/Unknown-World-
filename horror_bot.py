import os, random, textwrap, math, requests
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import *
from moviepy.audio.AudioClip import AudioClip

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
        "hook": "මේ කැලේ ඇතුළට ගිය අය ආයෙත් ආවේ නෑ කියනවා...",
        "body": "රෑ වෙද්දී අමුතු හඬවල් ඇහෙනවා කියලා ගමේ අය අදටත් කියනවා.",
        "end": "ඔයා මෙතනට තනියම යයිද?"
    },
    {
        "hook": "CCTV එකට අහුවුණු අමුතුම දර්ශනයක්...",
        "body": "හොඳට බලද්දී පිටිපස්සේ අමුතු සෙවණැල්ලක් චලනය වෙනවා.",
        "end": "ඔයාටත් ඒක පේනවද?"
    },
]

VIDEO_KEYWORDS = ["dark forest", "abandoned house", "fog night", "dark road", "moon night"]

def get_font(paths, size):
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def sinhala_font(size):
    return get_font([
        "/usr/share/fonts/truetype/noto/NotoSansSinhala-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansSinhala-Regular.ttf",
    ], size)

def english_font(size):
    return get_font([
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ], size)

def download_file(url, path):
    r = requests.get(url, timeout=45)
    r.raise_for_status()
    path.write_bytes(r.content)
    return path

def get_pixabay_video():
    if not PIXABAY_KEY:
        return None
    q = random.choice(VIDEO_KEYWORDS)
    data = requests.get(
        "https://pixabay.com/api/videos/",
        params={
            "key": PIXABAY_KEY,
            "q": q,
            "orientation": "vertical",
            "per_page": 20,
            "safesearch": "true"
        },
        timeout=30
    ).json()

    hits = data.get("hits", [])
    if not hits:
        return None

    item = random.choice(hits)
    videos = item.get("videos", {})
    url = videos.get("large", {}).get("url") or videos.get("medium", {}).get("url")
    if not url:
        return None

    return download_file(url, OUTPUT / "background.mp4")

def get_pexels_video():
    if not PEXELS_KEY:
        return None
    q = random.choice(VIDEO_KEYWORDS)
    data = requests.get(
        "https://api.pexels.com/videos/search",
        headers={"Authorization": PEXELS_KEY},
        params={"query": q, "orientation": "portrait", "per_page": 10},
        timeout=30
    ).json()

    videos = data.get("videos", [])
    if not videos:
        return None

    files = random.choice(videos).get("video_files", [])
    files = sorted(files, key=lambda x: x.get("width", 0), reverse=True)
    if not files:
        return None

    return download_file(files[0]["link"], OUTPUT / "background.mp4")

def make_real_fallback_background():
    frames = []
    for frame in range(DURATION * 30):
        img = Image.new("RGB", (W, H), (6, 6, 12))
        draw = ImageDraw.Draw(img)

        # sky gradient
        for y in range(H):
            shade = int(10 + y / H * 35)
            draw.line((0, y, W, y), fill=(shade // 3, shade // 3, shade))

        # moon
        draw.ellipse((760, 180, 930, 350), fill=(170, 170, 185))

        # mountains
        draw.polygon([(0, 1250), (250, 900), (520, 1250)], fill=(8, 8, 12))
        draw.polygon([(350, 1250), (680, 820), (1080, 1250)], fill=(10, 10, 15))

        # trees
        for x in range(0, W, 85):
            h = random.randint(280, 480)
            draw.rectangle((x+30, 1200-h, x+45, 1400), fill=(0, 0, 0))
            draw.polygon([(x, 1200-h+120), (x+38, 1200-h), (x+80, 1200-h+120)], fill=(0, 0, 0))

        # fog
        for i in range(7):
            y = 950 + i * 90 + int(math.sin(frame / 22 + i) * 25)
            draw.rectangle((0, y, W, y + 35), fill=(38, 38, 48))

        # shadow person
        sx = 540 + int(math.sin(frame / 25) * 25)
        draw.ellipse((sx-45, 1120, sx+45, 1210), fill=(0, 0, 0))
        draw.rectangle((sx-35, 1200, sx+35, 1450), fill=(0, 0, 0))

        # lightning flash
        if frame % 170 in [0, 1, 2]:
            draw.rectangle((0, 0, W, H), fill=(120, 120, 145))

        frames.append(np.array(img))

    return ImageSequenceClip(frames, fps=30).set_duration(DURATION)

def draw_center(draw, text, y, font, fill, width):
    lines = []
    for part in text.split("\n"):
        lines.extend(textwrap.wrap(part, width=width))

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        x = (W - tw) // 2
        draw.text((x+5, y+5), line, font=font, fill=(0, 0, 0, 240))
        draw.text((x, y), line, font=font, fill=fill)
        y += int(font.size * 1.35)
    return y

def make_text_png(story):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    brand_en = english_font(42)
    brand_si = sinhala_font(40)
    title = sinhala_font(70)
    body = sinhala_font(54)
    small = sinhala_font(42)

    # brand fixed: English and Sinhala separate
    draw_center(draw, "Unknown World", 70, brand_en, (255, 80, 80, 255), 24)
    draw_center(draw, "නොදන්නා ලෝකය", 125, brand_si, (255, 80, 80, 255), 24)

    draw_center(draw, "⚠ භයානක අභිරහසක්", 260, small, (255, 255, 255, 255), 22)

    y = 590
    y = draw_center(draw, story["hook"], y, title, (255, 255, 255, 255), 14)
    y += 70
    draw_center(draw, story["body"], y, body, (240, 240, 240, 255), 17)

    draw_center(draw, story["end"], 1580, small, (255, 70, 70, 255), 20)
    draw_center(draw, "@Unknown World", 1760, english_font(36), (210, 210, 210, 230), 24)

    path = OUTPUT / "text.png"
    img.save(path)
    return path

def generated_horror_audio():
    def sound(t):
        return (
            0.10 * np.sin(2 * np.pi * 45 * t) +
            0.05 * np.sin(2 * np.pi * 90 * t) +
            0.05 * np.sin(2 * np.pi * 0.8 * t)
        )
    return AudioClip(sound, duration=DURATION, fps=44100).volumex(0.45)

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
        bg = bg.crop(x_center=bg.w/2, y_center=bg.h/2, width=W, height=H)

        if bg.duration > DURATION:
            start = random.uniform(0, bg.duration - DURATION)
            bg = bg.subclip(start, start + DURATION)
        else:
            bg = bg.loop(duration=DURATION)

        return bg.set_duration(DURATION)

    print("No video found. Creating realistic Python horror visual.")
    return make_real_fallback_background()

def create_reel():
    story = random.choice(STORIES)

    bg = prepare_background()

    dark = ColorClip((W, H), color=(0, 0, 0), duration=DURATION).set_opacity(0.32)
    red = ColorClip((W, H), color=(70, 0, 0), duration=DURATION).set_opacity(0.08)
    text = ImageClip(str(make_text_png(story))).set_duration(DURATION)

    final = CompositeVideoClip([bg, dark, red, text], size=(W, H))
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

if __name__ == "__main__":
    create_reel()
