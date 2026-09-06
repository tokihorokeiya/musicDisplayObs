import asyncio
import base64
import time
import datetime
import re
import traceback
from functools import lru_cache
from winsdk.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager as MediaManager,
    GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus
)
from winsdk.windows.storage.streams import DataReader

# Pre-compiled regex patterns for high-throughput string cleaning & extraction
RE_TOPIC = re.compile(r'\s*-\s*Topic$', re.IGNORECASE)
CLUTTER_PATTERNS = [
    re.compile(r'\s*[\(\[\{【](?:official\s+)?(?:music\s+video|video|audio|lyric\s+video|visualizer|mv|hd|4k|remastered|performance\s+video|live|official)[\)\]\}】]', re.IGNORECASE),
    re.compile(r'\s*[\(\[\{【](?:full\s+ver\.|full\s+version|mv)[\)\]\}】]', re.IGNORECASE),
    re.compile(r'\s*\|?\s*Official\s+(?:Music\s+)?Video\s*$', re.IGNORECASE),
    re.compile(r'\s*\|?\s*Official\s+Audio\s*$', re.IGNORECASE),
    re.compile(r'\s*【MV】\s*$', re.IGNORECASE),
    re.compile(r'\s*\[MV\]\s*$', re.IGNORECASE),
    re.compile(r'\s*\(MV\)\s*$', re.IGNORECASE)
]
RE_DASH = re.compile(r'^([^-\u2013\u2014]+)\s*[-\u2013\u2014]\s*(.+)$')
RE_FEAT = re.compile(r'[\(\[\{]?\s*(?:feat\.|ft\.|featuring)\s*([^\)\]\}]+)[\)\]\}]?', re.IGNORECASE)
RE_SPACES = re.compile(r'\s{2,}')

@lru_cache(maxsize=256)
def parse_song_and_artist(raw_title, raw_artist):
    """
    Intelligently extracts clean song title and all artists/singers (including collaborations and features)
    from YouTube and YouTube Music metadata.
    Memoized with LRU cache for O(1) instantaneous lookups during polling.
    """
    if not raw_title:
        return "", raw_artist or ""
        
    title = raw_title.strip()
    artist = raw_artist.strip() if raw_artist else ""

    # 1. Clean "- Topic" from artist channel names (YouTube Music auto-generated)
    artist = RE_TOPIC.sub('', artist)

    # 2. Strip common YouTube video junk from title
    for cp in CLUTTER_PATTERNS:
        title = cp.sub('', title)
    title = title.strip()

    # 3. Check for "Artist(s) - Title" format (very common in YouTube music videos)
    dash_match = RE_DASH.match(title)
    extracted_artist = ""
    extracted_title = title

    if dash_match:
        part1 = dash_match.group(1).strip()
        part2 = dash_match.group(2).strip()

        # Check if part1 contains the artist or if artist matches part1
        if artist and (artist.lower() in part1.lower() or part1.lower() in artist.lower()):
            # Part 1 often has multiple artists! e.g. artist="Taylor Swift", part1="Taylor Swift, Post Malone"
            extracted_artist = part1
            extracted_title = part2
        elif not artist:
            extracted_artist = part1
            extracted_title = part2
        elif len(part1.split()) <= 8:
            # If artist is a record label or channel name, prefer part1 if it has collaboration indicators
            part1_lower = part1.lower()
            if any(w in part1_lower for w in ('feat', 'ft.', '&', ' x ', 'with', ',', '/')):
                extracted_artist = part1
                extracted_title = part2

    if extracted_artist:
        artist = extracted_artist
        title = extracted_title

    # 4. Check for featured artists in the title: e.g. "Fortnight (feat. Post Malone)"
    feat_match = RE_FEAT.search(title)
    if feat_match:
        featured = feat_match.group(1).strip()
        # If featured artist is not already in artist string
        if featured.lower() not in artist.lower():
            if artist:
                artist = f"{artist} ft. {featured}"
            else:
                artist = f"ft. {featured}"
        # Remove the feat segment from the title
        title = RE_FEAT.sub('', title).strip()

    # Clean double spaces
    title = RE_SPACES.sub(' ', title).strip()
    artist = RE_SPACES.sub(' ', artist).strip()

    return title, artist


