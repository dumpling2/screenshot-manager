# 🏗️ システムアーキテクチャ

Screenshot Manager for WSLの技術仕様とシステム構成について詳しく説明します。

## 📋 システム概要

### コンセプト
Claude Codeで作成したWebアプリケーションの起動後画面を自動的にキャプチャし、動作確認を支援するWSL専用ツール。

### 技術スタック

**基盤技術:**
- **Python 3.8+**: メイン開発言語
- **Bash**: スクリプト・システム統合
- **PowerShell**: Windows連携
- **WSL2**: Linux-Windows統合環境

**主要ライブラリ:**
- **watchdog**: ファイルシステム監視
- **requests**: HTTP通信・Webアプリ検知
- **playwright**: ブラウザ自動化・高度スクリーンショット
- **json**: 設定管理・データ交換

## 🏛️ アーキテクチャ構成

### システム全体図

```
┌─────────────────────────────────────────────────────────────┐
│                        Windows 層                            │
├─────────────────────────────────────────────────────────────┤
│  PowerShell Scripts  │  Screenshots Folder  │  Web Apps     │
│  - take_screenshot   │  - Auto Detection    │  - Port:3000  │
│  - Window Capture    │  - File Monitoring   │  - Port:5173  │
└─────────────────────────────────────────────────────────────┘
                              │ /mnt/c
┌─────────────────────────────────────────────────────────────┐
│                         WSL2 層                             │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
│ │  File Monitor   │ │  Webapp Monitor │ │  Screenshot     │ │
│ │  (v1.0)         │ │  (v2.0)         │ │  Capture        │ │
│ │                 │ │                 │ │                 │ │
│ │ • Watchdog      │ │ • Port Monitor  │ │ • PowerShell    │ │
│ │ • Auto Copy     │ │ • Browser Auto  │ │ • Playwright    │ │
│ │ • Organization  │ │ • Multi-Device  │ │ • Multi-Monitor │ │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘ │
│                              │                              │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │               Configuration Layer                       │ │
│ │  • config.json (Basic)  • webapp_config.json (WebApp) │ │
│ └─────────────────────────────────────────────────────────┘ │
│                              │                              │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │                Storage Layer                            │ │
│ │  • screenshots/ (Images)  • logs/ (Monitoring)         │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### コンポーネント構成

```
screenshot-manager/
├── 🔧 Core Scripts/
│   ├── screenshot_monitor.py      # ファイル監視エンジン (v1.0)
│   ├── webapp_monitor.py          # Webアプリ監視エンジン (v2.0)
│   ├── playwright_capture.py      # ブラウザ自動化
│   └── screenshot_manager.sh      # 統合管理スクリプト
├── 🎯 Screenshot Capture/
│   └── take_screenshot.sh         # 高度撮影機能
├── ⚙️ Configuration/
│   ├── config.json               # 基本設定
│   └── webapp_config.json        # Webアプリ監視設定
├── 📁 Data Storage/
│   ├── screenshots/              # 画像ファイル
│   └── logs/                     # ログ・履歴
├── 🧪 Testing/
│   └── test_webapp_monitor.py    # 統合テスト
└── 📚 Documentation/
    └── docs/                     # ドキュメント体系
```

## 🔄 データフロー

### v1.0: 基本監視フロー

```
[Windows Screenshot] 
       │
       ▼ File System Event
[File Monitor (watchdog)]
       │
       ▼ Detect New File
[Copy & Process]
       │
       ├─ Date Organization
       ├─ Duplicate Detection (MD5)
       └─ Auto Cleanup
       │
       ▼
[Local Storage] ─────────────────► [Transfer Log]
```

### v2.0: Webアプリ監視フロー

```
[Web App Start]
       │
       ▼ Port Listen Detection
[Port Monitor (ss/netstat)]
       │
       ▼ New App Detected
[App Analysis]
       │
       ├─ Framework Detection
       ├─ Process Information
       └─ Health Check (HTTP)
       │
       ▼ App Ready
[Browser Automation (Playwright)]
       │
       ├─ Multiple Viewports
       ├─ Error Detection
       └─ Full Page Capture
       │
       ▼
[Report Generation] ──────────────► [HTML Report]
       │
       ▼
