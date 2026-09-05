# 🎵 OBS 即時音樂動態顯示器

<p align="center">
  <a href="README.md"><b>English</b></a> | 
  <a href="README.zh-TW.md"><b>繁體中文</b></a> | 
  <a href="README.ja.md"><b>日本語</b></a>
</p>

<p align="center">
  <img src="static/showcase.png" alt="OBS 即時音樂顯示器風格展示" width="100%">
</p>

<p align="center">
  <a href="https://github.com/tokihorokeiya/musicDisplayObs/releases"><img src="https://img.shields.io/github/v/release/tokihorokeiya/musicDisplayObs?color=blue&label=最新版本" alt="Release"></a>
  <img src="https://img.shields.io/badge/支援平台-Windows%2010%20%7C%2011-0078D6?logo=windows&logoColor=white" alt="Platform">
  <img src="https://img.shields.io/badge/OBS%20Studio-v28%2B%20相容-black?logo=obsstudio&logoColor=white" alt="OBS Studio">
  <img src="https://img.shields.io/badge/瀏覽器外掛-完全免安裝-success" alt="免外掛">
  <img src="https://img.shields.io/badge/內建模板-10%20款精選風格-8A2BE2" alt="10 款模板">
</p>

---

專為 Windows 實況主設計的免外掛、免設定即時音樂串流顯示工具！透過 Windows 系統媒體服務（GSMTC），直接抓取 **YouTube、YouTube Music、Spotify、Apple Music、KKBOX、Chrome、Edge、Firefox** 等播放中的曲目資訊，並生成 100% 全透明、高質感的 HTML5 動畫組件，無縫融入 **OBS Studio** 實況畫面。

* **完全免裝任何瀏覽器外掛** — 只要瀏覽器正在播放音樂，軟體自動即時抓取！
* **一鍵快速複製 OBS 網址** — 點選模板旁的「複製網址」，貼入 OBS「瀏覽器」來源即可使用。
* **內建 10 款高品質風格模板** — 毛玻璃、賽博龐克、復古黑膠、錄音帶、萌系粉彩等應有盡有。
* **微軟正黑體 UI 專屬字型優化** — 繁體中文曲名與歌手名稱皆以標準清晰的系統字體完美渲染。
* **平滑無抖動進度條與時間顯示** — 精確計算真實播放時間，避免時間倒退或反覆跳動。
* **一鍵直接從 GitHub 線上更新** — 軟體內建版本檢查與自動熱更新功能，升級時完整保留個人自訂設定。
* **系統匣常駐與完整關閉管理** — 關閉視窗時可彈性選擇最小化至右下角系統匣或完全關閉進程。

---

### 🚀 快速安裝與使用

#### 方法一：下載免安裝綠色版（推薦，無需安裝 Python）
1. 前往本專案的 [Releases 發行頁面](https://github.com/tokihorokeiya/musicDisplayObs/releases)。
2. 下載最新版的 `OBSMusicDisplay-vX.X.X-windows.zip`。
3. 將壓縮檔解壓縮至電腦任意資料夾。
4. 點擊 **`OBSMusicDisplay.exe`** 即可啟動！

#### 方法二：使用 Python 原始碼執行
1. 確保電腦已安裝 Python 3.10 以上版本。
2. 複製本專案原始碼：
   ```bash
   git clone https://github.com/tokihorokeiya/musicDisplayObs.git
   cd musicDisplayObs
   ```
3. 安裝必要套件：
   ```bash
   pip install -r requirements.txt
   ```
4. 點擊 `run.bat` 或輸入：
   ```bash
   python main.py
   ```

---

### 📺 如何將音樂面板加入 OBS Studio

您可以透過以下兩種方式輕鬆將音樂顯示器加入 OBS Studio：

#### 方法 A：直接拖曳至 OBS（最推薦、最快速！🚀）
1. 同時開啟 **OBS Music Display** 與 **OBS Studio**。
2. 在軟體中的任意 **模板預覽圖**、**網址方塊** 或 **`⠿ 拖曳至 OBS` 標籤** 上按住滑鼠左鍵，直接拖曳至 **OBS Studio 畫面預覽區（畫布）**。
3. OBS Studio 會自動辨識並彈出提示視窗：
   > *「您已將 URL 拖曳至 OBS。這將會自動新增此連結為來源。是否繼續？」*
4. 點擊 **「是」**，OBS 將自動為您建立好「瀏覽器」來源！
5. 在 OBS 該來源上按右鍵 -> **屬性**，將 **寬度** 設為 `1920`、**高度** 設為 `700`，點擊 **確定** 即可。

#### 方法 B：複製網址並手動貼上
1. 在 OBS Music Display 中，點擊首頁的 **「📋 複製全域網址」** 或模板庫中的 **「📋 複製網址」**。
2. 在 OBS Studio 中：
   - 在「來源」面板下方點擊 **`+`** 號，選擇 **「瀏覽器」**。
   - 在「網址 (URL)」欄位貼上剛才複製的連結 (`Ctrl + V`)。
   - 將寬度設為 `1920`，高度設為 `700`（若使用精簡小組件模式可設為 `1000` × `400`）。
   - 點擊 **確定**。

> [!TIP]
> **🌐 全域模板自動即時同步功能：**
> 若您在 OBS 中加入「全域網址」（`http://localhost:11150/overlay`），未來您只需在軟體首頁切換想使用的模板，OBS 畫面將會即時自動無縫更換為新樣式，完全無需重複至 OBS 複製與貼上網址！

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

| 參數名稱 | 可用數值 | 預設值 | 功能說明 |
|---|---|---|---|
| `theme` | `glassmorphism`, `cyberpunk`, `vinyl` 等 | `glassmorphism` | 指定面板佈局樣式 |
| `autohide` | `1` 或 `0` | `0` | 當音樂暫停或停止播放時，組件自動平滑淡出隱藏 |
| `delay` | 數字（例如 `3`） | `3` | 音樂暫停後等待多少秒才開始淡出 |
| `w` | 像素寬度 | `1920` | 畫布寬度 |
| `h` | 像素高度 | `700` | 畫布高度 |
| `mode` | `1920x700`, `1000x400`, `1920x1080` | `1920x700` | 預設響應式尺寸設定 |

**範例網址：**
```
http://localhost:11150/overlay?theme=cyberpunk&autohide=1&delay=3&w=1920&h=700
```

---

### 📄 開源授權

本專案採用 MIT 授權條款釋出。
