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
        self._template_cache = {}

        if getattr(sys, 'frozen', False):
            bundle_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
            self.base_dir = bundle_dir if os.path.exists(os.path.join(bundle_dir, "templates")) else os.path.dirname(sys.executable)
        else:
            self.base_dir = os.path.dirname(os.path.abspath(__file__))

        self._setup_routes()

    def _get_template(self, name):
        """Returns in-memory cached template content to eliminate blocking disk I/O on async loop."""
        if name not in self._template_cache:
            path = os.path.join(self.base_dir, "templates", name)
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        self._template_cache[name] = f.read()
                except Exception:
                    self._template_cache[name] = None
            else:
                self._template_cache[name] = None
        return self._template_cache[name]

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
        content = self._get_template("dashboard.html")
        if content is not None:
            return web.Response(text=content, content_type="text/html", headers=self._no_cache_headers())
        return web.Response(text="<h1>Dashboard Not Found</h1>", content_type="text/html", status=404)

    def _get_theme_template(self, theme):
        """Returns in-memory cached theme HTML template content."""
        if not hasattr(self, "_theme_template_cache"):
            self._theme_template_cache = {}
        if theme not in self._theme_template_cache:
            path = os.path.join(self.base_dir, "static", "templates", f"{theme}.html")
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        self._theme_template_cache[theme] = f.read()
                except Exception:
                    self._theme_template_cache[theme] = ""
            else:
                self._theme_template_cache[theme] = ""
        return self._theme_template_cache[theme]

    async def _handle_overlay(self, request):
        content = self._get_template("overlay.html")
        if content is not None:
            theme = request.query.get("theme")
            if not theme or theme in ("active", "global"):
                theme = self.media_engine.current_data.get("active_theme", "glassmorphism")
            initial_html = self._get_theme_template(theme)
            rendered = content.replace("{{THEME}}", theme).replace("{{INITIAL_TEMPLATE}}", initial_html)
            return web.Response(text=rendered, content_type="text/html", headers=self._no_cache_headers())
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
        clients = list(self.ws_clients)

        async def _safe_send(client):
            try:
                await client.send_str(payload)
                return None
            except Exception:
                return client

        # Broadcast concurrently across all connected OBS browser sources
        results = await asyncio.gather(*[_safe_send(ws) for ws in clients], return_exceptions=True)
        for r in results:
            if isinstance(r, web.WebSocketResponse):
                self.ws_clients.discard(r)

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
