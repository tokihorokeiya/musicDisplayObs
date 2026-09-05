import asyncio
import os
import sys
import json
from aiohttp import web

class MediaServer:
    def __init__(self, media_engine, port=11150):
        self.media_engine = media_engine
        self.port = port
        self.app = web.Application()
        self.runner = None
        self.site = None
        self.ws_clients = set()
        self.is_running = False

        if getattr(sys, 'frozen', False):
            bundle_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
            self.base_dir = bundle_dir if os.path.exists(os.path.join(bundle_dir, "templates")) else os.path.dirname(sys.executable)
        else:
            self.base_dir = os.path.dirname(os.path.abspath(__file__))

        self._setup_routes()

    def _setup_routes(self):
        # Static files
        static_dir = os.path.join(self.base_dir, "static")
        os.makedirs(static_dir, exist_ok=True)
        self.app.router.add_static("/static/", static_dir, name="static")

        # HTML Routes
        self.app.router.add_get("/", self._handle_dashboard)
        self.app.router.add_get("/overlay", self._handle_overlay)

        # API & WebSocket Routes
        self.app.router.add_get("/api/status", self._handle_api_status)
        self.app.router.add_get("/ws", self._handle_websocket)

    def _no_cache_headers(self):
        return {
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0"
        }

    async def _handle_dashboard(self, request):
        path = os.path.join(self.base_dir, "templates", "dashboard.html")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return web.Response(text=f.read(), content_type="text/html", headers=self._no_cache_headers())
        return web.Response(text="<h1>Dashboard Not Found</h1>", content_type="text/html", status=404)

    async def _handle_overlay(self, request):
        path = os.path.join(self.base_dir, "templates", "overlay.html")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return web.Response(text=f.read(), content_type="text/html", headers=self._no_cache_headers())
        return web.Response(text="<h1>Overlay Not Found</h1>", content_type="text/html", status=404)

    async def _handle_api_status(self, request):
        return web.json_response(self.media_engine.current_data, headers=self._no_cache_headers())

    async def _handle_websocket(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.ws_clients.add(ws)

        # Send current media state immediately on connect
        try:
            await ws.send_str(json.dumps(self.media_engine.current_data))
        except Exception:
            pass

        try:
            async for msg in ws:
                pass
        finally:
            self.ws_clients.discard(ws)

        return ws

    async def broadcast_media_update(self, data):
        if not self.ws_clients:
            return
        payload = json.dumps(data)
        dead_clients = []
        for ws in self.ws_clients:
            try:
                await ws.send_str(payload)
            except Exception:
                dead_clients.append(ws)
        
        for ws in dead_clients:
            self.ws_clients.discard(ws)

    async def start(self):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, "0.0.0.0", self.port)
        await self.site.start()
        self.is_running = True
        print(f"[Server] Media Server running at http://localhost:{self.port}")

    async def stop(self):
        self.is_running = False
        for ws in list(self.ws_clients):
            await ws.close()
        self.ws_clients.clear()

        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        print("[Server] Server stopped successfully")
