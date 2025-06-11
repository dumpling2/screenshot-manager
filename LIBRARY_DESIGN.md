# ライブラリ化設計仕様書

## 設計方針

### 1. 既存機能の保持
- 現在のスクリプト群は維持
- 後方互換性を保証
- 段階的移行を可能にする

### 2. 簡潔なAPI設計
- 最小限のコードで利用可能
- 他プロジェクトからの import が容易
- 設定の簡素化

## ライブラリ構造

```
screenshot_lib/
├── __init__.py           # メインAPI
├── capture.py           # スクリーンショット撮影
├── monitor.py           # 監視機能
├── metadata.py          # メタデータ管理
├── config.py            # 設定管理
└── utils.py             # 共通ユーティリティ
```

## API設計

### 基本利用パターン
```python
from screenshot_lib import ScreenshotCapture

# 1. 最もシンプルな利用
capture = ScreenshotCapture()
image_path = capture.take_screenshot()

# 2. オプション指定
capture = ScreenshotCapture(save_path="./my_screenshots")
result = capture.take_screenshot(
    monitor=0,
    include_metadata=True,
    filename="test_screenshot.png"
)

# 3. コンテキスト情報付き撮影（AI用途）
result = capture.capture_with_context()
# result = {
#   'image_path': './screenshots/chrome_20250611_123456.png',
#   'metadata': {
#     'timestamp': '2025-06-11T12:34:56',
#     'active_app': 'Chrome',
#     'window_title': 'GitHub - Screenshot Manager',
#     'monitor': 0,
#     'resolution': '1920x1080',
#     'window_bounds': {'x': 0, 'y': 0, 'width': 1920, 'height': 1080}
#   }
# }
```

### 監視機能
```python
from screenshot_lib import ScreenshotMonitor

# 自動監視（従来機能）
monitor = ScreenshotMonitor()
monitor.start()  # バックグラウンド開始

# カスタム設定での監視
monitor = ScreenshotMonitor(
    watch_folder="/mnt/c/Users/user/Pictures/Screenshots",
    save_folder="./ai_screenshots",
    interval=1.0,
    auto_cleanup_days=7
)
monitor.start_with_callback(lambda file_info: process_screenshot(file_info))
```

## メタデータ仕様

### メタデータ形式
```json
{
  "screenshot_id": "uuid-string",
  "timestamp": "2025-06-11T12:34:56.789Z",
  "capture_method": "manual|auto",
  "system_info": {
    "platform": "Windows",
    "wsl_version": "WSL2"
  },
  "display_info": {
    "monitor_count": 2,
    "active_monitor": 0,
    "resolution": "1920x1080",
    "scale_factor": 1.0
  },
  "window_info": {
    "active_app": "chrome",
    "process_name": "chrome.exe",
    "window_title": "GitHub - Screenshot Manager",
    "window_handle": 67938,
    "bounds": {
      "x": 0, "y": 0, "width": 1920, "height": 1080
    }
  },
  "file_info": {
    "original_name": "スクリーンショット 2025-06-11 123456.png",
    "saved_path": "./screenshots/chrome_20250611_123456.png",
    "file_size": 245760,
    "md5_hash": "abc123...",
    "format": "PNG"
  }
}
```

## 設定管理

### 1. 環境変数優先
```bash
export SCREENSHOT_SAVE_PATH="./my_screenshots"
export SCREENSHOT_AUTO_CLEANUP=true
export SCREENSHOT_CLEANUP_DAYS=14
```

### 2. 設定ファイル
```yaml
# ~/.screenshot_config.yaml または ./screenshot_config.yaml
save_path: "./screenshots"
auto_cleanup:
  enabled: true
  days: 7
windows:
  username: "user"
  screenshot_path: "/mnt/c/Users/{username}/Pictures/Screenshots"
metadata:
  include_window_info: true
  include_system_info: true
  extract_text: false  # Phase 2で実装
```

### 3. コード内設定
```python
capture = ScreenshotCapture(
    save_path="./custom_path",
    auto_cleanup_days=30,
    include_metadata=True
)
```

## 実装ステップ

### Step 1: 基本ライブラリ構造作成
- [ ] `screenshot_lib/` ディレクトリ作成
- [ ] 基本的な `__init__.py` 実装
- [ ] `capture.py` で撮影機能を抽出

### Step 2: 既存機能の移植
- [ ] `take_screenshot.sh` の機能をPythonに移植
- [ ] メタデータ収集機能の実装
- [ ] 設定管理システムの実装

### Step 3: 統合テスト
- [ ] 既存スクリプトとの互換性確認
- [ ] 他プロジェクトでのテスト利用
- [ ] パフォーマンステスト

## 利用例とテストケース

### テストケース1: 基本利用
```python
# test_basic.py
from screenshot_lib import ScreenshotCapture

def test_basic_capture():
    capture = ScreenshotCapture()
    result_path = capture.take_screenshot()
    assert os.path.exists(result_path)
    assert result_path.endswith('.png')
```

### テストケース2: メタデータ付き
```python
def test_metadata_capture():
    capture = ScreenshotCapture(include_metadata=True)
    result = capture.capture_with_context()
    
    assert 'image_path' in result
    assert 'metadata' in result
    assert 'timestamp' in result['metadata']
    assert 'active_app' in result['metadata']
```

### テストケース3: 他プロジェクトでの利用
```python
# my_ai_project.py
from screenshot_lib import ScreenshotCapture

class AIAnalyzer:
    def __init__(self):
        self.capture = ScreenshotCapture(
            save_path="./ai_analysis/screenshots",
            include_metadata=True
        )
    
    def analyze_current_screen(self):
        result = self.capture.capture_with_context()
        # AI分析処理
        return self.ai_analyze(result['image_path'], result['metadata'])
```

## 依存関係とパッケージ化

### requirements.txt更新
```
watchdog>=3.0.0
pillow>=9.0.0  # 画像処理用（Phase 2）
pyyaml>=6.0    # 設定ファイル用
```

### setup.py作成（将来的）
```python
from setuptools import setup, find_packages

setup(
    name="screenshot-manager-lib",
    version="2.0.0",
    packages=find_packages(),
    install_requires=[
        "watchdog>=3.0.0",
        "pillow>=9.0.0",
        "pyyaml>=6.0"
    ],
    author="Screenshot Manager Team",
    description="WSL-Windows Screenshot Management Library",
    python_requires=">=3.8"
)
```

---
*設計完了: 2025-06-11*