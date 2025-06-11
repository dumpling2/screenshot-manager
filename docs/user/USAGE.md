# 🎮 使用方法

Screenshot Manager for WSLの機能別使用方法ガイドです。

## 📁 基本監視機能

### 監視の開始・停止

```bash
# 監視を開始（バックグラウンド）
./screenshot_manager.sh start

# 監視を停止
./screenshot_manager.sh stop

# 監視を再起動
./screenshot_manager.sh restart

# 状態を確認
./screenshot_manager.sh status
```

### 監視状況の確認

```bash
# ログを表示
./screenshot_manager.sh logs

# リアルタイムでログを監視
./screenshot_manager.sh logs --tail

# デバッグモード（フォアグラウンドで実行）
./screenshot_manager.sh watch
```

### 設定の変更

```bash
# 設定ファイルを編集
./screenshot_manager.sh config

# または直接編集
nano config/config.json
```

## 📸 高度なスクリーンショット撮影

### モニター指定撮影

```bash
# 利用可能なモニターを表示
./take_screenshot.sh --list-monitors

# 出力例：
# Monitor 0: 1920x1080 at (0,0) (Primary)
# Monitor 1: 1920x1080 at (1920,0)

# 指定モニターのスクリーンショット
./take_screenshot.sh --monitor 0
./take_screenshot.sh --monitor 1 monitor1.png
```

### ウィンドウ指定撮影

```bash
# 実行中のウィンドウを表示
./take_screenshot.sh --list-windows

# 出力例：
# Handle: 67938, Process: chrome, Title: GitHub
# Handle: 52342, Process: Code, Title: Visual Studio Code

# プロセス名で指定
./take_screenshot.sh --process Chrome
./take_screenshot.sh --process Code vscode.png

# ウィンドウハンドルで指定
./take_screenshot.sh --window 67938
```

### 全画面スクリーンショット

```bash
# デフォルト（全画面）
./take_screenshot.sh

# ファイル名を指定
./take_screenshot.sh my_screenshot.png
```

## 🌐 Webアプリ自動監視（v2.0新機能）

### 基本的な監視

```bash
# Webアプリ監視を開始
./webapp_monitor.py

# 監視されるポート：
# 3000, 3001 (React, Express)
# 5000 (Flask)
# 5173, 5174 (Vite)
# 8000 (Django)
# 8080 (汎用)
# 4200 (Angular)
# 4000 (Phoenix)
# 8888 (Jupyter)
# 9000 (PHP)
```

### 実際の使用例

#### パターン1: React アプリの開発

```bash
# 1. Webアプリ監視を開始
./webapp_monitor.py &

# 2. Claude Codeでアプリ作成
claude> "Reactでシンプルなタスク管理アプリを作って"

# 3. 自動的に以下が実行される：
# [INFO] 新しいWebアプリを検出!
# [INFO]    URL: http://localhost:3000
# [INFO]    Framework: React
# [INFO]    Process: node
# [INFO] アプリケーション準備完了: http://localhost:3000
# [INFO] 📸 スクリーンショット撮影完了: ./screenshots/webapp_3000_20250611_123456/
```

#### パターン2: Django アプリの開発

```bash
# 1. Webアプリ監視を開始
./webapp_monitor.py

# 2. Django開発サーバー起動
python manage.py runserver

# 3. 自動検知・スクリーンショット
# [INFO] ✨ 新しいWebアプリを検出!
# [INFO]    URL: http://localhost:8000
# [INFO]    Framework: Django
# [INFO] 📸 Playwrightスクリーンショット完了
```

### 生成されるファイル

スクリーンショット撮影時に以下のファイルが生成されます：

```
screenshots/webapp_3000_20250611_123456/
├── 📱 mobile.png          # モバイル表示
├── 💻 tablet.png          # タブレット表示
├── 🖥️ desktop.png         # デスクトップ表示
├── 📄 main_page.png       # フルページ
├── 👁️ viewport.png        # ビューポート
├── 📊 report.html         # HTMLレポート
├── ℹ️ page_info.json      # ページ情報
└── ❌ errors.json         # エラー情報（あれば）
```

### レポートの確認

```bash
# HTMLレポートを開く
# Windows
explorer.exe screenshots/webapp_3000_*/report.html

# または直接ブラウザで
# http://localhost:8000/screenshots/webapp_3000_*/report.html
```

## ⚙️ 設定のカスタマイズ

### 基本設定の変更

```bash
# 基本設定ファイル
nano config/config.json
```

```json
{
  "windowsUsername": "YourUsername",
  "checkInterval": 2,          // 監視間隔（秒）
  "organizeByDate": true,      // 日付別フォルダ分け
  "maxFileSizeMB": 50,         // 最大ファイルサイズ
  "autoCleanup": {
    "enabled": true,
    "daysToKeep": 7           // 保持日数
  }
}
```

