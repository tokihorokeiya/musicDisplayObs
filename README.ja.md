# 🎵 OBS リアルタイム音楽オーバーレイ

<p align="center">
  <a href="README.md"><b>English</b></a> | 
  <a href="README.zh-TW.md"><b>繁體中文</b></a> | 
  <a href="README.ja.md"><b>日本語</b></a>
</p>

<p align="center">
  <img src="static/showcase.png" alt="OBS リアルタイム音楽オーバーレイ テーマ一覧" width="100%">
</p>

<p align="center">
  <a href="https://github.com/tokihorokeiya/musicDisplayObs/releases"><img src="https://img.shields.io/github/v/release/tokihorokeiya/musicDisplayObs?color=blue&label=最新リリース" alt="Release"></a>
  <img src="https://img.shields.io/badge/対応OS-Windows%2010%20%7C%2011-0078D6?logo=windows&logoColor=white" alt="Platform">
  <img src="https://img.shields.io/badge/OBS%20Studio-v28%2B%20対応-black?logo=obsstudio&logoColor=white" alt="OBS Studio">
  <img src="https://img.shields.io/badge/ブラウザ拡張機能-完全不要-success" alt="拡張機能不要">
  <img src="https://img.shields.io/badge/テーマ-19%20種類内蔵-8A2BE2" alt="19 Themes">
</p>

---

Windows 環境向けに特化した、ブラウザ拡張機能不要のリアルタイム音楽表示ツールです！Windows 標準のメディア機能（GSMTC）を通じて、**YouTube、YouTube Music、Spotify、Apple Music、Chrome、Edge、Firefox** などの再生中楽曲（タイトル・アーティスト・アルバムアート・進捗バー）を瞬時に取得し、**OBS Studio** 向けの完全透過アニメーションオーバーレイとして描画します。

* **ブラウザ拡張機能一切不要** — ブラウザで音楽を流すだけで自動認識！
* **OBS 画面へ直接ドラッグ＆ドロップ** — プレビューカードをそのまま OBS キャンバスにドラッグするだけで即座に追加可能。
* **19 種類の多彩なビジュアルスタイル** — グラスモフィズム、スイススタイル、レトロ 70 年代、8-Bit 像素、Bento グリッドなど豊富に内蔵。
* **くっきり滑らかなベクターフォント描画** — 游ゴシック UI、メイリオ、微軟正黑體等の高品質フォントを採用し、ビットマップフォント化を防止。
* **カクつきのないスムーズな進捗＆時間表示** — 経過時間を正確に計算し、巻き戻りや数値の揺れを防止。
* **ワンクリックで GitHub から直接アップデート** — アプリ内から最新版を検知して自動熱更新。個人設定も安全に保持されます。
* **Notion 風ミニマルワークスペース UI** — ポップアップ不要の非同期フローティングトースト通知を採用。
* **システムトレイ＆完全終了対応** — アプリ終了時にトレイへの最小化またはプロセスの完全終了を選択可能。

---

### 🚀 クイックスタート