[Screenshot Storage]
```

## 🧩 主要モジュール詳細

### 1. ファイル監視システム (screenshot_monitor.py)

**責任範囲:**
- Windowsスクリーンショットフォルダの監視
- 新規ファイルの自動検出
- ローカルストレージへの転送・整理

**技術実装:**
```python
class ScreenshotMonitor:
    def __init__(self):
        self.observer = Observer()           # watchdog Observer
        self.event_handler = FileHandler()  # カスタムイベントハンドラ
        
    def start_monitoring(self):
        self.observer.schedule(
            self.event_handler,
            self.windows_path,
            recursive=False
        )
```

**主要機能:**
- **リアルタイム監視**: watchdogによるファイルシステムイベント監視
- **重複検出**: MD5ハッシュによる重複ファイル排除
- **自動整理**: 日付ベースのフォルダ構成
- **クリーンアップ**: 設定日数経過後の自動削除

### 2. Webアプリ監視システム (webapp_monitor.py)

**責任範囲:**
- 開発サーバーの起動検知
- Webアプリケーションの健全性確認
- 自動スクリーンショット撮影の調整

**技術実装:**
```python
class PortMonitor:
    DEFAULT_PORTS = [3000, 5000, 5173, 8000, 8080, 4200]
    
    def check_ports(self) -> Dict[int, bool]:
        # ss/netstatコマンドでポート状態確認
        # HTTPリクエストで応答確認
        
    def detect_framework(self, port: int) -> str:
        # HTML内容解析によるフレームワーク推定
        # ヘッダー情報の確認
```

**検知対象ポート:**
- **3000, 3001**: React, Express, Node.js
- **5000**: Flask, Python開発サーバー
- **5173, 5174**: Vite
- **8000**: Django, Python http.server
- **8080**: 汎用Webサーバー
- **4200**: Angular CLI
- **4000**: Phoenix Framework
- **8888**: Jupyter Notebook
- **9000**: PHP Built-in Server

### 3. ブラウザ自動化システム (playwright_capture.py)

**責任範囲:**
- ヘッドレスブラウザの制御
- 複数ビューポートでのスクリーンショット
- エラー要素の自動検出

**技術実装:**
```python
class PlaywrightScreenshotCapture:
    async def capture_webapp_screenshots(self, app_info):
        # Chromiumブラウザ起動
        browser = await playwright.chromium.launch(headless=True)
        
        # 複数ビューポートでキャプチャ
        for device, viewport in viewports.items():
            page.set_viewport_size(**viewport)
            await page.screenshot(path=f"{device}.png")
```

**キャプチャ種類:**
- **Full Page**: ページ全体のスクリーンショット
- **Viewport**: 表示領域のみ
- **Responsive**: Desktop/Tablet/Mobile各解像度
- **Error Detection**: CSSセレクタによるエラー要素検出

## 🔧 設定システム

### 設定階層構造

```
System Defaults (Python Code)
        │
        ▼ Override
User Global Config (~/.screenshot_manager/)
        │
        ▼ Override  
Project Local Config (./config/)
        │
        ▼ Override
