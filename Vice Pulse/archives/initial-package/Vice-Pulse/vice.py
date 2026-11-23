#!/usr/bin/env python3
import argparse
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import urllib.request
import tempfile
from zoneinfo import ZoneInfo
from urllib.parse import urlparse

import services

ROOT = Path(__file__).resolve().parent
STATE = ROOT/"state"
CONFIG = ROOT/"campaign.json"
TZ = ZoneInfo("America/New_York")


def digest(path):
    h = hashlib.sha256()
    with open(path,"rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):
            h.update(block)
    return h.hexdigest()


def atomic_json(path, data):
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data,ensure_ascii=False,indent=2))
    temp.replace(path)


def db_file():
    STATE.mkdir(exist_ok=True)
    db = sqlite3.connect(STATE/"vice.sqlite",timeout=30)
    db.row_factory = sqlite3.Row
    db.executescript("""
    CREATE TABLE IF NOT EXISTS clips(day TEXT, slot INTEGER, source TEXT, start REAL, end REAL,
        campaign TEXT, title TEXT, file TEXT, hash TEXT, url TEXT, PRIMARY KEY(day,slot));
    CREATE TABLE IF NOT EXISTS jobs(day TEXT,slot INTEGER,network TEXT,status TEXT,post_id TEXT,
        public_url TEXT,sent_at TEXT,reward_ref TEXT,PRIMARY KEY(day,slot,network));
    """)
    return db


def load_config(day, delivery=False):
    if not CONFIG.is_file():
        raise ValueError("Falta campaign.json con el material y los permisos verificados.")
    c=json.loads(CONFIG.read_text())
    if c["verified_on"]!=day or not c["accepting_clips"] or c["remaining_budget"]<=0:
        raise ValueError("Revisar hoy vigencia, saldo y condiciones de la campaña.")
    if not c["campaign_url"].startswith("https://contentrewards.com/") or not c["brief"].strip():
        raise ValueError("Falta el brief de campaña.")
    if not c["disclosure"].strip() or not c["caption_suffix"].strip():
        raise ValueError("Faltan el aviso comercial y el texto de campaña.")
    if c["logo_required"] and not (ROOT/c["logo"]).is_file():
        raise ValueError("Falta el logo oficial.")
    if delivery:
        available={str(a["id"]):a["service"].lower() for a in services.channels()}
        for n,settings in c["platforms"].items():
            if settings["authorized"] and not available.get(settings["channel_id"])==n:
                raise ValueError("Canal de Buffer no verificado: "+n)
    return c


def approved_sources(c):
    ready=[]
    for s in c["sources"]:
        path=ROOT/s["file"]
        if not s.get("evidence_file"):
            continue
        proof=ROOT/s["evidence_file"]
        if not proof.is_file() or not proof.stat().st_size:
            continue
        if not all(s.get("rights",{}).get(k) is True for k in ("footage","game_ip","audio","commercial_edit","crosspost")):
            continue
        if not set(s.get("platforms",[])).issuperset(n for n,v in c["platforms"].items() if v["authorized"]):
            continue
        if s["campaign_url"]!=c["campaign_url"]:
            continue
        if not path.exists() and s.get("source_url") and len(s["sha256"])==64:
            if urlparse(s["source_url"]).scheme!="https":
                raise ValueError("Se requiere HTTPS para descargar la fuente aprobada.")
            path.parent.mkdir(parents=True,exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=path.parent,delete=False) as temp:
                staging=Path(temp.name)
            try:
                with urllib.request.urlopen(s["source_url"],timeout=90) as reply, staging.open("wb") as out:
                    shutil.copyfileobj(reply,out,1<<20)
                if digest(staging)!=s["sha256"]:
                    raise ValueError("La descarga no coincide con la fuente autorizada.")
                staging.replace(path)
            finally:
                staging.unlink(missing_ok=True)
        if not path.is_file() or s["sha256"]!=digest(path):
            continue
        ready.append((s,path))
    if not ready:
        raise ValueError("Falta una fuente con licencia comprobada para el material y las redes elegidas.")
    return ready


def analyze(path, source_id):
    cache=STATE/(source_id+".analysis.json")
    if cache.exists():
        return json.loads(cache.read_text())
    import whisper
    segments=whisper.load_model(os.getenv("WHISPER_MODEL","base")).transcribe(
        str(path),fp16=False,verbose=None)["segments"]
    segments=[{"start":s["start"],"end":s["end"],"text":s["text"]} for s in segments
              if s["end"]>s["start"] and s["text"].strip()]
    choices=services.highlights(segments)
    if not choices:
        raise ValueError("No se encontraron fragmentos utilizables.")
    result={"segments":segments,"choices":choices}
    atomic_json(cache,result)
    return result