### Webアプリ監視設定の変更

```bash
# Webアプリ監視設定ファイル
nano config/webapp_config.json
```

```json
{
  "check_interval": 2,                    // チェック間隔
  "additional_ports": [3333, 4444],       // 追加監視ポート
  "exclude_ports": [8888],                // 除外ポート
  "startup_timeout": 30,                  // 起動待機時間
  "capture": {
    "wait_before_capture": 2000,          // 撮影前待機時間
    "viewports": {                        // ビューポート設定
      "desktop": {"width": 1920, "height": 1080},
      "tablet": {"width": 768, "height": 1024},
      "mobile": {"width": 375, "height": 667}
    },
    "error_selectors": [                  // エラー要素のセレクタ
      ".error",
      ".alert-danger",
      "[data-testid='error-message']"
    ]
  }
}
```

## 📊 ログとモニタリング

### ログファイルの確認

```bash
# 基本監視ログ
tail -f logs/monitor.log

# Webアプリ監視ログ
tail -f logs/webapp_monitor.log

# 転送ログ（JSONL形式）
tail -f logs/transfers.jsonl

# エラーログ
grep ERROR logs/*.log
```

### 統計情報の確認

```bash
# 転送統計
wc -l logs/transfers.jsonl  # 転送ファイル数

# ディスク使用量
du -sh screenshots/         # スクリーンショットのサイズ

# ログサイズ
du -sh logs/               # ログファイルのサイズ
```

## 🎯 実用的な使用パターン

### パターン1: 日常的な開発

```bash
# 朝の準備
./screenshot_manager.sh start    # 基本監視開始
./webapp_monitor.py &           # Webアプリ監視開始（バックグラウンド）

# 夜の終了
./screenshot_manager.sh stop    # 監視停止
pkill -f webapp_monitor.py      # Webアプリ監視停止
```

### パターン2: プレゼン・デモ用

```bash
# 高品質撮影
./take_screenshot.sh --monitor 0 demo_main.png
./take_screenshot.sh --process Chrome demo_browser.png

# 複数パターンの撮影
./take_screenshot.sh --monitor 0 slide1.png
sleep 10  # 画面変更
./take_screenshot.sh --monitor 0 slide2.png
```

### パターン3: レビュー・共有用

```bash
# 日付ごとのファイル確認
ls screenshots/$(date +%Y-%m-%d)/

# 最新のスクリーンショットを確認
ls -la screenshots/ | tail -5

# 特定アプリのスクリーンショットを検索
find screenshots/ -name "*Chrome*" -type f
```

## 🚀 効率的な使い方のコツ

### 1. 自動起動の活用
```bash
# ~/.bashrcに追加して自動起動
echo 'cd /path/to/screenshot-manager && ./screenshot_manager.sh start' >> ~/.bashrc
```

### 2. エイリアスの設定
```bash
# ~/.bashrcにエイリアス追加
alias ss='cd /path/to/screenshot-manager && ./take_screenshot.sh'
alias ssmon='cd /path/to/screenshot-manager && ./screenshot_manager.sh'
alias ssweb='cd /path/to/screenshot-manager && ./webapp_monitor.py'
```

### 3. 定期実行の設定
```bash
# crontabで定期スクリーンショット
crontab -e

# 毎時0分にスクリーンショット
0 * * * * /path/to/screenshot-manager/take_screenshot.sh hourly_$(date +\%H).png
```

## 🔗 コマンドリファレンス

### 基本管理コマンド

| コマンド | 機能 |
|---------|------|
| `./screenshot_manager.sh start` | 監視開始 |
| `./screenshot_manager.sh stop` | 監視停止 |
| `./screenshot_manager.sh restart` | 監視再起動 |
| `./screenshot_manager.sh status` | 状態確認 |
| `./screenshot_manager.sh logs` | ログ表示 |
| `./screenshot_manager.sh config` | 設定編集 |

### スクリーンショットコマンド

| コマンド | 機能 |
|---------|------|
| `./take_screenshot.sh` | 全画面撮影 |
| `./take_screenshot.sh --list-monitors` | モニター一覧 |
| `./take_screenshot.sh --list-windows` | ウィンドウ一覧 |
| `./take_screenshot.sh --monitor N` | モニターN撮影 |
| `./take_screenshot.sh --process NAME` | プロセス指定撮影 |
| `./take_screenshot.sh --window HANDLE` | ウィンドウ指定撮影 |

### Webアプリ監視コマンド

| コマンド | 機能 |
|---------|------|
| `./webapp_monitor.py` | Webアプリ監視開始 |
| `./test_webapp_monitor.py` | 機能テスト |
| `./install_webapp_deps.sh` | 依存関係インストール |

---

次のステップ: [🔧 トラブルシューティング](TROUBLESHOOTING.md) | [📖 セットアップガイド](SETUP.md)