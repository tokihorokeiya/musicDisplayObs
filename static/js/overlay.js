/**
 * Real-Time Music Display OBS Overlay Controller V5
 * Modular multi-file theme architecture with on-demand CSS & HTML template streaming.
 * Multi-resolution (1920x700, 1000x400, 1920x1080 bottom), Auto-scaling,
 * Zero-leak base64 SVG, White Title, Normal CJK ClearType fonts.
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
const templateCache = {};

// Parse Query Parameters
const urlParams = new URLSearchParams(window.location.search);
const requestedThemeParam = urlParams.get('theme');
const isGlobalTheme = (!requestedThemeParam || requestedThemeParam === 'active' || requestedThemeParam === 'global');
const serverTheme = (typeof window !== 'undefined' && window.INITIAL_THEME) 
    || (typeof document !== 'undefined' && document.getElementById('overlay-container')?.className.match(/theme-([^\s]+)/)?.[1]) 
    || 'glassmorphism';
let currentTheme = (requestedThemeParam && requestedThemeParam !== 'active' && requestedThemeParam !== 'global') 
    ? requestedThemeParam 
    : serverTheme;
const autoHideEnabled = urlParams.get('autohide') === '1';
const autoHideDelay = parseInt(urlParams.get('delay') || '4', 10) * 1000;
const requestedMode = urlParams.get('mode') || (urlParams.get('w') === '1920' ? '1920x700' : 'auto');
const requestedPos = urlParams.get('pos') || 'center';
const customScale = parseFloat(urlParams.get('scale') || '0');

document.addEventListener('DOMContentLoaded', () => {
    // Cache server-side pre-rendered template for the initial theme
    const container = document.getElementById('overlay-container');
    if (container && container.querySelector('#widget-card')) {
        templateCache[currentTheme] = container.innerHTML;
    }

    applyTheme(currentTheme);
    applyPositionAndMode();
    connectWebSocket();
    startPlaybackTicker();
    setupAutoScale();

    if (urlParams.get('mock') === '1') {
        updateUI({
            title: "Sincerely",
            artist: "TRUE (Violet Evergarden OP)",
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

        // Responsive stream scaling
        if (windowW >= 1600 && windowH >= 650) {
            const scale = Math.min(windowW / 1100, windowH / 460, 1.65);
            container.style.transform = `scale(${scale})`;
        } else if (windowW >= 1200) {
            const scale = Math.min(windowW / 1050, windowH / 420, 1.35);
            container.style.transform = `scale(${scale})`;
        } else {
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

    // 1. Dynamically swap the theme-specific stylesheet link
    let themeLink = document.getElementById('theme-css');
    if (!themeLink) {
        themeLink = document.createElement('link');
        themeLink.id = 'theme-css';
        themeLink.rel = 'stylesheet';
        document.head.appendChild(themeLink);
    }
    const targetHref = `/static/css/themes/${themeName}.css?v=5.1`;
    if (themeLink.getAttribute('href') !== targetHref) {
        themeLink.href = targetHref;
    }

    // 2. Render theme HTML template
    renderThemeHTML(themeName);
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

const UNIVERSAL_FALLBACK_HTML = `
    <div class="widget-card" id="widget-card">
        <img class="cover-art" id="cover-img" src="/static/sample_cover.png" alt="">
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

function renderThemeHTML(theme) {
    const container = document.getElementById('overlay-container');
    if (!container) return;

    // Fast Path: In-memory cache hit
    if (templateCache[theme]) {
        container.innerHTML = templateCache[theme];
        cacheDOMElements();
        updateUI(currentMedia);
        return;
    }

    // Async Path: Fetch template file on-demand
    fetch(`/static/templates/${theme}.html?v=5.1`)
        .then(res => {
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return res.text();
        })
        .then(html => {
            templateCache[theme] = html;
            if (currentTheme === theme) {
                container.innerHTML = html;
                cacheDOMElements();
                updateUI(currentMedia);
            }
        })
        .catch(err => {
            console.warn(`[OBS Overlay] Could not load template for ${theme}, falling back:`, err);
            container.innerHTML = UNIVERSAL_FALLBACK_HTML;
            cacheDOMElements();
            updateUI(currentMedia);
        });
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

    // If using Global Active Overlay, cleanly reload if active_theme changed
    if (isGlobalTheme && data.active_theme && data.active_theme !== currentTheme) {
        console.log(`[OBS Overlay] Active theme changed from ${currentTheme} to ${data.active_theme}. Reloading overlay...`);
        currentTheme = data.active_theme;
        window.location.reload();
        return;
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
            if (isGlobalTheme && (data.reload || (data.active_theme && data.active_theme !== currentTheme))) {
                console.log(`[OBS Overlay] Theme change detected (target: ${data.active_theme}). Reloading overlay for clean layout...`);
                currentTheme = data.active_theme || currentTheme;
                window.location.reload();
                return;
            }
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
