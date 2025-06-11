# Webアプリ起動検知機能設計書

## 概要
Claude Codeで作成されたWebアプリケーションの起動を自動的に検知し、適切なタイミングでスクリーンショットを撮影する機能の設計。

## 検知手法

### 1. ポート監視による検知
```python
import subprocess
import time
from typing import Set, Dict

class PortMonitor:
    """Webアプリケーションの一般的なポートを監視"""
    
    DEFAULT_PORTS = [
        3000,    # React, Express
        5000,    # Flask, Python
        5173,    # Vite
        8000,    # Django, Python http.server
        8080,    # 汎用
        4200,    # Angular
        3001,    # Create React App (alternative)
        8888,    # Jupyter
        9000,    # PHP
        4000,    # Phoenix
    ]
    
    def __init__(self, ports: List[int] = None):
        self.ports = ports or self.DEFAULT_PORTS
        self.active_apps: Dict[int, AppInfo] = {}
    
    def check_ports(self) -> Dict[int, bool]:
        """指定ポートがリスニング状態かチェック"""
        cmd = "ss -tln | grep -E ':({})'".format('|'.join(map(str, self.ports)))
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        active_ports = {}
        for port in self.ports:
            active_ports[port] = f":{port}" in result.stdout
        
        return active_ports
    
    def detect_new_apps(self) -> List[AppInfo]:
        """新しく起動したWebアプリを検出"""
        current_ports = self.check_ports()
        new_apps = []
        
        for port, is_active in current_ports.items():
            if is_active and port not in self.active_apps:
                # 新しいアプリを検出
                app_info = self._get_app_info(port)
                self.active_apps[port] = app_info
                new_apps.append(app_info)
            elif not is_active and port in self.active_apps:
                # アプリが停止
                del self.active_apps[port]
        
        return new_apps
```

### 2. プロセス監視による検知
```python
class ProcessMonitor:
    """開発サーバープロセスを監視"""
    
    WATCH_COMMANDS = [
        'node.*dev',          # npm run dev
        'webpack-dev-server',
        'vite',
        'next dev',
        'react-scripts start',
        'ng serve',
        'python.*manage.py runserver',  # Django
        'flask run',
        'php.*-S',           # PHP built-in server
        'ruby.*rails server',
    ]
    
    def find_dev_processes(self) -> List[ProcessInfo]:
        """開発サーバープロセスを検索"""
        processes = []
        
        for pattern in self.WATCH_COMMANDS:
            cmd = f"ps aux | grep -E '{pattern}' | grep -v grep"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            for line in result.stdout.strip().split('\n'):
                if line:
                    process_info = self._parse_process_line(line)
                    processes.append(process_info)
        
        return processes
```

### 3. ファイルシステム監視
```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ProjectFileMonitor(FileSystemEventHandler):
    """プロジェクトファイルの変更を監視"""
    
    TRIGGER_FILES = [
        'package.json',
        'package-lock.json',
        '.env.local',
        'webpack.config.js',
        'vite.config.js',
        'next.config.js',
    ]
    
    def on_modified(self, event):
        if event.src_path.endswith(tuple(self.TRIGGER_FILES)):
            # 開発サーバーの再起動を検知
            self._check_for_restart()
```

## 起動検知フロー

### 1. 初回起動検知
```python
class WebAppDetector:
    def __init__(self):
        self.port_monitor = PortMonitor()
        self.process_monitor = ProcessMonitor()
        self.detected_apps = {}
        
    def start_detection(self, callback):
        """検知開始"""
        while True:
            # 1. ポート監視
            new_apps = self.port_monitor.detect_new_apps()
            
            # 2. プロセス確認
            for app in new_apps:
                process_info = self.process_monitor.find_process_for_port(app.port)
                app.process_info = process_info
            
            # 3. 起動確認（HTTPリクエスト）
            for app in new_apps:
                if self._wait_for_app_ready(app):
                    self.detected_apps[app.port] = app
                    callback(app)
            
            time.sleep(2)  # 2秒ごとにチェック
    
    def _wait_for_app_ready(self, app: AppInfo, timeout: int = 30) -> bool:
        """アプリケーションの準備完了を待機"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"http://localhost:{app.port}", timeout=1)
                if response.status_code < 500:  # サーバーエラー以外
                    return True
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(0.5)
        
        return False
```

### 2. アプリケーション情報の取得
```python
@dataclass
class AppInfo:
    port: int
    url: str
    process_name: str
    process_cmd: str
    project_path: str
    framework: str = "unknown"
    
    def detect_framework(self):
        """使用フレームワークを推定"""
        if self.project_path:
            # package.jsonから判定
            package_json = Path(self.project_path) / "package.json"
            if package_json.exists():
                with open(package_json) as f:
                    data = json.load(f)
                    deps = data.get('dependencies', {})
                    
                    if 'react' in deps:
                        self.framework = 'React'
                    elif 'vue' in deps:
                        self.framework = 'Vue'
                    elif '@angular/core' in deps:
                        self.framework = 'Angular'
                    elif 'next' in deps:
                        self.framework = 'Next.js'
```

