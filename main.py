import asyncio
import threading
import sys
import os

from config import load_config, save_config
from media_engine import MediaEngine
from server import MediaServer
from app_gui import AppGUI

class AppCoordinator:
    def __init__(self):
        self.config = load_config()
        self.loop = None
        self.async_thread = None
        self.media_engine = None
        self.server = None
        self.gui = None

    def start(self):
        # Initialize media engine
        self.media_engine = MediaEngine(on_update_callback=self._on_media_update)
        self.media_engine.set_active_theme(self.config.get("selected_theme", "glassmorphism"))
        self.server = MediaServer(self.media_engine, port=self.config.get("port", 11150))

        # Initialize GUI in main thread first
        self.gui = AppGUI(
            config=self.config,
            on_port_change_callback=self._on_port_changed,
            on_theme_change_callback=self._on_theme_changed,
            on_exit_callback=self._shutdown
        )

        # Start async event loop in background thread once GUI is ready
        self.async_thread = threading.Thread(target=self._run_async_loop, daemon=True)
        self.async_thread.start()

        try:
            self.gui.mainloop()
        finally:
            self._shutdown()
            os._exit(0)

    def _run_async_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        async def main_tasks():
            await self.server.start()
            await self.media_engine.start_monitoring(poll_interval=0.5)

        self.loop.run_until_complete(main_tasks())

    async def _on_media_update(self, data):
        # Broadcast to websockets
        if self.server:
            await self.server.broadcast_media_update(data)
        # Update GUI
        if self.gui:
            self.gui.update_media_display(data)

    def _on_theme_changed(self, theme_id):
        self.config["selected_theme"] = theme_id
        save_config(self.config)
        if self.media_engine:
            self.media_engine.set_active_theme(theme_id)
        if self.loop and self.server:
            async def broadcast_theme():
                payload = dict(self.media_engine.current_data)
                payload["theme_changed"] = True
                payload["reload"] = True
                await self.server.broadcast_media_update(payload)
            asyncio.run_coroutine_threadsafe(broadcast_theme(), self.loop)

    def _on_port_changed(self, new_port):
        self.config["port"] = new_port
        save_config(self.config)
        if self.loop and self.server:
            async def restart_srv():
                await self.server.stop()
                self.server.port = new_port
                await self.server.start()
            asyncio.run_coroutine_threadsafe(restart_srv(), self.loop)

    def _shutdown(self):
        save_config(self.config)
        if self.media_engine:
            self.media_engine.stop_monitoring()
        if self.loop and self.server:
            try:
                future = asyncio.run_coroutine_threadsafe(self.server.stop(), self.loop)
                future.result(timeout=1.0)
            except Exception:
                pass
        if self.loop and self.loop.is_running():
            try:
                self.loop.call_soon_threadsafe(self.loop.stop)
            except Exception:
                pass


def main():
    coordinator = AppCoordinator()
    coordinator.start()

if __name__ == "__main__":
    main()
