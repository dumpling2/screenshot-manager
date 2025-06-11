#!/usr/bin/env python3
"""
Webアプリケーション自動検知・スクリーンショット撮影ツール
Claude Codeで作成したWebアプリの起動を検知し、自動的にブラウザでアクセスしてスクリーンショットを撮影
"""

import os
import json
import time
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set, Optional, Tuple
import signal
import sys
import threading
import requests
from dataclasses import dataclass, asdict

@dataclass
class AppInfo:
    """検出されたWebアプリケーションの情報"""
    port: int
    url: str
    process_name: str = ""
    process_cmd: str = ""
    project_path: str = ""
    framework: str = "unknown"
    detected_at: str = ""
    
    def __post_init__(self):
        if not self.url:
            self.url = f"http://localhost:{self.port}"
        if not self.detected_at:
            self.detected_at = datetime.now().isoformat()

class PortMonitor:
    """Webアプリケーションの一般的なポートを監視"""
    
    DEFAULT_PORTS = [
        3000,    # React, Express
        3001,    # Create React App (alternative)
        5000,    # Flask, Python
        5173,    # Vite
        5174,    # Vite (alternative)
        8000,    # Django, Python http.server
        8080,    # 汎用
        8888,    # Jupyter
        4200,    # Angular
        4000,    # Phoenix
        9000,    # PHP
    ]
    
    def __init__(self, ports: List[int] = None, logger=None):
        self.ports = ports or self.DEFAULT_PORTS
        self.active_apps: Dict[int, AppInfo] = {}
        self.logger = logger or logging.getLogger(__name__)
    
    def check_ports(self) -> Dict[int, bool]:
        """指定ポートがリスニング状態かチェック"""
        active_ports = {}
        
        for port in self.ports:
            try:
                # ssコマンドでポート状態をチェック
                cmd = f"ss -tln | grep -E ':{port}\\s'"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                is_active = bool(result.stdout.strip())
                
                # HTTPリクエストで確認
                if is_active:
                    try:
                        response = requests.get(f"http://localhost:{port}", timeout=1)
                        is_active = response.status_code < 500
                    except:
                        # HTTPでアクセスできない場合もポートは開いている
                        pass
                
                active_ports[port] = is_active
                
            except Exception as e:
                self.logger.error(f"ポート{port}のチェック中にエラー: {e}")
                active_ports[port] = False
        
        return active_ports
    
    def get_process_info(self, port: int) -> Optional[Dict[str, str]]:
        """ポートを使用しているプロセス情報を取得"""
        try:
            # lsofを使用してポート情報取得
            cmd = f"lsof -i :{port} -P -n | grep LISTEN"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                if lines:
                    parts = lines[0].split()
                    if len(parts) >= 2:
                        return {
                            'name': parts[0],
                            'pid': parts[1]
                        }
            
            # netstatでも試す
            cmd = f"netstat -tlnp 2>/dev/null | grep :{port}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.stdout:
                # PID/プロセス名を抽出
                import re
                match = re.search(r'(\d+)/([\w\-\.]+)', result.stdout)
                if match:
                    return {
                        'pid': match.group(1),
                        'name': match.group(2)
                    }
                    
        except Exception as e:
            self.logger.debug(f"プロセス情報取得エラー: {e}")
        
        return None
    
    def detect_framework(self, port: int) -> str:
        """使用されているフレームワークを推定"""
        try:
            # HTMLのレスポンスから判定
            response = requests.get(f"http://localhost:{port}", timeout=2)
            content = response.text.lower()
            
            if 'react' in content or '_react' in content:
                return 'React'
            elif 'vue' in content or 'v-' in content:
                return 'Vue'
            elif 'ng-' in content or 'angular' in content:
                return 'Angular'
            elif 'next' in content:
                return 'Next.js'
            elif 'vite' in content:
                return 'Vite'
            
            # ヘッダーから判定
            headers = response.headers
            if 'x-powered-by' in headers:
                powered_by = headers['x-powered-by'].lower()
                if 'express' in powered_by:
                    return 'Express'
                elif 'flask' in powered_by:
                    return 'Flask'
                elif 'django' in powered_by:
                    return 'Django'
                    
        except:
            pass
        
        # ポート番号から推定
        port_framework = {
            3000: 'React/Express',
            5173: 'Vite',
            4200: 'Angular',
            5000: 'Flask',
            8000: 'Django'
        }
        
        return port_framework.get(port, 'unknown')
    
    def detect_new_apps(self) -> List[AppInfo]:
        """新しく起動したWebアプリを検出"""
        current_ports = self.check_ports()
        new_apps = []
        
        for port, is_active in current_ports.items():
            if is_active and port not in self.active_apps:
                # 新しいアプリを検出
                app_info = AppInfo(
                    port=port,
                    url=f"http://localhost:{port}"
                )
                
                # プロセス情報取得
                process_info = self.get_process_info(port)
                if process_info:
                    app_info.process_name = process_info.get('name', '')
                
                # フレームワーク推定
                app_info.framework = self.detect_framework(port)
                
                self.active_apps[port] = app_info
                new_apps.append(app_info)
                
            elif not is_active and port in self.active_apps:
                # アプリが停止
                del self.active_apps[port]
        
        return new_apps

