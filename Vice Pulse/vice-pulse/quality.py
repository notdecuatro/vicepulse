"""Validate an actual video export before delivery; editorial review is separate."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess


def inspect_export(path, *, require_full_hd=True):
    metadata = json.loads(subprocess.check_output(
        ['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)], text=True))
    video = next((s for s in metadata['streams'] if s['codec_type'] == 'video'), None)
    audio = next((s for s in metadata['streams'] if s['codec_type'] == 'audio'), None)
    if not video or not audio:
        raise ValueError('Falta vídeo o audio en el archivo final.')
    issues = []
    dimensions = [video['width'], video['height']]
    if dimensions[0] * 16 != dimensions[1] * 9:
        issues.append('La proporción final no es 9:16.')
    if require_full_hd and (dimensions[0] < 1080 or dimensions[1] < 1920):
        issues.append('La exportación está por debajo de 1080 × 1920.')
    if video['codec_name'] != 'h264' or audio['codec_name'] != 'aac':
        issues.append('Se esperan H.264 y AAC.')
    duration = float(metadata['format']['duration'])
    if not math.isfinite(duration) or duration <= 0:
        issues.append('Duración inválida.')
    subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-xerror', '-i', str(path),
                    '-map', '0:v:0', '-map', '0:a:0', '-f', 'null', '-'],
                   check=True, capture_output=True)
    result = subprocess.run(['ffmpeg', '-nostdin', '-v', 'info', '-i', str(path), '-vn',
                             '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json',
                             '-f', 'null', '-'], check=True, capture_output=True, text=True)
    matches = re.findall(r'\{\s*"input_i".*?\}', result.stderr, re.S)
    if not matches:
        raise ValueError('No se pudo medir el audio exportado.')
    levels = json.loads(matches[-1])
    loudness, peak = float(levels['input_i']), float(levels['input_tp'])
    if not math.isfinite(loudness) or not -20 <= loudness <= -12:
        issues.append('Volumen fuera del intervalo de revisión de −20 a −12 LUFS.')
    if not math.isfinite(peak) or peak > -1:
        issues.append('El pico real supera −1 dBTP o no es medible.')
    fingerprint = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            fingerprint.update(block)
    return {'file': path.name, 'sha256': fingerprint.hexdigest(), 'duration_seconds': duration,
            'dimensions': dimensions, 'video_codec': video['codec_name'], 'audio_codec': audio['codec_name'],
            'measured_lufs': loudness if math.isfinite(loudness) else None,
            'measured_true_peak_db': peak if math.isfinite(peak) else None,
            'full_decode': True, 'issues': issues, 'technical_pass': not issues,
            'editorial_review': 'Revisar gancho, encuadre, subtítulos, audio escuchado y brief.'}


def require_export(path, *, require_full_hd=True):
    report = inspect_export(path, require_full_hd=require_full_hd)
    if not report['technical_pass']:
        raise ValueError('; '.join(report['issues']))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('video', type=Path)
    args = parser.parse_args()
    report = inspect_export(args.video)
    print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
    raise SystemExit(0 if report['technical_pass'] else 1)