def produce(db,c,day,analyzer=analyze,renderer=None):
    if renderer is None:
        from media import render as renderer
    sources=approved_sources(c)
    logo=(ROOT/c["logo"]) if c.get("logo") else None
    for slot in (1,2):
        current=db.execute("SELECT * FROM clips WHERE day=? AND slot=?",(day,slot)).fetchone()
        if current:
            if current["campaign"]!=c["campaign_url"] or current["source"] not in {s["sha256"] for s,p in sources}:
                raise ValueError("La campaña o la licencia del clip preparado ha cambiado.")
            if not Path(current["file"]).exists() or digest(current["file"])!=current["hash"]:
                raise ValueError("La exportación guardada ha cambiado. Revisar antes de continuar.")
            continue
        selected=False
        for s,path in sources:
            data=analyzer(path,s["sha256"])
            for cut in data["choices"]:
                start,end=cut["start"],cut["end"]
                used=db.execute("SELECT 1 FROM clips WHERE source=? AND start<? AND end>?",
                                (s["sha256"],end,start)).fetchone()
                if used:
                    continue
                out=STATE/(day+"-"+str(slot)+".mp4")
                renderer(path,start,end,data["segments"],logo,c["disclosure"],out)
                with db:
                    db.execute("INSERT INTO clips VALUES(?,?,?,?,?,?,?,?,?,NULL)",
                               (day,slot,s["sha256"],start,end,c["campaign_url"],cut["title"],str(out),digest(out)))
                selected=True
                break
            if selected:
                break
        if not selected:
            raise ValueError("Material agotado. Añadir una nueva fuente autorizada.")


def dispatch(db,c,day,slot,draft,api=services):
    sources=approved_sources(c)
    row=db.execute("SELECT * FROM clips WHERE day=? AND slot=?",(day,slot)).fetchone()
    if not row or row["campaign"]!=c["campaign_url"] or row["source"] not in {s["sha256"] for s,p in sources}:
        raise ValueError("Clip sin autorización vigente para esta campaña.")
    if digest(row["file"])!=row["hash"]:
        raise ValueError("El vídeo cambió después de exportarlo.")
    eligible=[(n,p) for n,p in c["platforms"].items() if n in services.NETWORKS and p["authorized"]]
    if not eligible:
        raise ValueError("Ninguna plataforma confirmada.")
    if not draft and (not c["joined"] or not c["submission_session_ready"] or c.get("preapproval_required") is not False):
        raise ValueError("Primero verificar adhesión, entrega y aprobación previa si aplica.")
    if not draft and any(p.get("native_disclosure_supported") is not True for _,p in eligible):
        raise ValueError("Usar borradores y aplicar la etiqueta comercial nativa antes de publicar.")
    url=row["url"]
    if not url:
        url=api.upload(Path(row["file"]),row["hash"])
        with db:
            db.execute("UPDATE clips SET url=? WHERE day=? AND slot=?",(url,day,slot))
    for n,p in eligible:
        identity=(day,slot,n)
        job=db.execute("SELECT status FROM jobs WHERE day=? AND slot=? AND network=?",identity).fetchone()
        if job:
            continue  # A draft must be published from Buffer; ambiguous sends require reconciliation.
        payload=services.post_input(p["channel_id"],n,row["title"],
                c["disclosure"]+" "+row["title"]+"\n"+c["caption_suffix"],url,draft)
        with db:
            db.execute("INSERT INTO jobs(day,slot,network,status) VALUES(?,?,?,'sending')",identity)
        remote_id=api.send(payload)
        with db:
            db.execute("UPDATE jobs SET status=?,post_id=? WHERE day=? AND slot=? AND network=?",
                       ("draft" if draft else "queued",remote_id,*identity))


def sync(db,api=services):
    for job in db.execute("SELECT * FROM jobs WHERE post_id IS NOT NULL AND reward_ref IS NULL AND status!='native_sent'").fetchall():
        r=api.receipt(job["post_id"])
        with db:
            db.execute("UPDATE jobs SET status=?,public_url=?,sent_at=? WHERE day=? AND slot=? AND network=?",
                       (r["status"],r.get("externalLink"),r.get("sentAt"),job["day"],job["slot"],job["network"]))
    now=dt.datetime.now(dt.timezone.utc)
    for job in db.execute("SELECT * FROM jobs ORDER BY day,slot,network"):
        item=dict(job)
        if job["sent_at"] and not job["reward_ref"]:
            sent=dt.datetime.fromisoformat(job["sent_at"].replace("Z","+00:00"))
            deadline=sent+dt.timedelta(minutes=30)
            item["submit_before"]=deadline.isoformat()
            item["window_open"]=sent<=now<deadline
        print(json.dumps(item,ensure_ascii=False))


