#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
if ! command -v brew >/dev/null && [[ -x /opt/homebrew/bin/brew ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
fi
if ! command -v brew >/dev/null; then
    installer="$(mktemp)"
    trap 'rm -f "$installer"' EXIT
    curl --fail --location --proto '=https' https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh -o "$installer"
    /bin/bash "$installer"
    eval "$(/opt/homebrew/bin/brew shellenv)"
fi
brew install ffmpeg ollama python@3.11
PY="$(brew --prefix python@3.11)/bin/python3.11"
"$PY" -m venv .runtime
.runtime/bin/python -m pip install 'openai-whisper' 'cloudinary>=1.44,<2' 'Pillow>=10,<14' 'yt-dlp==2026.10.26'
if ! curl -fsS http://127.0.0.1:11434/api/tags >/dev/null; then
    brew services start ollama
    for i in {1..30}; do
        if curl -fsS http://127.0.0.1:11434/api/tags >/dev/null; then break; fi
        sleep 1
    done
fi
ollama pull qwen2.5:1.5b
.runtime/bin/python -c 'import whisper; whisper.load_model("base")'
.runtime/bin/python vice.py doctor
.runtime/bin/python acceptance.py

.runtime/bin/python real_smoke.py
