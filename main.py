import os
import re
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
import yt_dlp

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

progress_data = {}

def progress_hook(d, url):
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', '0%').strip()
        percent = re.sub(r'\x1b[^m]*m', '', percent) 
        progress_data[url] = percent
    elif d['status'] == 'finished':
        progress_data[url] = '100%'

# ده الجزء اللي بيخلي الصفحة تظهر لما تفتح الرابط
@app.get("/")
def serve_html():
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/progress")
def get_progress(url: str):
    return {"progress": progress_data.get(url, "0%")}

@app.get("/download")
async def download_video(url: str, format: str = "mp4"):
    try:
        progress_data[url] = "0%"
        
        ydl_opts = {
            "outtmpl": "downloads/%(title)s.%(ext)s",
            "noplaylist": True,
            "progress_hooks": [lambda d: progress_hook(d, url)]
        }

        if format == "mp3":
            ydl_opts.update({
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            })
        else:
            ydl_opts.update({
                "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            })

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info_dict)
            if format == "mp3":
                filename = filename.rsplit(".", 1)[0] + ".mp3"

        return FileResponse(
            path=filename,
            filename=os.path.basename(filename),
            media_type="application/octet-stream",
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