class WebAppMonitor:
    """Webアプリケーション監視メインクラス"""
    
    def __init__(self, config_path: str = None):
        self.config_path = Path(config_path) if config_path else Path(__file__).parent / 'config' / 'webapp_config.json'
        self.setup_logging()
        self.load_config()
        self.port_monitor = PortMonitor(logger=self.logger)
        self.running = True
        self.detected_apps: Dict[int, AppInfo] = {}
        
    def setup_logging(self):
        """ログ設定"""
        log_dir = Path(__file__).parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger('webapp_monitor')
        self.logger.setLevel(logging.INFO)
        
        # ファイルハンドラ
        fh = logging.FileHandler(log_dir / 'webapp_monitor.log')
        fh.setLevel(logging.INFO)
        
        # コンソールハンドラ
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # フォーマット
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
    
    def load_config(self):
        """設定ファイルを読み込む"""
        default_config = {
            'check_interval': 2,
            'additional_ports': [],
            'exclude_ports': [],
            'startup_timeout': 30,
            'capture': {
                'wait_before_capture': 2000,
                'viewports': {
                    'desktop': {'width': 1920, 'height': 1080},
                    'tablet': {'width': 768, 'height': 1024},
                    'mobile': {'width': 375, 'height': 667}
                }
            }
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            except Exception as e:
                self.logger.warning(f"設定ファイル読み込みエラー: {e}")
        
        self.config = default_config
        
        # ポート設定の適用
        all_ports = PortMonitor.DEFAULT_PORTS + self.config.get('additional_ports', [])
        exclude_ports = self.config.get('exclude_ports', [])
        self.monitored_ports = [p for p in all_ports if p not in exclude_ports]
    
    def wait_for_app_ready(self, app_info: AppInfo, timeout: int = None) -> bool:
        """アプリケーションの準備完了を待機"""
        timeout = timeout or self.config.get('startup_timeout', 30)
        start_time = time.time()
        
        self.logger.info(f"アプリケーション準備待機中: {app_info.url}")
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(app_info.url, timeout=1)
                if response.status_code < 500:  # サーバーエラー以外
                    self.logger.info(f"アプリケーション準備完了: {app_info.url}")
                    return True
            except requests.exceptions.ConnectionError:
                pass
            except Exception as e:
                self.logger.debug(f"接続エラー: {e}")
            
            time.sleep(0.5)
        
        self.logger.warning(f"アプリケーション準備タイムアウト: {app_info.url}")
        return False
    
    def capture_screenshots(self, app_info: AppInfo):
        """スクリーンショットを撮影"""
        try:
            # Playwrightがインストールされているかチェック
            result = subprocess.run(['python3', '-c', 'import playwright'], capture_output=True)
            if result.returncode != 0:
                self.logger.warning("Playwrightがインストールされていません。基本的なスクリーンショットのみ撮影します。")
                self.capture_basic_screenshot(app_info)
                return
            
            # Playwrightでスクリーンショット撮影
            self.capture_with_playwright(app_info)
            
        except Exception as e:
            self.logger.error(f"スクリーンショット撮影エラー: {e}")
            self.capture_basic_screenshot(app_info)
    
    def capture_basic_screenshot(self, app_info: AppInfo):
        """基本的なスクリーンショット撮影（take_screenshot.sh使用）"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"webapp_{app_info.framework}_{app_info.port}_{timestamp}.png"
        
        # take_screenshot.shを使用
        script_path = Path(__file__).parent / 'scripts' / 'take_screenshot.sh'
        if script_path.exists():
            cmd = f'"{script_path}" "{filename}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info(f"スクリーンショット保存: {filename}")
            else:
                self.logger.error(f"スクリーンショット撮影失敗: {result.stderr}")
    
    def capture_with_playwright(self, app_info: AppInfo):
        """Playwrightを使用した高度なスクリーンショット撮影"""
        try:
            from src.capture.playwright_capture import capture_webapp_sync
            
            result = capture_webapp_sync(
                app_info=app_info,
                config=self.config,
                logger=self.logger
            )
            
            if result:
                self.logger.info(f"📸 Playwrightスクリーンショット完了: {result}")
            else:
                self.logger.warning("Playwrightスクリーンショット失敗、基本撮影にフォールバック")
                self.capture_basic_screenshot(app_info)
                
        except ImportError:
            self.logger.warning("playwright_capture.py が見つかりません")
            self.capture_basic_screenshot(app_info)
    
    def on_app_detected(self, app_info: AppInfo):
        """Webアプリ検出時の処理"""
        self.logger.info(f"✨ 新しいWebアプリを検出!")
        self.logger.info(f"   URL: {app_info.url}")
        self.logger.info(f"   Framework: {app_info.framework}")
        self.logger.info(f"   Process: {app_info.process_name}")
        
        # アプリの準備完了待機
        if self.wait_for_app_ready(app_info):
            # スクリーンショット撮影
            self.capture_screenshots(app_info)
            
            # 検出履歴を保存
            self.save_detection_log(app_info)
    
    def save_detection_log(self, app_info: AppInfo):
        """検出履歴をログファイルに保存"""
        log_dir = Path(__file__).parent / 'logs'
        log_file = log_dir / 'webapp_detections.jsonl'
        
        try:
            with open(log_file, 'a') as f:
                json.dump(asdict(app_info), f)
                f.write('\n')
        except Exception as e:
            self.logger.error(f"検出ログ保存エラー: {e}")
    
    def run(self):
        """監視メインループ"""
        self.logger.info("🔍 Webアプリ監視を開始します...")
        self.logger.info(f"監視ポート: {self.monitored_ports}")
        
        self.port_monitor.ports = self.monitored_ports
        
        try:
            while self.running:
                # 新しいアプリを検出
                new_apps = self.port_monitor.detect_new_apps()
                
                for app in new_apps:
                    self.detected_apps[app.port] = app
                    # 別スレッドで処理
                    thread = threading.Thread(
                        target=self.on_app_detected,
                        args=(app,)
                    )
                    thread.start()
                
                time.sleep(self.config.get('check_interval', 2))
                
        except KeyboardInterrupt:
            self.logger.info("監視を停止します...")
        except Exception as e:
            self.logger.error(f"監視エラー: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """監視を停止"""
        self.running = False
        self.logger.info("Webアプリ監視を停止しました")

def signal_handler(signum, frame):
    """シグナルハンドラ"""
    sys.exit(0)

def main():
    """メイン関数"""
    # シグナルハンドラ設定
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 監視開始
    monitor = WebAppMonitor()
    monitor.run()

if __name__ == "__main__":
    main()