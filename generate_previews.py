import asyncio
import os
import time
from media_engine import MediaEngine
from server import MediaServer

THEMES = [
    "glassmorphism",
    "cyberpunk",
    "vinyl",
    "minimal_pill",
    "cassette",
    "broadcast",
    "cute_kawaii",
    "spotify",
    "lofi_cozy",
    "dynamic_island"
]

def find_edge():
    paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    return "msedge"

async def capture_all_previews():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    previews_dir = os.path.join(base_dir, "static", "previews")
    os.makedirs(previews_dir, exist_ok=True)
    
    edge_bin = find_edge()
    print("Using Edge browser at:", edge_bin, flush=True)

    engine = MediaEngine()
    engine.current_data = {
        "title": "Sincerely",
        "artist": "Yuzuki Choco",
        "album": "Hololive Summer",
        "status": "Playing",
        "is_playing": True,
        "thumbnail": "",
        "position": 142.0,
        "duration": 278.0,
        "has_media": True,
        "updated_at": time.time()
    }

    server = MediaServer(engine, port=11150)
    await server.start()
    print("Server started for preview generation.", flush=True)

    # Let server spin up
    await asyncio.sleep(1)

    for theme in THEMES:
        out_path = os.path.join(previews_dir, f"{theme}.png")
        url = f"http://localhost:11150/overlay?theme={theme}&mock=1"
        cmd = [
            edge_bin,
            "--headless=new",
            "--disable-gpu",
            f"--screenshot={out_path}",
            "--window-size=1000,400",
            url
        ]
        print(f"Capturing {theme}...", flush=True)
        try:
            proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            await asyncio.wait_for(proc.communicate(), timeout=10.0)
            if os.path.exists(out_path):
                print(f" -> Saved {out_path} ({os.path.getsize(out_path)} bytes)", flush=True)
            else:
                print(f" -> Warning: file not created for {theme}", flush=True)
        except Exception as e:
            print(f" -> Failed {theme}: {e}", flush=True)

    await server.stop()
    print("All previews generated successfully!", flush=True)

if __name__ == "__main__":
    asyncio.run(capture_all_previews())
