"""Render a reviewed edit plan without publishing or changing campaign permissions."""
import argparse
import json
import subprocess
import tempfile
from pathlib import Path

from media import render
from quality import require_export

ROOT = Path(__file__).resolve().parent


def run(plan_path):
    plan = json.loads(plan_path.read_text())
    transcript = json.loads((ROOT / plan['transcript']).read_text())
    output = ROOT / plan['output']
    output.parent.mkdir(parents=True, exist_ok=True)
    ranges = plan['ranges'] if 'ranges' in plan else [[plan['start'], plan['end']]]
    if not ranges or any(start < 0 or end <= start for start, end in ranges):
        raise ValueError('El plan contiene cortes inválidos.')
    with tempfile.TemporaryDirectory(dir=output.parent) as directory:
        folder = Path(directory)
        parts = []
        for index, (start, end) in enumerate(ranges):
            part = folder / f'part-{index}.mp4'
            render(ROOT / plan['source'], start, end, transcript['segments'], None,
                   plan.get('disclosure', 'Ad'), part, layout=plan.get('layout'),
                   hook=plan.get('hook') if index == 0 else None,
                   brand_overlay=ROOT / plan['brand_overlay'] if plan.get('brand_overlay') else None,
                   call_to_action=plan.get('call_to_action')
                   if index == len(ranges)-1 else None)
            parts.append(part)
        listing = folder / 'concat.txt'
        listing.write_text(''.join(f"file '{part.name}'\n" for part in parts))
        staging = folder / 'final.mp4'
        subprocess.run(['ffmpeg','-v','error','-nostdin','-y','-f','concat','-safe','0',
                        '-i',str(listing),'-c','copy','-movflags','+faststart',str(staging)],check=True)
        report = require_export(staging)
        staging.replace(output)
        report['file'] = str(output.relative_to(ROOT))
        output.with_suffix('.quality.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False))
    print(output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan', type=Path)
    run(parser.parse_args().plan.resolve())
