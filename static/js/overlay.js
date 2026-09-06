/**
 * Real-Time Music Display OBS Overlay Controller V4
 * Multi-resolution (1920x700, 1000x400, 1920x1080 bottom), Auto-scaling,
 * Zero-leak base64 SVG, White Title, Cute Kawaii & Lo-Fi Cozy themes.
 */

const DEFAULT_COVER = "/static/sample_cover.png";

let currentMedia = {
    title: "",
    artist: "",
    status: "Stopped",
    is_playing: false,
    thumbnail: "",
    position: 0,
    duration: 0,
    has_media: false,
    updated_at: Date.now() / 1000
};

let hideTimeout = null;
let socket = null;
let localPosition = 0;
let lastSyncTimestamp = Date.now();

// Parse Query Parameters
const urlParams = new URLSearchParams(window.location.search);
const requestedThemeParam = urlParams.get('theme');
const isGlobalTheme = (!requestedThemeParam || requestedThemeParam === 'active' || requestedThemeParam === 'global');
let currentTheme = (requestedThemeParam && requestedThemeParam !== 'active' && requestedThemeParam !== 'global') 
    ? requestedThemeParam 
    : 'glassmorphism';
const autoHideEnabled = urlParams.get('autohide') === '1';
const autoHideDelay = parseInt(urlParams.get('delay') || '4', 10) * 1000;
const requestedMode = urlParams.get('mode') || (urlParams.get('w') === '1920' ? '1920x700' : 'auto');
const requestedPos = urlParams.get('pos') || 'center';
const customScale = parseFloat(urlParams.get('scale') || '0');

document.addEventListener('DOMContentLoaded', () => {
    applyTheme(currentTheme);
    applyPositionAndMode();
    connectWebSocket();
    startPlaybackTicker();
    setupAutoScale();

    if (urlParams.get('mock') === '1') {
        updateUI({
            title: "Sincerely",
            artist: "Yuzuki Choco",
            status: "Playing",
            is_playing: true,
            thumbnail: "/static/sample_cover.png",
            position: 140.0,
            duration: 278.0,
            has_media: true,
            updated_at: Date.now() / 1000
        });
    }
});

function applyPositionAndMode() {
    if (requestedPos === 'bottom') {
        document.body.classList.add('pos-bottom');
    } else {
        document.body.classList.add('pos-center');
    }

    if (requestedMode === '1920x700') {
        document.body.classList.add('mode-1920x700');
    }
}

function setupAutoScale() {
    function autoScale() {
        const windowW = window.innerWidth;
        const windowH = window.innerHeight;
        const container = document.getElementById('overlay-container');
        if (!container) return;

        if (customScale > 0) {
            container.style.transform = `scale(${customScale})`;
            return;
        }

        // If in 1920x700 or full screen window
        if (windowW >= 1600 && windowH >= 650) {
            // Scale up nicely for 1920p stream
            const scale = Math.min(windowW / 1100, windowH / 460, 1.65);
            container.style.transform = `scale(${scale})`;
        } else if (windowW >= 1200) {
            const scale = Math.min(windowW / 1050, windowH / 420, 1.35);
            container.style.transform = `scale(${scale})`;
        } else {
            // Standard 1000x400 fit
            const scale = Math.min(windowW / 1000, windowH / 400);
            if (scale < 0.99 || scale > 1.01) {
                container.style.transform = `scale(${scale})`;
            } else {
                container.style.transform = 'none';
            }
        }
    }

    window.addEventListener('resize', autoScale);
    autoScale();
}

const dom = {
    container: null,
    widgetCard: null,
    titleEl: null,
    titleWrapper: null,
    artistEl: null,
    coverEl: null,
    vinylCenter: null,
    fillEl: null,
    timeDisplayEl: null,
    timeCurrentEl: null,
    timeDurationEl: null
};

function cacheDOMElements() {
    dom.container = document.getElementById('overlay-container');
    dom.widgetCard = document.getElementById('widget-card');
    dom.titleEl = document.getElementById('track-title');
    dom.titleWrapper = document.getElementById('title-wrapper');
    dom.artistEl = document.getElementById('artist-name');
    dom.coverEl = document.getElementById('cover-img');
    dom.vinylCenter = document.getElementById('vinyl-center-img');
    dom.fillEl = document.getElementById('progress-fill');
    dom.timeDisplayEl = document.getElementById('time-display');
    dom.timeCurrentEl = document.getElementById('time-current');
    dom.timeDurationEl = document.getElementById('time-duration');
}

