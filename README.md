# 🎵 Real-Time Music Display for OBS Studio

<p align="center">
  <img src="static/showcase.png" alt="OBS Real-Time Music Display Themes" width="100%">
</p>

<p align="center">
  <a href="https://github.com/tokihorokeiya/musicDisplayObs/releases"><img src="https://img.shields.io/github/v/release/tokihorokeiya/musicDisplayObs?color=blue&label=Latest%20Release" alt="Release"></a>
  <img src="https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6?logo=windows&logoColor=white" alt="Platform">
  <img src="https://img.shields.io/badge/OBS%20Studio-v28%2B%20Compatible-black?logo=obsstudio&logoColor=white" alt="OBS Studio">
  <img src="https://img.shields.io/badge/Browser%20Extension-Zero%20Required-success" alt="No Extensions">
  <img src="https://img.shields.io/badge/Themes-10%20Built--in%20Styles-8A2BE2" alt="10 Themes">
</p>

---

## 🌐 Language Navigation / 語言切換 / 言語切替
* 🇬🇧 [English User Guide](#-english-user-guide)
* 🇹🇼 [繁體中文使用指南](#-繁體中文使用指南)
* 🇯🇵 [日本語ユーザーガイド](#-日本語ユーザーガイド)

---

<br>

# 🇬🇧 English User Guide

A standalone desktop tool for Windows that captures currently playing music or video from **YouTube, YouTube Music, Spotify, Apple Music, Chrome, Edge, Firefox, etc.** via Windows System Media Services (GSMTC) and displays transparent, animated widgets for **OBS Studio** streams.

* **No browser extensions required** — zero configuration or token setup.
* **Direct Drag-and-Drop** — simply grab any template badge from the app and drop it right into OBS Studio!
* **10 High-Quality Built-in Themes** — from Glassmorphism and Cyberpunk to Retro Cassette and Vinyl.
* **Auto-marquee text** — long song titles and artist names smoothly scroll without ever being cut off.

---

### 🚀 Quick Start

#### Method 1: Standalone Windows App (Recommended - No Python Needed)
1. Go to the [Releases Page](https://github.com/tokihorokeiya/musicDisplayObs/releases).
2. Download OBSMusicDisplay-vX.X.X-windows.zip.
3. Extract the .zip archive to any folder on your PC.
4. Double-click **OBSMusicDisplay.exe** to start.

#### Method 2: Run from Python Source
1. Ensure Python 3.10+ is installed on Windows.
2. Clone this repository:
   `ash
   git clone https://github.com/tokihorokeiya/musicDisplayObs.git
   cd musicDisplayObs
   `
3. Install dependencies:
   `ash
   pip install -r requirements.txt
   `
4. Double-click 
un.bat or run:
   `ash
   python main.py
   `

---

### 🎬 How to Add to OBS Studio

#### ✨ Option A: Instant Drag & Drop (Fastest)
1. Launch **OBS Music Display** and **OBS Studio**.
2. In the app, switch to the **"10 Style Templates (Drag to OBS)"** tab.
3. Click and hold the green **⠿ Drag to OBS** badge (or preview thumbnail) of your desired template.
4. Drag your mouse into OBS Studio and release it onto the **Sources dock** or **Preview Canvas**.
5. OBS Studio will automatically create a **Browser Source** pointing to your live music overlay!

> **⚠️ Note on Windows Admin Mode:** If OBS Studio is running as *Administrator*, Windows UIPI security prevents dragging between standard and elevated windows. Run OBS Studio normally, or use **Option B** below.

#### 📋 Option B: One-Click Copy URL
1. Click the blue **"📋 Copy URL"** button next to any template in the gallery.
2. In OBS Studio, click **+** under **Sources** ➔ select **Browser**.
3. Paste the copied URL into the **URL** input field.
4. Set **Width** to 1920 and **Height** to 700 (or 1000 × 400 for compact widgets).
5. Click **OK** — your transparent overlay is ready!

---

### 🎨 10 Built-In Theme Templates

| Theme Name | Style Description | Preview Screenshot |
|---|---|:---:|
| **1. Glassmorphism** | Frosted glass acrylic panel with glowing neon border and smooth blur | <img src="static/previews/glassmorphism.png" width="320"> |
| **2. Cyberpunk 2077** | Neon cyan/magenta HUD with digital equalizer soundbars and glitch styling | <img src="static/previews/cyberpunk.png" width="320"> |
| **3. Vinyl Turntable** | Spinning realistic vinyl LP record sliding smoothly from the album sleeve | <img src="static/previews/vinyl.png" width="320"> |
| **4. Minimal Pill** | Ultra-clean floating capsule pill badge with auto-scrolling marquee title | <img src="static/previews/minimal_pill.png" width="320"> |
| **5. Retro Cassette** | Dual-spool animated vintage cassette tape with warm handwritten song label | <img src="static/previews/cassette.png" width="320"> |
| **6. Broadcast Banner** | Clean television lower-third news-ticker layout with streaming status tag | <img src="static/previews/broadcast.png" width="320"> |
| **7. Cute Kawaii** | Soft pastel aesthetic with floating sparkles, hearts, and candy-colored gradients | <img src="static/previews/cute_kawaii.png" width="320"> |
| **8. Spotify Card** | Spotify-inspired modern dark card with glowing green active audio equalizer | <img src="static/previews/spotify.png" width="320"> |
| **9. Lo-Fi Cozy** | Warm twilight bedroom vibes with amber string-light glow and soft typography | <img src="static/previews/lofi_cozy.png" width="320"> |
| **10. Dynamic Island** | Apple-style floating pill with fluid spring-bounce expansion when music updates | <img src="static/previews/dynamic_island.png" width="320"> |

---

### ⚙️ URL Parameters & Customization

You can adjust any overlay on the fly by appending URL parameters:

| Parameter | Values | Default | Description |
|---|---|---|---|
| 	heme | glassmorphism, cyberpunk, inyl, etc. | glassmorphism | Visual layout style |
| utohide | 1 or | delay | Number (e.g. 3) | 3 | Seconds to wait before fading out on pause |
| w | Width in pixels | 1920 | Canvas width |
| h | Height in pixels | 700 | Canvas height |
| mode | 1920x700, 1000x400, 1920x1080 | 1920x700 | Pre-configured responsive sizing preset |

**Example URL:**
`
http://localhost:11150/overlay?theme=cyberpunk&autohide=1&delay=3&w=1920&h=700
`

---

<br>

# 🇹🇼 繁體中文使用指南

專為 Windows 實況主設計的免外掛、免設定即時音樂串流顯示工具！透過 Windows 系統媒體服務（GSMTC），直接抓取 **YouTube、YouTube Music、Spotify、Apple Music、KKBOX、Chrome、Edge、Firefox** 等播放中的曲目資訊，並生成 100% 全透明、高質感的 HTML5 動畫組件，無縫融入 **OBS Studio** 實況畫面。

* **完全免裝任何瀏覽器外掛** — 只要瀏覽器正在播放音樂，軟體自動即時抓取！
* **滑鼠直接拖曳進 OBS** — 免手動複製貼上，按住模板卡片直接拖進 OBS 即可建立瀏覽器來源！
* **內建 10 款高品質風格模板** — 毛玻璃、賽博龐克、復古黑膠、錄音帶、萌系粉彩等應有盡有。
* **微軟正黑體 UI 專屬字型優化** — 繁體中文曲名與歌手名稱皆以標準清晰的系統無襯線字體完美渲染。

---

### 🚀 快速安裝與使用

#### 方法一：下載免安裝綠色版（推薦，無需安裝 Python）
1. 前往本專案的 [Releases 發行頁面](https://github.com/tokihorokeiya/musicDisplayObs/releases)。
2. 下載最新版的 OBSMusicDisplay-vX.X.X-windows.zip。
3. 將壓縮檔解壓縮至電腦任意資料夾。
4. 點擊 **OBSMusicDisplay.exe** 即可啟動！

#### 方法二：使用 Python 原始碼執行
1. 確保電腦已安裝 Python 3.10 以上版本。
2. 複製本專案原始碼：
   `ash
   git clone https://github.com/tokihorokeiya/musicDisplayObs.git
   cd musicDisplayObs
   `
3. 安裝必要套件：
   `ash
   pip install -r requirements.txt
   `
4. 執行 
un.bat 或輸入：
   `ash
   python main.py
   `

---

### 📺 如何將音樂面板加入 OBS Studio

#### ✨ 方式一：滑鼠直接拖曳至 OBS（最快最方便）
1. 同時開啟 **OBS Music Display 控制面板** 與 **OBS Studio**。
2. 在軟體視窗上方切換至 **「10 款風格模板庫 (拖曳至 OBS)」** 分頁。
3. 滑鼠左鍵按住任一模板上的綠色標籤 **⠿ 按住拖曳至 OBS！**（或直接按住預覽縮圖）。
4. 直接拖曳滑鼠至 OBS 的 **「來源」清單** 或 **「預覽畫布」** 上放開。
5. OBS 將會自動建立對應的 **Browser（瀏覽器）來源**，透明音樂面版立刻上線！

> **⚠️ Windows 管理員權限提醒：** 若 OBS Studio 是以「以系統管理員身分執行」啟動，Windows 安全機制 (UIPI) 會阻擋非管理員程式的拖曳操作。請以一般使用者權限開啟 OBS，或使用下方的方式二複製網址。

#### 📋 方式二：一鍵複製網址加入
1. 在模板庫中點擊欲使用主題右側的 **「📋 複製網址」** 按鈕。
2. 開啟 OBS Studio，在「來源」面板下方點擊 **+** ➔ 選擇 **「瀏覽器」**。
3. 在「網址 (URL)」欄位貼上剛才複製的連結。
4. 將寬度設為 1920，高度設為 700（或精簡小組件模式 1000 × 400）。
5. 點擊 **確定**，全透明實況音樂組件立即開始運作！

---

### 🎨 10 大內建風格主題一覽

| 主題名稱 | 設計風格說明 | 實機預覽截圖 |
|---|---|:---:|
| **1. 毛玻璃漸層 (Glassmorphism)** | 磨砂壓克力毛玻璃卡片，具備動態霓虹邊框光暈與半透明背景 | <img src="static/previews/glassmorphism.png" width="320"> |
| **2. 賽博龐克 (Cyberpunk 2077)** | 霓虹青綠與桃紅 HUD 邊框、數位等化器音波條與科技感跳動效果 | <img src="static/previews/cyberpunk.png" width="320"> |
| **3. 復古黑膠唱片機 (Vinyl)** | 播歌時黑膠唱片從封套中緩緩滑出並持續擬真旋轉，質感滿分 | <img src="static/previews/vinyl.png" width="320"> |
| **4. 極簡浮動膠囊 (Minimal Pill)** | 超低遮擋的極簡圓角膠囊造型，長歌名自動平滑跑馬燈滾動 | <img src="static/previews/minimal_pill.png" width="320"> |
| **5. 復古卡式錄音帶 (Cassette)** | 雙齒輪轉動的懷舊卡帶機芯，手寫復古字體標籤，Lo-Fi 必備 | <img src="static/previews/cassette.png" width="320"> |
| **6. 實況新聞跑馬燈 (Broadcast)** | 專業電視台新聞圖層下三分之一排版，整合播放狀態與時間進度 | <img src="static/previews/broadcast.png" width="320"> |
| **7. 萌系可愛粉彩 (Cute Kawaii)** | 柔和馬卡龍粉彩色調、閃爍星芒、愛心氣泡與可愛甜美圓弧設計 | <img src="static/previews/cute_kawaii.png" width="320"> |
| **8. Spotify 潮流黑綠 (Spotify)** | 經典深色系搭律動翡翠綠條，完美重現現代流行音樂軟體風貌 | <img src="static/previews/spotify.png" width="320"> |
| **9. 暖心 Lo-Fi 書房 (Lo-Fi Cozy)** | 溫暖的暮色鎢絲燈光暈、柔和質感邊框，深夜伴讀與聊天台首選 | <img src="static/previews/lofi_cozy.png" width="320"> |
| **10. 動態島彈動視窗 (Dynamic Island)** | 宛如智慧型手機的流暢物理彈動視窗，曲目切換時動態延展彈跳 | <img src="static/previews/dynamic_island.png" width="320"> |

---

### ⚙️ 網址參數自訂指南

您可以透過修改網址尾端的參數來微調顯示行為：

`
http://localhost:11150/overlay?theme=vinyl&autohide=1&delay=3&w=1920&h=700
`

* 	heme: 指定模板代碼（例如 glassmorphism, cyberpunk, inyl 等）。
* utohide=1: 當音樂暫停或停止播放時，組件自動平滑淡出隱藏。
* delay=3: 音樂暫停後等待多少秒才開始淡出（預設為 3 秒）。
* w 與 h: 畫布寬高像素尺寸（預設為 1920 與 700）。

---

<br>

# 🇯🇵 日本語ユーザーガイド

Windows 環境向けに特化した、ブラウザ拡張機能不要のリアルタイム音楽表示ツールです！Windows 標準のメディア機能（GSMTC）を通じて、**YouTube、YouTube Music、Spotify、Apple Music、Chrome、Edge、Firefox** などの再生中楽曲（タイトル・アーティスト・アルバムアート・進捗バー）を瞬時に取得し、**OBS Studio** 向けの完全透過アニメーションオーバーレイとして描画します。

* **ブラウザ拡張機能一切不要** — ブラウザで音楽を流すだけで自動認識！
* **OBS への直接ドラッグ＆ドロップ対応** — アプリ上のテンプレートを OBS にドラッグするだけでソース登録完了！
* **10 種類の多彩なビジュアルスタイル** — グラスモフィズム、サイバーパンク、レコード、カセットテープ、カワイイなど。
* **日本語（游ゴシック UI）最適化** — 日本語の曲名やアーティスト名も美しい Windows 標準フォントでくっきり表示。

---

### 🚀 クイックスタート

#### 方法 1: Windows 単体実行ファイル版（推奨・Python 不要）
1. [Releases ページ](https://github.com/tokihorokeiya/musicDisplayObs/releases) を開きます。
2. 最新の OBSMusicDisplay-vX.X.X-windows.zip をダウンロードします。
3. ZIP ファイルをお好みのフォルダーに解凍します。
4. **OBSMusicDisplay.exe** をダブルクリックして起動します。

#### 方法 2: Python ソースコードから実行
1. PC に Python 3.10 以上がインストールされていることを確認します。
2. リポジトリをクローン：
   `ash
   git clone https://github.com/tokihorokeiya/musicDisplayObs.git
   cd musicDisplayObs
   `
3. 依存パッケージをインストール：
   `ash
   pip install -r requirements.txt
   `
4. 
un.bat を実行、または以下のコマンドを入力：
   `ash
   python main.py
   `

---

### 📺 OBS Studio への導入手順

#### ✨ 方法 A: ドラッグ＆ドロップで追加（最速）
1. **OBS Music Display** と **OBS Studio** を両方起動します。
2. アプリ上部で **「10 Style Templates (Drag to OBS)」** タブに切り替えます。
3. お好みのテンプレートにある緑色の **⠿ Drag to OBS** バッジ（またはプレビュー画像）を左クリックで長押しします。
4. そのまま OBS Studio の **「ソース」一覧** または **プレビュー画面** へドラッグしてドロップします。
5. OBS に **ブラウザソース** が自動的に作成され、透過オーバーレイが即座に反映されます！

> **⚠️ 管理者権限についての注意：** OBS Studio を「管理者として実行」している場合、Windows のセキュリティ機能 (UIPI) により外部アプリからのドラッグ＆ドロップが無効化されます。OBS を通常権限で起動するか、以下の「方法 B」をご利用ください。

#### 📋 方法 B: URL コピーで追加
1. テンプレート一覧で使いたいテーマの **「📋 Copy URL」** ボタンをクリックします。
2. OBS Studio の「ソース」下部にある **+** をクリック ➔ **「ブラウザ」** を選択します。
3. 「URL」欄にコピーしたアドレスを貼り付けます。
4. 幅を 1920、高さを 700（または小型ウィジェットモード 1000 × 400）に設定します。
5. **「OK」** を押せば完了です！

---

### 🎨 10 種類のスタイルテンプレート一覧

| テーマ名 | 特徴・デザイン説明 | プレビュー画像 |
|---|---|:---:|
| **1. Glassmorphism** | 美しいすりガラス効果、ネオングラデーションの境界線と滑らかなブラー | <img src="static/previews/glassmorphism.png" width="320"> |
| **2. Cyberpunk 2077** | サイバーなネオンカラー、デジタルイコライザーバーと近未来 HUD 風デザイン | <img src="static/previews/cyberpunk.png" width="320"> |
| **3. Vinyl Turntable** | 再生中にジャケットから回転するリアルなアナログレコード盤がスライド | <img src="static/previews/vinyl.png" width="320"> |
| **4. Minimal Pill** | 画面の邪魔をしないコンパクトな角丸カプセル、長い曲名は自動マーキースクロール | <img src="static/previews/minimal_pill.png" width="320"> |
| **5. Retro Cassette** | リールが回転するヴィンテージカセットテープ、手書き風の温かいレトロデザイン | <img src="static/previews/cassette.png" width="320"> |
| **6. Broadcast** | テレビ報道のような下部テロップレイアウト、配信ステータス付き | <img src="static/previews/broadcast.png" width="320"> |
| **7. Cute Kawaii** | パステルマカロンカラー、キラキラ星やハートが浮かぶ愛らしいデザイン | <img src="static/previews/cute_kawaii.png" width="320"> |
| **8. Spotify Card** | Spotify をオマージュしたスタイリッシュなダークカード＆グリーンイコライザー | <img src="static/previews/spotify.png" width="320"> |
| **9. Lo-Fi Cozy** | 落ち着いた間接照明の温かい光、深夜配信や作業用配信にぴったりの空間 | <img src="static/previews/lofi_cozy.png" width="320"> |
| **10. Dynamic Island** | 再生切り替え時にぷるんと伸縮するスマートフォン風のモダンなポップアップ | <img src="static/previews/dynamic_island.png" width="320"> |

---

### ⚙️ パラメータ設定

URL 末尾にパラメータを追加することで、動作を自由にカスタマイズできます：

`
http://localhost:11150/overlay?theme=vinyl&autohide=1&delay=3&w=1920&h=700
`

* 	heme: テンプレート識別名（glassmorphism, cyberpunk, inyl など）
* utohide=1: 音楽を一時停止または停止した際に自動でフェードアウト
* delay=3: 一時停止後、非表示になるまでの待機秒数（デフォルト: 3秒）
* w / h: キャンバスの横幅・縦幅（デフォルト: 1920 × 700）

---

## 📄 License
Released under the [MIT License](LICENSE).
