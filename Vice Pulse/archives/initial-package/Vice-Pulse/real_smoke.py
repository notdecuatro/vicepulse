"""Exercise the installed ML and production media path with original narration. No publication."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from unittest.mock import patch

import vice
from media import render

def run():
    for binary in ("ffmpeg","ffprobe","say","ollama"):
        if not shutil.which(binary):
            raise SystemExit("Missing dependency: "+binary)
    narration=("The route begins at the blue checkpoint. I follow the road along the water and wait for the first marker. "
               "Look at the path where it crosses the bridge. The next marker turns orange as I arrive. "
               "The second run takes a different turn. I pass the entrance, watch the line change, and reach the finish. "
               "At the final checkpoint I compare both routes and mark the shortest one. ")
    with tempfile.TemporaryDirectory() as temp:
        t=Path(temp); source=t/"source.mp4"
        subprocess.run(["say","-r","145","-o",str(t/"speech.aiff"),narration*3],check=True)
        subprocess.run(["ffmpeg","-v","error","-f","lavfi","-i","testsrc2=size=640x360:rate=30",
                        "-i",str(t/"speech.aiff"),"-t","75","-shortest","-c:v","libx264","-c:a","aac",
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
    run()

