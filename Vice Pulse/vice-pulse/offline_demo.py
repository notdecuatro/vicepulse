"""Offline media fixture. Encodes real QuickTime JPEG/PCM previews with Pillow and the standard library.
The live worker uses FFmpeg H.264/AAC. No service is contacted by this demo.
"""
import array
import io
import math
import struct
from pathlib import Path
from PIL import Image, ImageDraw
from media import overlay, caption_at, captions, font

def box(name, data):
    return struct.pack(">I4s",8+len(data),name.encode())+data

def pack(fmt,*args):
    return struct.pack(">"+fmt,*args)

def full(name,data,flags=0):
    return box(name,pack("I",flags)+data)

MATRIX=pack("9I",65536,0,0,0,65536,0,0,0,1<<30)
RATE=8000
FPS=6


def movie(path,frames,sound,size):
    w,h=size
    jpeg=[]
    for im in frames:
        buf=io.BytesIO()
        im.save(buf,"JPEG",quality=66,optimize=True)
        jpeg.append(buf.getvalue())
    n=len(jpeg)
    samples=len(sound)//2
    duration=round(n*1000/FPS)
    ftyp=box("ftyp",b"qt  "+pack("I",0)+b"qt  ")
    offset=len(ftyp)+8
    video_offset=offset
    audio_offset=offset+sum(map(len,jpeg))
    mvhd=full("mvhd",pack("4IIH",0,0,1000,duration,65536,256)+bytes(10)+MATRIX+bytes(24)+pack("I",3))
    def track(video):
        ident=1 if video else 2
        tkhd=full("tkhd",pack("5I",0,0,ident,0,duration)+bytes(8)+pack("4H",0,0,0 if video else 256,0)+MATRIX+
                  pack("2I",w<<16 if video else 0,h<<16 if video else 0),7)
        mdhd=full("mdhd",pack("4I2H",0,0,FPS if video else RATE,n if video else samples,0,0))
        hdlr=full("hdlr",bytes(4)+(b"vide" if video else b"soun")+bytes(12)+b"Vice Pulse\0")
        dinf=box("dinf",full("dref",pack("I",1)+full("url ",b"",1)))
        common=bytes(6)+pack("H",1)
        if video:
            desc=box("jpeg",common+bytes(16)+pack("2H3I2H",w,h,72<<16,72<<16,0,1,0)[:-2]+bytes(32)+pack("Hh",24,-1))
            header=full("vmhd",bytes(8),1)
        else:
            desc=box("sowt",common+bytes(8)+pack("4HI",1,16,0,0,RATE<<16))
            header=full("smhd",bytes(4))
        count=n if video else samples
        stsd=full("stsd",pack("I",1)+desc)
        stts=full("stts",pack("3I",1,count,1))
        stsc=full("stsc",pack("4I",1,1,count,1))
        stsz=full("stsz",pack("2I",0 if video else 2,count)+(b"".join(pack("I",len(j)) for j in jpeg) if video else b""))
        stco=full("stco",pack("2I",1,video_offset if video else audio_offset))
        return box("trak",tkhd+box("mdia",mdhd+hdlr+box("minf",header+dinf+box("stbl",stsd+stts+stsc+stsz+stco))))
    path.write_bytes(ftyp+box("mdat",b"".join(jpeg)+sound)+box("moov",mvhd+track(True)+track(False)))


def base(t):
    img=Image.new("RGB",(800,450),(15,25,42))
    d=ImageDraw.Draw(img)
    color=(74,223,184) if t<18 else (255,167,86)
    for x in range(-40,870,50):
        d.line((x+t*2%50,0,x+t*2%50,450),fill=(28,45,63))
    for y in range(0,450,50):
        d.line((0,y,800,y),fill=(28,45,63))
    route=[(250,305),(342,264),(345,214),(415,180),(433,124),(535,99)]
    d.line(route,width=5,fill=color)
    s=(t/5)%5
    i=int(s)
    x,y=route[i]
    nx,ny=route[i+1]
    x,y=x+(nx-x)*(s-i),y+(ny-y)*(s-i)
    d.ellipse((x-7,y-7,x+7,y+7),fill="white")
    d.text((400,65),"VICE PULSE",font=font(23),fill="white",anchor="mm")
    d.text((400,356),"ROUTE 01" if t<18 else "ROUTE 02",font=font(25),fill=color,anchor="mm")
    return img


def sample_audio(t):
    beat=t%0.75
    return int(3200*math.exp(-beat*9)*math.sin(2*math.pi*(220 if t<18 else 330)*t))


def demo(folder):
    folder.mkdir(exist_ok=True,parents=True)
    transcript=[{"start":0,"end":8,"text":"Watch the dot follow the first route."},
                {"start":8,"end":18,"text":"It reaches the final turn at the top."},
                {"start":18,"end":26,"text":"The second route starts in orange."},
                {"start":26,"end":36,"text":"Follow the marker to the last checkpoint."}]
    groups=captions(transcript)
    # Encode and independently decode each source frame before selecting its interval.
    frames=[]
    for index in range(36*FPS):
        b=io.BytesIO()
        base(index/FPS).save(b,"JPEG",quality=78)
        frames.append(b.getvalue())
    sound=array.array("h",(sample_audio(i/RATE) for i in range(36*RATE))).tobytes()
    for slot,(start,end) in enumerate(((0,18),(18,36)),1):
        def composed():
            for i in range(start*FPS,end*FPS):
                with Image.open(io.BytesIO(frames[i])) as im:
                    yield overlay(im,caption_at(groups,i/FPS),None,"VICE PULSE  /  LOCAL TEST")
        movie(folder/("demo-"+str(slot)+".mov"),composed(),sound[start*RATE*2:end*RATE*2],(720,1280))


if __name__=="__main__":
    import sys
    demo(Path(sys.argv[1]) if len(sys.argv)>1 else Path("demo"))