#### 方法 1: Windows 単体実行ファイル版（推奨・Python 不要）
1. [Releases ページ](https://github.com/tokihorokeiya/musicDisplayObs/releases) を開きます。
2. 最新の `OBSMusicDisplay-vX.X.X-windows.zip` をダウンロードします。
3. ZIP ファイルをお好みのフォルダーに解凍します。
4. **`OBSMusicDisplay.exe`** をダブルクリックして起動します。

#### 方法 2: Python ソースコードから実行
1. PC に Python 3.10 以上がインストールされていることを確認します。
2. リポジトリをクローン：
   ```bash
   git clone https://github.com/tokihorokeiya/musicDisplayObs.git
   cd musicDisplayObs
   ```
3. 依存パッケージをインストール：
   ```bash
   pip install -r requirements.txt
   ```
4. `run.bat` を実行、または以下のコマンドを入力：
   ```bash
   python main.py
   ```

---

### 📺 OBS Studio への追加手順

以下の2つの方法のいずれかで、簡単に音楽オーバーレイを OBS Studio へ追加できます：

#### 方法 A: OBS への直接ドラッグ＆ドロップ（一番簡単＆おすすめ！🚀）
1. **OBS Music Display** と **OBS Studio** を起動します。
2. アプリ内の任意の **テンプレートプレビュー画像**、**URL入力欄**、または **`⠿ OBSへドラッグ` バッジ** をマウスで掴み、そのまま **OBS Studio のプレビュー画面（キャンバス）** へドラッグ＆ドロップします。
3. OBS Studio が自動認識し、確認ダイアログが表示されます：
   > *「URL を OBS にドラッグしました。このリンクをソースとして自動的に追加します。続行しますか？」*
4. **「はい」** をクリックすると、OBS が自動で「ブラウザ」ソースを作成します！
5. 追加されたソースを右クリック -> **プロパティ** を開き、**幅** を `1920`、**高さ** を `700` に設定して **「OK」** をクリックします。

#### 方法 B: URL をコピーして手動で貼り付け
1. OBS Music Display にて、メイン画面の **「📋 グローバルURLをコピー」** またはテンプレートギャラリーの **「📋 URLコピー」** をクリックします。
2. OBS Studio にて：
   - 「ソース」ドック下の **`+`** アイコンをクリックし、**「ブラウザ」** を選択。
   - 「URL」欄にコピーしたリンクを貼り付け (`Ctrl + V`)。
   - **幅** を `1920`、**高さ** を `700` に設定（コンパクトモードの場合は `1000` × `400`）。
   - **「OK」** をクリック。

> [!TIP]
> **🌐 グローバルテンプレート自動同期機能：**
> OBS に「グローバルURL」（`http://localhost:11150/overlay`）を追加しておけば、アプリのメイン画面でお好きなテンプレートを切り替えるだけで、OBS の表示もリアルタイムに自動同期・変更されます。OBS 側で URL を毎回貼り直す必要はありません！

---

### 🎨 19 種類の内蔵テーマ一覧

| テーマ名 | スタイルの特徴 | プレビュー画像 |
|---|---|:---:|
| **1. グラスモフィズム** | すりガラス風のアクリルカード、ネオンバックライトと柔らかな角丸デザイン | <img src="static/previews/glassmorphism.png" width="320"> |
| **2. サイバーパンク 2077** | シアンとマゼンタのネオンが輝く近未来HUD、デジタルタイマー表示付き | <img src="static/previews/cyberpunk.png" width="320"> |
| **3. レトロ レコードプレイヤー** | 音楽再生中にジャケットから滑り出して回転するアナログレコード | <img src="static/previews/vinyl.png" width="320"> |
| **4. ミニマル・フローティングピル** | 極限まで削ぎ落としたスタイリッシュなカプセルバッジ | <img src="static/previews/minimal_pill.png" width="320"> |
| **5. レトロ カセットテープ** | 温かみのある手書きラベルと回転するデュアルスプール | <img src="static/previews/cassette.png" width="320"> |
| **6. ニュース速報風テロップ** | プロ仕様のテレビ風テロップ、洗練されたスライドインアニメーション | <img src="static/previews/broadcast.png" width="320"> |
| **7. カワイイ・パステル** | パステルピンクと星のきらめき、VTuber やアニメ配信に最適 | <img src="static/previews/cute_kawaii.png" width="320"> |
| **8. Spotify スタイル** | 洗練されたダークグリーン配色のストリーミングプレイヤー風カード | <img src="static/previews/spotify.png" width="320"> |
| **9. 暖炉とカフェ Lo-Fi** | ダークウォールナットと琥珀色のアンバーライトで落ち着いた空間を演出 | <img src="static/previews/lofi_cozy.png" width="320"> |
| **10. ダイナミック・アイランド** | Apple風のスプリングバウンドアニメーションが心地よいフローティングバナー | <img src="static/previews/dynamic_island.png" width="320"> |
| **11. ミニマリズム** | 不要な装飾を排し、美しいタイポグラフィとアートワークに集中した極簡構成 | <img src="static/previews/minimalism.png" width="320"> |
| **12. スイス・スタイル** | 国際タイポグラフィ様式、整然とした Helvetica グリッドとシャープな十字アクセント | <img src="static/previews/swiss.png" width="320"> |
| **13. エディトリアル・マガジン** | 雑誌 Vogue や Kinfolk を思わせる高級感あふれるセリフ調ハイファッションレイアウト | <img src="static/previews/editorial.png" width="320"> |
| **14. 手描きスケッチブック** | マスキングテープと紙の繊維質ボーダーが温もりを演出するスクラップブック風 | <img src="static/previews/hand_drawn.png" width="320"> |
| **15. レトロ 70s Hi-Fi** | 黄金期のビンテージステレオアンプとデッキを再現した温かみあるレインボーストライプ | <img src="static/previews/retro.png" width="320"> |
| **16. ピクセル・アーケード** | 80年代アーケードCRTモニター風の走査線とサイバーネオングリッド | <img src="static/previews/pixel.png" width="320"> |
| **17. フラット 2.0** | 大胆なソリッドブロックと美しいコントラストカードによるモダンフラットデザイン | <img src="static/previews/flat.png" width="320"> |
| **18. 8-Bit レトロゲーミング** | ファミコンやゲームボーイを彷彿とさせるグリーン＆ブラックピクセルとHPバー進捗 | <img src="static/previews/eight_bit.png" width="320"> |
| **19. Bento モジュラーグリッド** | Apple風の機能美あふれる弁当箱モジュールカード、音声データを直感的に把握 | <img src="static/previews/bento.png" width="320"> |

---

### ⚙️ URL パラメータ設定

URLの末尾にクエリパラメータを追加することで、表示設定を自由にカスタマイズできます：

| パラメータ | 指定可能な値 | デフォルト値 | 説明 |
|---|---|---|---|
| `theme` | `glassmorphism`, `cyberpunk`, `vinyl` など | `glassmorphism` | テーマデザインの指定 |
| `autohide` | `1` または `0` | `0` | 再生停止・一時停止時に自動で非表示にする |
| `delay` | 秒数（例: `3`） | `3` | 一時停止から非表示になるまでの待機秒数 |
| `w` | 横幅（ピクセル） | `1920` | キャンバスの横幅 |
| `h` | 高さ（ピクセル） | `700` | キャンバスの高さ |
| `mode` | `1920x700`, `1000x400`, `1920x1080` | `1920x700` | プリセット解像度設定 |

**URL 例:**
```
http://localhost:11150/overlay?theme=cyberpunk&autohide=1&delay=3&w=1920&h=700
```

---

### 📄 ライセンス

本プロジェクトは MIT ライセンスの下で公開されています。