## ブラウザ起動とスクリーンショット

### 1. 自動ブラウザ起動
```python
from playwright.sync_api import sync_playwright

class AutoBrowser:
    def __init__(self):
        self.playwright = sync_playwright().start()
        self.browser = None
        
    def open_webapp(self, app_info: AppInfo):
        """Webアプリを自動的に開く"""
        if not self.browser:
            self.browser = self.playwright.chromium.launch(headless=False)
        
        context = self.browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()
        
        # コンソールエラーを記録
        page.on('console', lambda msg: self._log_console(msg))
        
        # ページ読み込み
        page.goto(app_info.url)
        
        # 完全に読み込まれるまで待機
        page.wait_for_load_state('networkidle')
        
        return page
    
    def capture_screenshots(self, page, app_info: AppInfo):
        """スクリーンショットを撮影"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_path = Path(f"./screenshots/webapp_{app_info.port}_{timestamp}")
        base_path.mkdir(parents=True, exist_ok=True)
        
        # 1. 初期画面
        page.screenshot(path=base_path / "initial.png", full_page=True)
        
        # 2. エラーチェック
        errors = page.query_selector_all('.error, .alert-danger, [class*="error"]')
        if errors:
            page.screenshot(path=base_path / "errors.png")
        
        # 3. レスポンシブテスト
        viewports = [
            {'name': 'desktop', 'width': 1920, 'height': 1080},
            {'name': 'tablet', 'width': 768, 'height': 1024},
            {'name': 'mobile', 'width': 375, 'height': 667},
        ]
        
        for viewport in viewports:
            page.set_viewport_size(
                width=viewport['width'], 
                height=viewport['height']
            )
            page.screenshot(
                path=base_path / f"{viewport['name']}.png"
            )
        
        return base_path
```

## 設定ファイル

### プロジェクト別設定
```yaml
# .screenshot-manager.yaml
webapp_detection:
  # 監視するポート（デフォルトに追加）
  additional_ports: [3333, 4444]
  
  # 除外するポート
  exclude_ports: [8888]  # Jupyter除外
  
  # 起動待機時間
  startup_timeout: 60  # 秒
  
  # スクリーンショット設定
  capture:
    # 撮影するページ
    pages:
      - "/"
      - "/login"
      - "/dashboard"
    
    # 待機時間（ミリ秒）
    wait_before_capture: 2000
    
    # エラー検出セレクタ
    error_selectors:
      - ".error"
      - ".alert-danger"
      - "[data-testid='error-message']"
    
    # レスポンシブテスト
    viewports:
      desktop:
        width: 1920
        height: 1080
      tablet:
        width: 768
        height: 1024
      mobile:
        width: 375
        height: 667
  
  # 通知設定
  notifications:
    on_startup: true
    on_error: true
    webhook_url: null
```

## 実装例

### 統合実装
```python
#!/usr/bin/env python3
"""Webアプリ自動検知・スクリーンショット撮影"""

import asyncio
from pathlib import Path

class WebAppScreenshotManager:
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.detector = WebAppDetector()
        self.browser = AutoBrowser()
        
    def start(self):
        """監視開始"""
        print("🔍 Webアプリ監視を開始します...")
        self.detector.start_detection(self._on_app_detected)
    
    def _on_app_detected(self, app_info: AppInfo):
        """Webアプリ検出時の処理"""
        print(f"✨ 新しいWebアプリを検出: {app_info.url}")
        print(f"   Framework: {app_info.framework}")
        print(f"   Process: {app_info.process_name}")
        
        # ブラウザで開く
        page = self.browser.open_webapp(app_info)
        
        # スクリーンショット撮影
        screenshot_path = self.browser.capture_screenshots(page, app_info)
        print(f"📸 スクリーンショット保存: {screenshot_path}")
        
        # レポート生成
        self._generate_report(app_info, screenshot_path)
    
    def _generate_report(self, app_info: AppInfo, screenshot_path: Path):
        """HTMLレポート生成"""
        # TODO: 実装
        pass

if __name__ == "__main__":
    manager = WebAppScreenshotManager()
    manager.start()
```

## エラーハンドリング

### 一般的なエラーと対処
1. **ポート競合**: 既に使用中のポートは無視
2. **起動タイムアウト**: 設定可能なタイムアウト時間
3. **ブラウザクラッシュ**: 自動再起動
4. **メモリ不足**: 定期的なリソース解放

---
*設計完了: 2025-06-11*