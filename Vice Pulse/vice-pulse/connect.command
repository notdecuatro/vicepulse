#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
umask 077
python3 - <<'PY'
import getpass,json,os,tempfile
from pathlib import Path
from urllib.parse import urlparse
cloud=getpass.getpass("Cloudinary URL (cloudinary://..., entrada oculta): ").strip()
token=getpass.getpass("Buffer API key (entrada oculta): ").strip()
p=urlparse(cloud)
if p.scheme!="cloudinary" or not p.username or not p.password or not p.hostname or not token:
    raise SystemExit("Se requieren ambas credenciales.")
with tempfile.NamedTemporaryFile(mode="w",dir=".",delete=False) as out:
    json.dump({"CLOUDINARY_URL":cloud,"BUFFER_API_KEY":token},out)
os.replace(out.name,"credentials.json")
print("Credenciales guardadas en este Mac.")
PY