function applyTheme(themeName) {
    currentTheme = themeName;
    const container = document.getElementById('overlay-container');
    if (container) {
        container.className = `theme-${themeName}`;
    }
    renderThemeHTML(themeName);
    cacheDOMElements();
}

function formatTime(seconds) {
    if (!seconds || isNaN(seconds) || seconds < 0) return "00:00";
    const totalSec = Math.floor(seconds);
    const m = Math.floor(totalSec / 60);
    const s = totalSec % 60;
    const mm = m < 10 ? `0${m}` : `${m}`;
    const ss = s < 10 ? `0${s}` : `${s}`;
    return `${mm}:${ss}`;
}

function renderThemeHTML(theme) {
    const container = document.getElementById('overlay-container');
    
    if (theme === 'vinyl') {
        container.innerHTML = `
            <div class="widget-card" id="widget-card">
                <div class="vinyl-wrapper">
                    <img class="vinyl-sleeve cover-art" id="cover-img" src="${DEFAULT_COVER}" alt="">
                    <div class="vinyl-record">
                        <div class="vinyl-center" id="vinyl-center-img"></div>
                    </div>
                </div>
                <div class="info-box">
                    <div class="marquee-wrapper" id="title-wrapper">
                        <div class="marquee-content track-title" id="track-title">Waiting for music...</div>
                    </div>
                    <div class="artist-name" id="artist-name">No active playback</div>
                    <div class="progress-section">
                        <div class="progress-bar-container">
                            <div class="progress-bar-fill" id="progress-fill"></div>
                        </div>
                        <div class="time-display" id="time-display">00:00 / 00:00</div>
                    </div>
                </div>
            </div>
        `;
    } else if (theme === 'cassette') {
        container.innerHTML = `
            <div class="widget-card" id="widget-card">
                <div class="cassette-label">
                    <div class="marquee-wrapper" id="title-wrapper">
                        <div class="marquee-content track-title" id="track-title">Waiting for music...</div>
                    </div>
                    <div class="spools-window">
                        <div class="spool"></div>
                        <div class="sound-bars">
                            <span></span><span></span><span></span><span></span><span></span>
                        </div>
                        <div class="spool"></div>
                    </div>
                    <div class="cassette-bottom-row">
                        <div class="artist-name" id="artist-name">No active playback</div>
                        <div class="time-display" id="time-display">00:00 / 00:00</div>
                    </div>
                    <div class="progress-bar-container">
                        <div class="progress-bar-fill" id="progress-fill"></div>
                    </div>
                </div>
            </div>
        `;
    } else if (theme === 'cyberpunk') {
        container.innerHTML = `
            <div class="widget-card" id="widget-card">
                <div class="cyber-scanline"></div>
                <div class="cyber-corner cyber-tl"></div>
                <div class="cyber-corner cyber-tr"></div>
                <div class="cyber-corner cyber-bl"></div>
                <div class="cyber-corner cyber-br"></div>
                <div class="cyber-header-row">
                    <span class="cyber-sys-badge">SYS.AUDIO_V2.0 // DECRYPTED_FEED</span>
                    <span class="cyber-status-tag">STATUS: LIVE_STREAM</span>
                </div>
                <div class="cyber-main-row">
                    <div class="cyber-cover-wrapper">
                        <img class="cover-art" id="cover-img" src="${DEFAULT_COVER}" alt="">
                    </div>
                    <div class="info-box">
                        <div class="marquee-wrapper" id="title-wrapper">
                            <div class="marquee-content track-title" id="track-title">Waiting for music...</div>
                        </div>
                        <div class="artist-name" id="artist-name">No active playback</div>
                        <div class="cyber-telemetry">
                            <span>BITRATE: 320KBPS</span>
                            <span>ENC: AAC-HE</span>
                            <span>FREQ: 48.0kHz</span>
                        </div>
                        <div class="progress-section">
                            <div class="progress-bar-container">
                                <div class="progress-bar-fill" id="progress-fill"></div>
                            </div>
                            <div class="time-display" id="time-display">00:00 / 00:00</div>
                        </div>
                    </div>
                    <div class="sound-bars">
                        <span></span><span></span><span></span><span></span><span></span>
                    </div>
                </div>
            </div>
        `;
    } else if (theme === 'minimal_pill') {
        container.innerHTML = `
            <div class="widget-card" id="widget-card">
                <div class="pill-cover-wrapper">
                    <img class="cover-art" id="cover-img" src="${DEFAULT_COVER}" alt="">
                    <div class="pill-play-indicator"></div>
                </div>
                <div class="info-box">
                    <div class="marquee-wrapper" id="title-wrapper">
                        <div class="marquee-content track-title" id="track-title">Waiting for music...</div>
                    </div>
                    <div class="pill-sub-row">
                        <div class="artist-name" id="artist-name">No active playback</div>
                        <div class="time-display" id="time-display">00:00 / 00:00</div>
                    </div>
                    <div class="progress-bar-container">
                        <div class="progress-bar-fill" id="progress-fill"></div>
                    </div>
                </div>
                <div class="sound-bars">
                    <span></span><span></span><span></span><span></span><span></span>
                </div>
            </div>
        `;
    } else if (theme === 'broadcast') {
        container.innerHTML = `
            <div class="widget-card" id="widget-card">
                <div class="broadcast-top-strip">
                    <div class="broadcast-live-badge">
                        <span class="broadcast-pulse-dot"></span>
                        <span>LIVE BROADCAST</span>
                    </div>
                    <div class="broadcast-channel-tag">STUDIO FEED // AUDIO MONITOR</div>
                </div>
                <div class="broadcast-content-row">
                    <img class="cover-art" id="cover-img" src="${DEFAULT_COVER}" alt="">
                    <div class="info-box">
                        <div class="marquee-wrapper" id="title-wrapper">
                            <div class="marquee-content track-title" id="track-title">Waiting for music...</div>
                        </div>
                        <div class="artist-name" id="artist-name">No active playback</div>
                        <div class="progress-section">
                            <div class="progress-bar-container">
                                <div class="progress-bar-fill" id="progress-fill"></div>
                            </div>
                            <div class="time-display" id="time-display">00:00 / 00:00</div>
                        </div>
                    </div>
                    <div class="sound-bars">
                        <span></span><span></span><span></span><span></span><span></span>
                    </div>
                </div>
            </div>
        `;
    } else if (theme === 'cute_kawaii') {
        container.innerHTML = `
            <div class="widget-card" id="widget-card">
                <div class="kawaii-banner">
                    <span>💖 NOW PLAYING ♫ VTUBER SPECIAL ✨</span>
                </div>
                <div class="kawaii-body">
                    <div class="kawaii-cover-wrap">
                        <img class="cover-art" id="cover-img" src="${DEFAULT_COVER}" alt="">
                        <div class="kawaii-heart-badge">♥</div>
                    </div>
                    <div class="info-box">
                        <div class="marquee-wrapper" id="title-wrapper">
                            <div class="marquee-content track-title" id="track-title">Waiting for music...</div>
                        </div>
                        <div class="artist-name" id="artist-name">No active playback</div>
                        <div class="progress-section">
                            <div class="progress-bar-container">
                                <div class="progress-bar-fill" id="progress-fill"></div>
                            </div>
                            <div class="time-display" id="time-display">00:00 / 00:00</div>
                        </div>
                    </div>
                    <div class="sound-bars">
                        <span></span><span></span><span></span><span></span><span></span>
                    </div>
                </div>
            </div>
        `;
    } else if (theme === 'spotify') {
        container.innerHTML = `
            <div class="widget-card" id="widget-card">
                <div class="spotify-badge-header">
                    <span>NOW PLAYING</span>
                </div>
                <div class="spotify-body">
                    <div class="spotify-cover-wrap">
                        <img class="cover-art" id="cover-img" src="${DEFAULT_COVER}" alt="">
                    </div>
                    <div class="info-box">
                        <div class="marquee-wrapper" id="title-wrapper">
                            <div class="marquee-content track-title" id="track-title">Waiting for music...</div>
                        </div>
                        <div class="artist-name" id="artist-name">No active playback</div>
                        <div class="progress-section spotify-progress-row">
                            <span class="time-current" id="time-current">00:00</span>
                            <div class="progress-bar-container">
                                <div class="progress-bar-fill" id="progress-fill"></div>
                            </div>
                            <span class="time-duration" id="time-duration">00:00</span>
                        </div>
                    </div>
                    <div class="sound-bars">
                        <span></span><span></span><span></span><span></span><span></span>
                    </div>
                </div>
            </div>
        `;
    } else if (theme === 'lofi_cozy') {
        container.innerHTML = `
            <div class="widget-card" id="widget-card">
                <div class="lofi-top-badge">
                    <span>☕ LO-FI BEATS TO RELAX / CHILL TO</span>
                    <span class="lofi-cassette-rpm">33⅓ RPM</span>
                </div>
                <div class="lofi-main">
                    <div class="lofi-cover-wrap">
                        <img class="cover-art" id="cover-img" src="${DEFAULT_COVER}" alt="">
                    </div>
                    <div class="info-box">
                        <div class="marquee-wrapper" id="title-wrapper">
                            <div class="marquee-content track-title" id="track-title">Waiting for music...</div>
                        </div>
                        <div class="artist-name" id="artist-name">No active playback</div>
                        <div class="progress-section">
                            <div class="progress-bar-container">
                                <div class="progress-bar-fill" id="progress-fill"></div>
                            </div>
                            <div class="time-display" id="time-display">00:00 / 00:00</div>
                        </div>
                    </div>
                    <div class="sound-bars">
                        <span></span><span></span><span></span><span></span><span></span>
                    </div>
                </div>
            </div>
        `;
    } else if (theme === 'dynamic_island') {
        container.innerHTML = `
            <div class="widget-card" id="widget-card">
                <div class="island-left">
                    <img class="cover-art" id="cover-img" src="${DEFAULT_COVER}" alt="">
                </div>
                <div class="info-box island-center">
                    <div class="marquee-wrapper" id="title-wrapper">
                        <div class="marquee-content track-title" id="track-title">Waiting for music...</div>
                    </div>
                    <div class="artist-name" id="artist-name">No active playback</div>
                    <div class="progress-section">
                        <div class="progress-bar-container">
                            <div class="progress-bar-fill" id="progress-fill"></div>
                        </div>
                    </div>
                </div>
                <div class="island-right">
                    <div class="sound-bars">
                        <span></span><span></span><span></span><span></span><span></span>
                    </div>
                    <div class="time-display" id="time-display">00:00</div>
                </div>
            </div>
        `;
    } else if (theme === 'bento') {
        container.innerHTML = `
            <div class="widget-card" id="widget-card">
                <div class="bento-cell bento-cover-cell">
                    <img class="cover-art" id="cover-img" src="${DEFAULT_COVER}" alt="">
                </div>
                <div class="bento-cell bento-main-cell">
                    <div class="bento-live-badge">
                        <span class="bento-live-dot"></span>
                        <span>LIVE STREAM AUDIO</span>
                    </div>
                    <div class="marquee-wrapper" id="title-wrapper">
                        <div class="marquee-content track-title" id="track-title">Waiting for music...</div>
                    </div>
                    <div class="artist-name" id="artist-name">No active playback</div>
                    <div class="progress-section">
                        <div class="progress-bar-container">
                            <div class="progress-bar-fill" id="progress-fill"></div>
                        </div>
                    </div>
                </div>
                <div class="bento-cell bento-stats-cell">
                    <div class="sound-bars">
                        <span></span><span></span><span></span><span></span><span></span>
                    </div>
                    <div class="time-display" id="time-display">00:00 / 00:00</div>
                </div>
            </div>
        `;
    } else if (theme === 'swiss') {
        container.innerHTML = `
            <div class="widget-card" id="widget-card">
                <div class="swiss-sidebar">
                    <div class="swiss-cross">+</div>
                    <div class="swiss-meta-vert">CH-8001</div>
                    <div class="swiss-cross">+</div>
                </div>
                <div class="swiss-body">
                    <img class="cover-art" id="cover-img" src="${DEFAULT_COVER}" alt="">
                    <div class="info-box">
                        <div class="swiss-header-tag">
                            <span>01 // NOW PLAYING</span>
                            <span>&bull;</span>
                            <span>STEREO</span>
                        </div>
                        <div class="marquee-wrapper" id="title-wrapper">
                            <div class="marquee-content track-title" id="track-title">Waiting for music...</div>
                        </div>
                        <div class="artist-name" id="artist-name">No active playback</div>
                        <div class="progress-section">
                            <div class="progress-bar-container">
                                <div class="progress-bar-fill" id="progress-fill"></div>
                            </div>
                            <div class="time-display" id="time-display">00:00 / 00:00</div>
                        </div>
                    </div>
                    <div class="sound-bars">
                        <span></span><span></span><span></span><span></span><span></span>
                    </div>
                </div>
            </div>
        `;
    } else if (theme === 'eight_bit') {
        container.innerHTML = `
            <div class="widget-card" id="widget-card">
                <img class="cover-art" id="cover-img" src="${DEFAULT_COVER}" alt="">
                <div class="info-box">
                    <div class="eight-bit-header">
                        <span>★ 1P LV.99 // BGM</span>
                        <span class="eight-bit-cursor">█</span>
                    </div>
                    <div class="marquee-wrapper" id="title-wrapper">
                        <div class="marquee-content track-title" id="track-title">Waiting for music...</div>
                    </div>
                    <div class="artist-name" id="artist-name">No active playback</div>
                    <div class="progress-section">
                        <span class="hp-label">HP</span>
                        <div class="progress-bar-container">
                            <div class="progress-bar-fill" id="progress-fill"></div>
                        </div>
                        <div class="time-display" id="time-display">00:00 / 00:00</div>
                    </div>
                </div>
                <div class="sound-bars">
                    <span></span><span></span><span></span><span></span><span></span>
                </div>
            </div>
        `;
    } else if (theme === 'editorial') {
        container.innerHTML = `
            <div class="widget-card" id="widget-card">
                <img class="cover-art" id="cover-img" src="${DEFAULT_COVER}" alt="">
                <div class="info-box">
                    <div class="editorial-meta">
                        <span>VOL. IV &middot; N&deg; 26</span>
                        <span>NOW AUDIBLE</span>
                    </div>
                    <div class="marquee-wrapper" id="title-wrapper">
                        <div class="marquee-content track-title" id="track-title">Waiting for music...</div>
                    </div>
                    <div class="artist-name" id="artist-name">No active playback</div>
                    <div class="progress-section">
                        <div class="progress-bar-container">
                            <div class="progress-bar-fill" id="progress-fill"></div>
                        </div>
                        <div class="time-display" id="time-display">00:00 / 00:00</div>
                    </div>
                </div>
                <div class="sound-bars">
                    <span></span><span></span><span></span><span></span><span></span>
                </div>
            </div>
        `;
    } else if (theme === 'hand_drawn') {
        container.innerHTML = `
            <div class="widget-card" id="widget-card">
                <div class="washi-tape"></div>
                <img class="cover-art" id="cover-img" src="${DEFAULT_COVER}" alt="">
                <div class="info-box">
                    <div class="doodle-tag">&starf; now playing &bull; tune &starf;</div>
                    <div class="marquee-wrapper" id="title-wrapper">
                        <div class="marquee-content track-title" id="track-title">Waiting for music...</div>
                    </div>
                    <div class="artist-name" id="artist-name">No active playback</div>
                    <div class="progress-section">
                        <div class="progress-bar-container">
                            <div class="progress-bar-fill" id="progress-fill"></div>
                        </div>
                        <div class="time-display" id="time-display">00:00 / 00:00</div>
                    </div>
                </div>
                <div class="sound-bars">
                    <span></span><span></span><span></span><span></span><span></span>
                </div>
            </div>
        `;
    } else if (theme === 'retro') {
        container.innerHTML = `
            <div class="widget-card" id="widget-card">
                <div class="retro-stripes"></div>
                <img class="cover-art" id="cover-img" src="${DEFAULT_COVER}" alt="">
                <div class="info-box">
                    <div class="retro-deck-label">STEREO HI-FI &bull; AUTO-REVERSE DECK</div>
                    <div class="marquee-wrapper" id="title-wrapper">
                        <div class="marquee-content track-title" id="track-title">Waiting for music...</div>
                    </div>
                    <div class="artist-name" id="artist-name">No active playback</div>
                    <div class="progress-section">
                        <div class="progress-bar-container">
                            <div class="progress-bar-fill" id="progress-fill"></div>
                        </div>
                        <div class="time-display" id="time-display">00:00 / 00:00</div>
                    </div>
                </div>
                <div class="sound-bars">
                    <span></span><span></span><span></span><span></span><span></span>
                </div>
            </div>
        `;
    } else if (theme === 'pixel') {
        container.innerHTML = `
            <div class="widget-card" id="widget-card">
                <img class="cover-art" id="cover-img" src="${DEFAULT_COVER}" alt="">
                <div class="info-box">
                    <div class="pixel-badge">&#9654; 1UP [MUSIC_ARCADE]</div>
                    <div class="marquee-wrapper" id="title-wrapper">
                        <div class="marquee-content track-title" id="track-title">Waiting for music...</div>
                    </div>
                    <div class="artist-name" id="artist-name">No active playback</div>
                    <div class="progress-section">
                        <div class="progress-bar-container">
                            <div class="progress-bar-fill" id="progress-fill"></div>
                        </div>
                        <div class="time-display" id="time-display">00:00 / 00:00</div>
                    </div>
                </div>
                <div class="sound-bars">
                    <span></span><span></span><span></span><span></span><span></span>
                </div>
            </div>
        `;
    } else if (theme === 'flat') {
        container.innerHTML = `
            <div class="widget-card" id="widget-card">
                <img class="cover-art" id="cover-img" src="${DEFAULT_COVER}" alt="">
                <div class="info-box">
                    <div><span class="flat-pill">ON AIR</span></div>
                    <div class="marquee-wrapper" id="title-wrapper">
                        <div class="marquee-content track-title" id="track-title">Waiting for music...</div>
                    </div>
                    <div class="artist-name" id="artist-name">No active playback</div>
                    <div class="progress-section">
                        <div class="progress-bar-container">
                            <div class="progress-bar-fill" id="progress-fill"></div>
                        </div>
                        <div class="time-display" id="time-display">00:00 / 00:00</div>
                    </div>
                </div>
                <div class="sound-bars">
                    <span></span><span></span><span></span><span></span><span></span>
                </div>
            </div>
        `;
    } else if (theme === 'minimalism') {
        container.innerHTML = `
            <div class="widget-card" id="widget-card">
                <img class="cover-art" id="cover-img" src="${DEFAULT_COVER}" alt="">
                <div class="info-box">
                    <div class="minimal-meta">PLAYING NOW</div>
                    <div class="marquee-wrapper" id="title-wrapper">
                        <div class="marquee-content track-title" id="track-title">Waiting for music...</div>
                    </div>
                    <div class="artist-name" id="artist-name">No active playback</div>
                    <div class="progress-section">
                        <div class="progress-bar-container">
                            <div class="progress-bar-fill" id="progress-fill"></div>
                        </div>
                        <div class="time-display" id="time-display">00:00 / 00:00</div>
                    </div>
                </div>
                <div class="sound-bars">
                    <span></span><span></span><span></span><span></span><span></span>
                </div>
            </div>
        `;
    } else {
        // Universal Layout (glassmorphism, cyberpunk, minimal_pill, broadcast, cute_kawaii, lofi_cozy, dynamic_island)
        container.innerHTML = `
            <div class="widget-card" id="widget-card">
                <img class="cover-art" id="cover-img" src="${DEFAULT_COVER}" alt="">
                <div class="info-box">
                    <div class="top-row">
                        <div class="marquee-wrapper" id="title-wrapper">
                            <div class="marquee-content track-title" id="track-title">Waiting for music...</div>
                        </div>
                        <div class="sound-bars">
                            <span></span><span></span><span></span><span></span><span></span>
                        </div>
                    </div>
                    <div class="artist-name" id="artist-name">No active playback</div>
                    <div class="progress-section">
                        <div class="progress-bar-container">
                            <div class="progress-bar-fill" id="progress-fill"></div>
                        </div>
                        <div class="time-display" id="time-display">00:00 / 00:00</div>
                    </div>
                </div>
            </div>
        `;
    }
}