class MediaEngine:
    def __init__(self, on_update_callback=None):
        self.on_update_callback = on_update_callback
        self.active_theme = "glassmorphism"
        self.current_data = {
            "title": "",
            "artist": "",
            "album": "",
            "status": "Stopped",
            "is_playing": False,
            "thumbnail": "",
            "position": 0,
            "duration": 0,
            "has_media": False,
            "updated_at": 0,
            "active_theme": self.active_theme
        }
        self.is_running = False
        self._last_broadcast_time = 0
        self._last_smooth_pos = 0.0
        self._last_smooth_song = ""
        self._media_manager = None
        self._cached_track_key = None
        self._cached_thumbnail_b64 = ""

    def set_active_theme(self, theme_id):
        """Updates active theme for dynamic overlay updates."""
        self.active_theme = theme_id
        self.current_data["active_theme"] = theme_id

    async def _extract_thumbnail(self, thumbnail_stream_ref):
        if not thumbnail_stream_ref:
            return ""
        try:
            stream = await thumbnail_stream_ref.open_read_async()
            size = stream.size
            if size <= 0:
                return ""
            reader = DataReader(stream.get_input_stream_at(0))
            await reader.load_async(size)
            buf = bytearray(size)
            reader.read_bytes(buf)
            b64_str = base64.b64encode(buf).decode('utf-8')
            return f"data:image/jpeg;base64,{b64_str}"
        except Exception:
            return ""

    async def get_current_media_info(self):
        try:
            if self._media_manager is None:
                self._media_manager = await MediaManager.request_async()
            manager = self._media_manager
            if not manager:
                return None
            
            sessions = manager.get_sessions()
            target_session = manager.get_current_session()
            
            if not target_session and sessions:
                for s in sessions:
                    pb = s.get_playback_info()
                    if pb and pb.playback_status == PlaybackStatus.PLAYING:
                        target_session = s
                        break
                if not target_session and len(sessions) > 0:
                    target_session = sessions[0]

            if not target_session:
                self._cached_track_key = None
                self._cached_thumbnail_b64 = ""
                return {
                    "title": "",
                    "artist": "",
                    "album": "",
                    "status": "Stopped",
                    "is_playing": False,
                    "thumbnail": "",
                    "position": 0,
                    "duration": 0,
                    "has_media": False,
                    "updated_at": time.time()
                }

            properties = await target_session.try_get_media_properties_async()
            playback_info = target_session.get_playback_info()
            timeline = target_session.get_timeline_properties()

            status_str = "Stopped"
            is_playing = False
            if playback_info:
                st = playback_info.playback_status
                if st == PlaybackStatus.PLAYING:
                    status_str = "Playing"
                    is_playing = True
                elif st == PlaybackStatus.PAUSED:
                    status_str = "Paused"
                    is_playing = False
                elif st == PlaybackStatus.STOPPED:
                    status_str = "Stopped"
                    is_playing = False
                elif st == PlaybackStatus.CHANGING:
                    status_str = "Changing"

            raw_title = properties.title if properties and properties.title else ""
            raw_artist = properties.artist if properties and properties.artist else ""
            album = properties.album_title if properties and properties.album_title else ""
            
            if not raw_artist and properties and properties.album_artist:
                raw_artist = properties.album_artist

            # Clean and extract multiple singers & title (O(1) cached lookup)
            clean_title, clean_artist = parse_song_and_artist(raw_title, raw_artist)

            # Timeline info (current position & duration)
            pos = 0.0
            dur = 0.0
            if timeline:
                try:
                    if timeline.end_time:
                        dur = max(0.0, float(timeline.end_time.total_seconds()))
                    if timeline.position:
                        raw_pos = max(0.0, float(timeline.position.total_seconds()))
                        if is_playing and timeline.last_updated_time:
                            lut = timeline.last_updated_time
                            if lut.tzinfo is None:
                                lut = lut.replace(tzinfo=datetime.timezone.utc)
                            now_utc = datetime.datetime.now(datetime.timezone.utc)
                            delta = (now_utc - lut).total_seconds()
                            if 0.0 <= delta < 3600.0:
                                raw_pos += delta
                        if dur > 0:
                            pos = min(dur, raw_pos)
                        else:
                            pos = raw_pos
                except Exception:
                    pass

            # Anti-jitter: prevent micro-backwards timestamp jumping during normal playback
            song_key = f"{clean_title}::{clean_artist}"
            if song_key == self._last_smooth_song and is_playing:
                # If time jittered backwards by less than 2.0 seconds, keep previous progress
                if 0.0 < (self._last_smooth_pos - pos) < 2.0:
                    pos = self._last_smooth_pos
                else:
                    self._last_smooth_pos = pos
            else:
                self._last_smooth_song = song_key
                self._last_smooth_pos = pos

            # Thumbnail: Cache based on song identity to avoid COM stream I/O and base64 re-encoding every 500ms
            track_key = (raw_title, raw_artist, album)
            if track_key == self._cached_track_key and self._cached_thumbnail_b64:
                thumbnail_b64 = self._cached_thumbnail_b64
            else:
                thumbnail_b64 = ""
                if properties and properties.thumbnail:
                    thumbnail_b64 = await self._extract_thumbnail(properties.thumbnail)
                self._cached_track_key = track_key
                self._cached_thumbnail_b64 = thumbnail_b64

            has_media = bool(clean_title or clean_artist)

            return {
                "title": clean_title,
                "artist": clean_artist,
                "album": album,
                "status": status_str,
                "is_playing": is_playing,
                "thumbnail": thumbnail_b64,
                "position": pos,
                "duration": dur,
                "has_media": has_media,
                "updated_at": time.time()
            }
        except Exception:
            self._media_manager = None
            return None

    async def start_monitoring(self, poll_interval=0.5):
        self.is_running = True
        while self.is_running:
            try:
                info = await self.get_current_media_info()
                if info is not None:
                    now = time.time()
                    # Check if metadata changed
                    meta_changed = (
                        info["title"] != self.current_data["title"] or
                        info["artist"] != self.current_data["artist"] or
                        info["status"] != self.current_data["status"] or
                        info["has_media"] != self.current_data["has_media"] or
                        (bool(info["thumbnail"]) != bool(self.current_data["thumbnail"])) or
                        abs(info["duration"] - self.current_data.get("duration", 0)) > 2
                    )

                    # Periodic time synchronization (every 3 seconds or immediately on seek)
                    # Note: overlay.js client has its own smooth 500ms local ticker, so 3s sync eliminates redundant network traffic
                    time_jump = abs(info["position"] - self.current_data.get("position", 0)) > 2.0
                    periodic_sync = (now - self._last_broadcast_time >= 3.0)

                    if meta_changed or time_jump or periodic_sync:
                        info["active_theme"] = self.active_theme
                        self.current_data = info
                        self._last_broadcast_time = now

                        if self.on_update_callback:
                            if asyncio.iscoroutinefunction(self.on_update_callback):
                                await self.on_update_callback(self.current_data)
                            else:
                                self.on_update_callback(self.current_data)
                    else:
                        # Keep current position updated in memory
                        self.current_data["position"] = info["position"]
                        self.current_data["duration"] = info["duration"]
                        self.current_data["updated_at"] = info["updated_at"]

            except Exception:
                pass
            
            await asyncio.sleep(poll_interval)

    def stop_monitoring(self):
        self.is_running = False
