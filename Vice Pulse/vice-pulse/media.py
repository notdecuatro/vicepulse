"""Frame composition shared by the offline fixture and the FFmpeg worker."""
import math
import os
import re
import subprocess
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

SIZE = (1080, 1920)
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


def overlay(frame, caption, logo, disclosure, call_to_action=None):
    frame = ImageOps.fit(frame.convert("RGB"), SIZE)
    annotations = Image.new('RGBA', (720, 1280))
    d = ImageDraw.Draw(annotations)
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
    if call_to_action:
        cta_font = font(25)
        width = d.textlength(call_to_action, font=cta_font)
        center = 340
        d.rounded_rectangle((center - width / 2 - 14, 944, center + width / 2 + 14, 990),
                            8, fill=(15, 19, 29))
        d.text((center, 967), call_to_action, font=cta_font, anchor="mm", fill="white")
    if logo:
        annotations.paste(logo, (720-logo.width-33, 1280-logo.height-55), logo)
    frame.paste(annotations.resize(SIZE, Image.Resampling.LANCZOS), (0, 0),
                annotations.resize(SIZE, Image.Resampling.LANCZOS))
    return frame


def caption_at(groups, when):
    for start, end, text in groups:
        if start <= when < end:
            return text
    return ""


def captions(segments, *, start=float('-inf'), end=float('inf')):
    groups = []
    for s in segments:
        if s.get("words"):
            words, size = s['words'], 3
        else:
            text = s['text'].strip().split()
            words = [{'start':s['start']+(s['end']-s['start'])*i/len(text),
                      'end':s['start']+(s['end']-s['start'])*(i+1)/len(text),
                      'word':word} for i,word in enumerate(text)]
            size = 5
        words = [w for w in words if w['start'] >= start and w['end'] <= end]
        for idx in range(0, len(words), size):
            chunk = words[idx:idx+size]
            groups.append((chunk[0]['start'], chunk[-1]['end'],
                           ' '.join(w['word'].strip() for w in chunk)))
    return groups


def render(source, start, end, segments, logo_file, disclosure, output, *, call_to_action=None,
           layout=None, hook=None, brand_overlay=None):
    duration = end - start
    if duration <= 0:
        raise ValueError("El final del corte debe seguir al inicio.")
    audio = subprocess.run(["ffmpeg","-nostdin","-v","info","-ss",str(start),"-i",str(source),
                            "-t",str(duration),"-vn","-af","volumedetect","-f","null","-"],
                           capture_output=True,text=True,check=True)
    volume = re.search(r"mean_volume: ([-\w.]+) dB",audio.stderr)
    if volume is None or float(volume.group(1)) < -50:
        raise ValueError("La fuente no tiene audio audible en el corte seleccionado.")
    size = SIZE
    split_layout = bool(layout and 'face_crop' in layout and 'game_crop' in layout)
    if split_layout:
        x,y,w,h = layout["face_crop"]
        gx,gy,gw,gh = layout["game_crop"]
        graph = (f"[0:v]fps=30,split=2[face][game];"
                 f"[face]crop={w}:{h}:{x}:{y},scale=1080:540:force_original_aspect_ratio=increase,"
                 "crop=1080:540[cam];"
                 f"[game]crop={gw}:{gh}:{gx}:{gy},scale=1080:1380:force_original_aspect_ratio=increase,"
                 "crop=1080:1380[play];"
                 "[cam][play]vstack=inputs=2,setsar=1[out]")
        decode = ["ffmpeg","-nostdin","-loglevel","error","-ss",str(start),"-i",str(source),
                  "-t",str(duration),"-filter_complex",graph,"-map","[out]",
                  "-f","rawvideo","-pix_fmt","rgb24","-"]
    else:
        graph = ("[0:v]fps=30,split=2[bg][fg];"
                 "[bg]scale=1080:1920:force_original_aspect_ratio=increase,"
                 "crop=1080:1920,gblur=sigma=24[background];"
                 "[fg]scale=1080:1920:force_original_aspect_ratio=decrease[foreground];"
                 "[background][foreground]overlay=(W-w)/2:(H-h)/2,setsar=1[out]")
        decode = ["ffmpeg","-nostdin","-loglevel","error","-ss",str(start),"-i",str(source),
                  "-t",str(duration),"-filter_complex",graph,"-map","[out]",
                  "-f","rawvideo","-pix_fmt","rgb24","-"]
    encode = ["ffmpeg","-nostdin","-loglevel","error","-y","-f","rawvideo","-pix_fmt","rgb24",
              "-s",f"{size[0]}x{size[1]}","-r","30","-i","-","-ss",str(start),"-i",str(source),
              "-map","0:v:0","-map","1:a:0","-t",str(duration),"-c:v","libx264","-preset","slow",
              "-crf","18","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-af","loudnorm=I=-16:TP=-1.5:LRA=11","-movflags","+faststart"]
    logo = Image.open(logo_file).convert("RGBA") if logo_file else None
    if logo:
        logo.thumbnail((145, 145))
    banner = Image.open(brand_overlay).convert("RGBA") if brand_overlay else None
    if banner:
        banner.thumbnail((650, 180), Image.Resampling.LANCZOS)
    groups = captions([s for s in segments if s["end"]>start and s["start"]<end], start=start, end=end)
    temp = output.with_suffix(".part.mp4")
    frame_size = math.prod(size)*3
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
                        img = Image.frombytes("RGB", size, raw)
                        when = start + count / FPS
                        text = caption_at(groups, when)
                        cta = call_to_action if when >= end - 3 else None
                        if split_layout:
                            draw = ImageDraw.Draw(img)
                            draw.text((55, 38), disclosure, font=font(26), fill="white",
                                      stroke_width=2, stroke_fill="black")
                            if banner:
                                img.paste(banner, (55, 540), banner)
                            labels = [(text, 930, 'white', 60)]
                            if hook and count / FPS < 2.5:
                                labels.insert(0, (hook, 720, '#FFE65C', 54))
                            for label, baseline, color, font_size in labels:
                                if not label:
                                    continue
                                words = label.upper().split()
                                lines = []
                                for word in words:
                                    if lines and draw.textlength(lines[-1]+" "+word,font=font(font_size)) < 880:
                                        lines[-1] += " " + word
                                    else:
                                        lines.append(word)
                                for i,line in enumerate(lines):
                                    draw.text((510, baseline+i*76),line,font=font(font_size),anchor="mm",
                                              fill=color,
                                              stroke_width=6,stroke_fill="black")
                            if cta:
                                draw.text((510,1580),cta,font=font(32),anchor="mm",fill="white",
                                          stroke_width=3,stroke_fill="black")
                            writer.stdin.write(img.tobytes())
                        else:
                            label = hook if hook and count/FPS < 2.5 else text
                            writer.stdin.write(overlay(img, label, logo, disclosure, cta).tobytes())
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

