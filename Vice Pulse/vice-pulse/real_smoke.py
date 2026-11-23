"""Exercise the installed ML and production media path with original narration. No publication."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from unittest.mock import patch

import vice
from media import render

def run(audio_file=None):
    for binary in ("ffmpeg", "ffprobe", "ollama"):
        if not shutil.which(binary):
            raise SystemExit("Missing dependency: "+binary)
    narration=("The route begins at the blue checkpoint. I follow the road along the water and wait for the first marker. "
               "Look at the path where it crosses the bridge. The next marker turns orange as I arrive. "
               "The second run takes a different turn. I pass the entrance, watch the line change, and reach the finish. "
               "At the final checkpoint I compare both routes and mark the shortest one. ")
    with tempfile.TemporaryDirectory() as temp:
        t=Path(temp); source=t/"source.mp4"
        if audio_file is None:
            if not shutil.which("say"):
                raise SystemExit("Pass a narration sample with --audio.")
            audio_file = t / "speech.aiff"
            subprocess.run(["say", "-r", "145", "-o", str(audio_file), narration * 3], check=True)
        audio_duration = subprocess.check_output([
            "ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(audio_file),
        ], text=True).strip()
        if not audio_duration or audio_duration == "N/A" or float(audio_duration) <= 0:
            raise SystemExit("The narration has no audio samples. Run with --audio and a speech recording.")
        subprocess.run(["ffmpeg","-v","error","-f","lavfi","-i","testsrc2=size=640x360:rate=30",
                        "-stream_loop","-1","-i",str(audio_file),"-t","75","-c:v","libx264","-c:a","aac",
                        str(source)],check=True)
        with patch.object(vice,"STATE",t):
            data=vice.analyze(source,vice.digest(source))
        if len(data["choices"])<2: raise ValueError("Whisper/Ollama produced fewer than two usable moments")
        for i,cut in enumerate(data["choices"][:2],1):
            target=t/("test-"+str(i)+".mp4")
            render(source,cut["start"],cut["end"],data["segments"],None,"Local test",target)
            info=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_streams","-of","json",str(target)]))
            video,audio=info["streams"]
            if (video["width"],video["height"],video["codec_name"],audio["codec_name"])!=(720,1280,"h264","aac"):
                raise ValueError("Unexpected output codecs/dimensions")
            print(i,cut["title"],video["duration"],video["codec_name"],audio["codec_name"])

if __name__=="__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audio", type=Path, help="Use an existing speech sample for this private test.")
    run(parser.parse_args().audio)

