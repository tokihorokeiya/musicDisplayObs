# 🎵 Real-Time Music Display for OBS Studio

A zero-browser-extension, standalone desktop tool for Windows that captures live playing music/videos from **YouTube, Spotify, Apple Music, Chrome, Edge, Firefox, etc.** and generates transparent, animated HTML widgets designed for **OBS Studio Browser Sources (1000 × 400)**.

---

## ✨ Features

- **Zero Browser Extensions Required**: Captures song title, artist/channel name, playback status (Playing/Paused), and live album art thumbnails directly via Windows GSMTC media services.
- **10+ Built-In Transparent Stream Templates**:
  1. **Glassmorphism Glow** (Frosted acrylic card with neon ambient glow)
  2. **Cyberpunk 2077 HUD** (High-tech HUD with neon cyan/magenta borders and equalizer bars)
  3. **Retro Vinyl Turntable** (Spinning LP vinyl record sliding out of sleeve when playing)
  4. **Minimal Floating Pill** (Ultra-compact sleek floating badge with marquee text)
  5. **Retro Cassette Tape (Lo-Fi)** (Animated dual-spool cassette with warm handwritten label)
  6. **Broadcast Lower-Third** (Clean TV/broadcast graphic with slide-in entry)
  7. **RGB Gaming Chroma** (Animated rainbow gradient glow with bouncing soundbars)
  8. **Spotify Green Card** (Spotify-inspired media card with green pulse)
  9. **90s CD Jewel Case** (Transparent CD case with rotating iridescent silver compact disc)
  10. **Dynamic Island Banner** (Fluid spring bounce animation and auto-fade)
- **Automatic Marquee Scrolling**: Long song titles automatically scroll smoothly so text is never cut off.
- **Customizable Server Port**: Defaults to `11150` (safe from common port collisions) and can be changed in the GUI anytime.
- **Desktop Controller & System Tray**: Monitor live track info, change templates, copy OBS URLs in 1-click, and minimize to system tray while streaming.
- **Interactive Web Gallery**: Open `http://localhost:11150/` to preview all 10 templates side-by-side with live music data.

---

## 🚀 Quick Start

### 1. Launch the Application
Simply double-click `run.bat` or run:
```bash
python main.py
```

### 2. Add to OBS Studio
1. In the desktop controller, select your preferred template and click **"📋 Copy OBS Browser Source URL"**.
2. Open **OBS Studio**, click the **`+`** icon under **Sources**, and choose **Browser**.
3. Configure the source:
   - **URL**: Paste the copied link (e.g. `http://localhost:11150/overlay?theme=glassmorphism`)
   - **Width**: `1000`
   - **Height**: `400`
   - **Custom CSS**: Leave blank (the overlay is natively 100% transparent)
4. Play any music or video in your browser (YouTube, Spotify, etc.) and watch your stream overlay update in real-time!

---

## 🎨 URL Query Parameters

You can customize the overlay directly in the OBS Browser Source URL:

| Parameter | Options | Description |
|---|---|---|
| `theme` | `glassmorphism`, `cyberpunk`, `vinyl`, `minimal_pill`, `cassette`, `broadcast`, `rgb_chroma`, `spotify`, `cd_jewel`, `dynamic_island` | Selects the visual layout template |
| `autohide` | `1` or `0` | Automatically fades out the overlay when music is paused or stopped |
| `delay` | Number (e.g. `3`) | Seconds to wait before fading out after pause (default: 4s) |

**Example URL:**
```
http://localhost:11150/overlay?theme=cyberpunk&autohide=1&delay=3
```

---

## 📦 Building Standalone Executable (.exe)

Run `build.bat` to compile the application into a standalone Windows executable (`dist/OBSMusicDisplay/OBSMusicDisplay.exe`).