Environment Variables
```

### 設定ファイル仕様

**基本設定 (config.json):**
```json
{
  "windowsUsername": "string",           // Windows ユーザー名
  "windowsScreenshotPath": "path",       // Windows スクリーンショットパス
  "localScreenshotPath": "path",         // ローカル保存パス
  "checkInterval": "number",             // 監視間隔(秒)
  "organizeByDate": "boolean",           // 日付別整理
  "autoCleanup": {
    "enabled": "boolean",
    "daysToKeep": "number"               // 保持日数
  }
}
```

**Webアプリ監視設定 (webapp_config.json):**
```json
{
  "check_interval": "number",            // ポートチェック間隔
  "additional_ports": "array",           // 追加監視ポート
  "exclude_ports": "array",              // 除外ポート
  "startup_timeout": "number",           // アプリ起動待機時間
  "capture": {
    "wait_before_capture": "number",     // キャプチャ前待機時間
    "viewports": "object",               // ビューポート設定
    "error_selectors": "array"           // エラー要素セレクタ
  }
}
```

## 🚀 パフォーマンス特性

### メモリ使用量

| コンポーネント | 基本使用量 | ピーク使用量 | 備考 |
|---------------|-----------|-------------|------|
| screenshot_monitor.py | ~15MB | ~30MB | ファイル処理時 |
| webapp_monitor.py | ~20MB | ~40MB | ポート監視時 |
| playwright_capture.py | ~100MB | ~300MB | ブラウザ起動時 |

### CPU使用率

- **アイドル時**: 0.1-0.5%
- **ファイル検出時**: 2-5%
- **Webアプリ検知時**: 5-10%
- **スクリーンショット撮影時**: 15-30%

### ディスク使用量

- **ログファイル**: ~1MB/日
- **設定ファイル**: ~1KB
- **スクリーンショット**: 画質・解像度により 100KB-5MB/枚

## 🔒 セキュリティ考慮事項

### アクセス制御

1. **ファイルシステム**: WSL-Windows間のアクセス権限
2. **ネットワーク**: localhost限定の通信
3. **プロセス**: 最小権限での実行

### データ保護

1. **機密情報**: スクリーンショット内の個人情報
2. **ログ**: 個人識別可能な情報の除外
3. **設定**: API キー等の環境変数化

### 脆弱性対策

1. **入力検証**: ファイルパス・ポート番号の妥当性確認
2. **プロセス分離**: 各コンポーネントの独立実行
3. **権限最小化**: 必要最小限の権限での動作

## 🧪 テスト戦略

### テストレベル

1. **単体テスト**: 個別関数・クラスのテスト
2. **統合テスト**: コンポーネント間連携のテスト
3. **システムテスト**: エンドツーエンドの動作確認

### テスト環境

```python
# 統合テストの例 (test_webapp_monitor.py)
def test_port_detection():
    server = start_test_server(3000)    # テストサーバー起動
    monitor = PortMonitor([3000])       # モニター作成
    apps = monitor.detect_new_apps()    # 検知テスト
    assert len(apps) == 1               # 検証
```

### CI/CD統合

将来的なGitHub Actions連携:
```yaml
name: Integration Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Run Tests
        run: ./test_webapp_monitor.py
```

## 📊 監視・ロギング

### ログレベル

- **DEBUG**: 詳細なトレース情報
- **INFO**: 一般的な動作情報
- **WARNING**: 注意が必要な状況
- **ERROR**: エラー・例外情報

### ログ形式

```
2025-06-11 12:34:56 - webapp_monitor - INFO - ✨ 新しいWebアプリを検出!
2025-06-11 12:34:56 - webapp_monitor - INFO -    URL: http://localhost:3000
2025-06-11 12:34:56 - webapp_monitor - INFO -    Framework: React
```

### メトリクス収集

**転送ログ (transfers.jsonl):**
```json
{"timestamp": "2025-06-11T12:34:56", "source": "screenshot.png", "target": "screenshots/2025-06-11/", "size": 245760, "md5": "abc123..."}
```

**検出ログ (webapp_detections.jsonl):**
```json
{"port": 3000, "url": "http://localhost:3000", "framework": "React", "detected_at": "2025-06-11T12:34:56"}
```

## 🔄 拡張性設計

### プラグインアーキテクチャ（将来計画）

```python
class CapturePlugin:
    def on_app_detected(self, app_info: AppInfo):
        """Webアプリ検出時のフック"""
        pass
    
    def on_screenshot_taken(self, screenshot_path: Path):
        """スクリーンショット撮影後のフック"""
        pass
```

### API化（v5.0計画）

```python
from fastapi import FastAPI
app = FastAPI()

@app.post("/capture")
async def capture_screenshot(request: CaptureRequest):
    """REST API経由でのスクリーンショット撮影"""
    pass
```

## 📈 将来的な技術的改善

### パフォーマンス最適化

1. **非同期処理**: asyncio利用の拡大
2. **キャッシュ**: ファイルハッシュ・プロセス情報のキャッシュ
3. **バッチ処理**: 複数ファイルの一括処理

### 機能拡張

1. **画像解析**: OpenCV/PIL利用の画像処理
2. **AI連携**: 画像内容の自動分析
3. **クラウド連携**: S3/GCS等への自動アップロード

---

関連ドキュメント: [🗺️ ロードマップ](ROADMAP.md) | [🤝 貢献ガイド](CONTRIBUTING.md)