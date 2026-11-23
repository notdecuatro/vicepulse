"""Frame composition shared by the offline fixture and the FFmpeg worker."""
import math
import os
import subprocess
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

SIZE = (720, 1280)
FPS = 30


@lru_cache(maxsize=12)
def font(size):
    candidates = [os.getenv("VICE_FONT"), "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
                  "DejaVuSans-Bold.ttf"]
    for name in filter(None, candidates):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    raise RuntimeError("Select a TrueType font in VICE_FONT")


def overlay(frame, caption, logo, disclosure):
    frame = ImageOps.fit(frame.convert("RGB"), SIZE)
    d = ImageDraw.Draw(frame)
    d.rounded_rectangle((35, 105, 35 + d.textlength(disclosure, font=font(23)) + 22, 145),
                        8, fill=(15, 19, 29))
    d.text((46, 111), disclosure, font=font(23), fill="white")
    lines = []
    for word in caption.split():
        if lines and d.textlength(lines[-1] + " " + word, font=font(41)) <= 540:
            lines[-1] += " " + word
        else:
            lines.append(word)
    for index, line in enumerate(lines):
        d.text((340, 880 - (len(lines)-1-index)*53), line, font=font(41), anchor="mm",
               fill="white", stroke_width=4, stroke_fill=(13, 17, 25))
    if logo:
        frame.paste(logo, (SIZE[0]-logo.width-33, SIZE[1]-logo.height-55), logo)
    return frame


def caption_at(groups, when):
    for start, end, text in groups:
        if start <= when < end:
            return text
    return ""


def captions(segments):
    groups = []
    for s in segments:
        words = s["text"].strip().split()
        for idx in range(0, len(words), 5):
            begin = s["start"] + (s["end"]-s["start"]) * idx/len(words)
            end = s["start"] + (s["end"]-s["start"]) * min(idx+5,len(words))/len(words)
            groups.append((begin, end, " ".join(words[idx:idx+5])))
    return groups


def render(source, start, end, segments, logo_file, disclosure, output):
    duration = end - start
    scale = "fps=30,scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2,setsar=1"
    decode = ["ffmpeg","-nostdin","-loglevel","error","-ss",str(start),"-i",str(source),
              "-t",str(duration),"-map","0:v:0","-vf",scale,"-f","rawvideo","-pix_fmt","rgb24","-"]
    encode = ["ffmpeg","-nostdin","-loglevel","error","-y","-f","rawvideo","-pix_fmt","rgb24",
              "-s","720x1280","-r","30","-i","-","-ss",str(start),"-i",str(source),
              "-map","0:v:0","-map","1:a:0","-t",str(duration),"-c:v","libx264","-preset","veryfast",
              "-crf","23","-pix_fmt","yuv420p","-c:a","aac","-b:a","112k","-movflags","+faststart"]
    logo = Image.open(logo_file).convert("RGBA") if logo_file else None
    if logo:
        logo.thumbnail((145, 145))
    groups = captions([s for s in segments if s["end"]>start and s["start"]<end])
    temp = output.with_suffix(".part.mp4")
    frame_size = math.prod(SIZE)*3
    try:
        with subprocess.Popen(decode, stdout=subprocess.PIPE) as reader:
            try:
                with subprocess.Popen(encode+[str(temp)], stdin=subprocess.PIPE) as writer:
                    count = 0
                    while True:
                        raw = reader.stdout.read(frame_size)
                        if not raw:
                            break
                        if len(raw) != frame_size:
                            raise ValueError("Incomplete source frame")
                        img = Image.frombytes("RGB", SIZE, raw)
                        text = caption_at(groups, start+count/FPS)
                        writer.stdin.write(overlay(img,text,logo,disclosure).tobytes())
                        count += 1
                    writer.stdin.close()
                    if writer.wait() or reader.wait() or abs(count/FPS-duration) > 0.25:
                        raise ValueError("Incomplete render")
            finally:
                reader.stdout.close()
                if reader.poll() is None:
                    reader.kill()
        subprocess.run(["ffmpeg","-v","error","-xerror","-i",str(temp),"-map","0:v","-map","0:a",
                        "-f","null","-"],check=True)
        temp.replace(output)
    finally:
        temp.unlink(missing_ok=True)