function getEstimatedPosition() {
    const duration = currentMedia.duration || 0;
    let pos = localPosition;
    if (currentMedia.is_playing) {
        const elapsed = (Date.now() - lastSyncTimestamp) / 1000;
        pos = localPosition + elapsed;
    }
    if (duration > 0 && pos > duration) {
        pos = duration;
    }
    return Math.max(0, pos);
}

function updateUI(data) {
    if (!data) return;

    const serverPos = (typeof data.position === 'number' && !isNaN(data.position)) ? Math.max(0, data.position) : 0;
    const songChanged = (data.title !== currentMedia.title || data.artist !== currentMedia.artist);
    const playStateChanged = (data.is_playing !== currentMedia.is_playing);

    if (!songChanged && !playStateChanged && currentMedia.is_playing && data.is_playing) {
        const currentLocal = getEstimatedPosition();
        const diff = Math.abs(serverPos - currentLocal);
        // Only jump if it's a real seek (> 2.0s), otherwise never bounce backwards
        if (diff > 2.0) {
            localPosition = serverPos;
            lastSyncTimestamp = Date.now();
        } else if (serverPos > localPosition) {
            localPosition = serverPos;
            lastSyncTimestamp = Date.now();
        }
    } else {
        localPosition = serverPos;
        lastSyncTimestamp = Date.now();
    }

    currentMedia = data;

    // If using the Global Active Overlay, dynamically switch theme if active_theme changed!
    if (isGlobalTheme && data.active_theme && data.active_theme !== currentTheme) {
        currentTheme = data.active_theme;
        applyTheme(currentTheme);
    }

    const container = dom.container;
    const widgetCard = dom.widgetCard;
    const titleEl = dom.titleEl;
    const titleWrapper = dom.titleWrapper;
    const artistEl = dom.artistEl;
    const coverEl = dom.coverEl;
    const vinylCenter = dom.vinylCenter;

    const hasMedia = data.has_media && (data.title || data.artist);
    const isPlaying = data.is_playing;

    // Handle auto-hide
    if (autoHideEnabled && container) {
        if (!hasMedia || !isPlaying) {
            if (!hideTimeout) {
                hideTimeout = setTimeout(() => {
                    container.classList.add('hidden-overlay');
                }, autoHideDelay);
            }
        } else {
            if (hideTimeout) {
                clearTimeout(hideTimeout);
                hideTimeout = null;
            }
            container.classList.remove('hidden-overlay');
        }
    } else if (container) {
        container.classList.remove('hidden-overlay');
    }

    // Playback state class
    if (widgetCard) {
        if (isPlaying) {
            widgetCard.classList.add('playing');
        } else {
            widgetCard.classList.remove('playing');
        }
    }

    // Cover
    const coverSrc = data.thumbnail || DEFAULT_COVER;
    if (coverEl && coverEl.src !== coverSrc) {
        coverEl.src = coverSrc;
    }
    if (vinylCenter) {
        vinylCenter.style.backgroundImage = `url("${coverSrc}")`;
    }

    // Title & Artist
    const displayTitle = data.title || "Waiting for music...";
    const displayArtist = data.artist || (hasMedia ? "Unknown Artist" : "No active playback");

    if (titleEl && titleEl.textContent !== displayTitle) {
        titleEl.textContent = displayTitle;
        adjustMarquee(titleEl, titleWrapper);
    }

    if (artistEl && artistEl.textContent !== displayArtist) {
        artistEl.textContent = displayArtist;
    }

    renderTimelineTick();
}