def main():
    if (ROOT/"credentials.json").is_file():
        file=ROOT/"credentials.json"
        if file.stat().st_mode & 0o077:
            raise SystemExit("credentials.json requiere permisos 0600.")
        for k,v in json.loads(file.read_text()).items():
            if k in ("CLOUDINARY_URL","BUFFER_API_KEY"):
                os.environ[k]=v
    parser=argparse.ArgumentParser()
    parser.add_argument("command",choices=["doctor","accounts","produce","draft","publish","sync","record","link","reconcile"])
    parser.add_argument("--slot",type=int,choices=[1,2])
    parser.add_argument("--network",choices=services.NETWORKS)
    parser.add_argument("--receipt")
    parser.add_argument("--post-id")
    parser.add_argument("--url")
    parser.add_argument("--sent-at")
    parser.add_argument("--day",default=dt.datetime.now(TZ).date().isoformat())
    a=parser.parse_args()
    if a.command=="doctor":
        from importlib.util import find_spec
        result={k:bool(shutil.which(k)) for k in ("ffmpeg","ffprobe","ollama")}
        result.update({k:bool(find_spec(k)) for k in ("whisper","cloudinary","PIL")})
        result.update({k:bool(os.getenv(k)) for k in ("CLOUDINARY_URL","BUFFER_API_KEY")})
        result["campaign"]=CONFIG.is_file()
        print(json.dumps(result,indent=2)); return
    if a.command=="accounts":
        print(json.dumps(services.channels(),indent=2)); return
    db=db_file()
    with open(STATE/"worker.lock","a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        if a.command=="sync":
            sync(db); return
        if a.command=="reconcile":
            if not a.slot or not a.network or not a.post_id:
                parser.error("reconcile requiere --slot --network --post-id")
            r=services.graph("query($id:PostId!){post(input:{id:$id}){id channelId text status}}",
                             {"id":a.post_id})["post"]
            c=json.loads(CONFIG.read_text())
            clip=db.execute("SELECT title FROM clips WHERE day=? AND slot=?",(a.day,a.slot)).fetchone()
            if not clip or r["channelId"]!=c["platforms"][a.network]["channel_id"] or clip["title"] not in r["text"]:
                raise ValueError("No coincide el clip o el canal.")
            with db:
                updated=db.execute("UPDATE jobs SET post_id=?,status=? WHERE day=? AND slot=? AND network=? AND status='sending'",
                                   (a.post_id,r["status"],a.day,a.slot,a.network))
                if updated.rowcount!=1: raise ValueError("No hay envío pendiente de conciliación.")
            return
        if a.command=="link":
            if not all((a.url,a.sent_at,a.network,a.slot)):
                parser.error("link requiere --slot --network --url --sent-at (ISO con zona)")
            parsed=urlparse(a.url)
            domains={"instagram":("instagram.com",),"youtube":("youtube.com","youtu.be"),"tiktok":("tiktok.com",)}
            if parsed.scheme!="https" or not any(parsed.hostname==host or (parsed.hostname or "").endswith("."+host)
                                                for host in domains[a.network]) or not parsed.path.strip("/"):
                raise ValueError("Se requiere el enlace real de la publicación.")
            stamp=dt.datetime.fromisoformat(a.sent_at.replace("Z","+00:00"))
            if not stamp.tzinfo or stamp>dt.datetime.now(dt.timezone.utc): raise ValueError("Hora de publicación inválida.")
            with db:
                found=db.execute("UPDATE jobs SET status='native_sent',public_url=?,sent_at=? WHERE day=? AND slot=? AND network=? AND public_url IS NULL AND reward_ref IS NULL",
                                 (a.url,stamp.isoformat(),a.day,a.slot,a.network))
                if found.rowcount!=1: raise ValueError("Comprobar el borrador y los enlaces existentes.")
            return
        if a.command=="record":
            if not a.receipt or not a.network or not a.slot:
                parser.error("record requiere --network, --slot y --receipt (referencia real de Content Rewards)")
            with db:
                result=db.execute("UPDATE jobs SET reward_ref=? WHERE day=? AND slot=? AND network=? AND public_url IS NOT NULL AND reward_ref IS NULL",
                                  (a.receipt,a.day,a.slot,a.network))
                if result.rowcount!=1:
                    raise ValueError("Se requiere una publicación confirmada y sin acuse previo.")
            return
        if a.day!=dt.datetime.now(TZ).date().isoformat():
            parser.error("La verificación y el lote deben corresponder a hoy.")
        c=load_config(a.day,a.command!="produce")
        if a.command=="produce":
            produce(db,c,a.day)
        else:
            if not a.slot: parser.error("Se requiere --slot 1 o 2.")
            dispatch(db,c,a.day,a.slot,a.command=="draft")


if __name__=="__main__":
    main()