function renderTimelineTick() {
    const duration = currentMedia.duration || 0;
    const pos = getEstimatedPosition();

    const percent = duration > 0 ? Math.min(100, Math.max(0, (pos / duration) * 100)) : 0;

    if (dom.fillEl) {
        dom.fillEl.style.width = `${percent}%`;
    }

    const curFormatted = formatTime(pos);
    const durFormatted = duration > 0 ? formatTime(duration) : "--:--";

    if (dom.timeDisplayEl) {
        dom.timeDisplayEl.textContent = `${curFormatted} / ${durFormatted}`;
    }
    if (dom.timeCurrentEl) {
        dom.timeCurrentEl.textContent = curFormatted;
    }
    if (dom.timeDurationEl) {
        dom.timeDurationEl.textContent = durFormatted;
    }
}

function startPlaybackTicker() {
    setInterval(() => {
        if (currentMedia.has_media && currentMedia.is_playing) {
            renderTimelineTick();
        }
    }, 500);
}

function adjustMarquee(textEl, wrapperEl) {
    if (!textEl || !wrapperEl) return;
    
    textEl.classList.remove('marquee-scroll');
    void textEl.offsetWidth;

    const textWidth = textEl.scrollWidth;
    const containerWidth = wrapperEl.clientWidth;

    if (textWidth > containerWidth + 15) {
        textEl.innerHTML = `${textEl.textContent}&nbsp;&nbsp;&nbsp;&nbsp;&bull;&nbsp;&nbsp;&nbsp;&nbsp;${textEl.textContent}`;
        textEl.classList.add('marquee-scroll');
    }
}

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
        console.log('[OBS Overlay] WebSocket connected');
    };

    socket.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            updateUI(data);
        } catch (e) {
            console.error('[OBS Overlay] Parsing error:', e);
        }
    };

    socket.onclose = () => {
        setTimeout(connectWebSocket, 2000);
    };

    socket.onerror = () => {
        socket.close();
    };
}
