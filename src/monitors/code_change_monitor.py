#!/usr/bin/env python3
"""
コード変更監視システム - Phase 2.3
Claude Codeでプロジェクトファイルが変更された際に自動的にスクリーンショットを再撮影
"""

import os
import time
import asyncio
import logging
import threading
from pathlib import Path
from typing import Dict, Set, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    FileSystemEventHandler = object  # フォールバック

@dataclass
class ChangeEvent:
    """ファイル変更イベント"""
    file_path: str
    event_type: str  # 'modified', 'created', 'deleted'
    timestamp: datetime = field(default_factory=datetime.now)
    project_path: str = ""
    framework: str = ""

@dataclass 
class ProjectWatchConfig:
    """プロジェクト監視設定"""
    project_path: str
    framework: str
    watch_patterns: List[str] = field(default_factory=list)
    exclude_patterns: List[str] = field(default_factory=list)
    debounce_seconds: float = 2.0
    auto_screenshot: bool = True
    notify_claude_code: bool = True

class CodeChangeHandler(FileSystemEventHandler):
    """ファイル変更イベントハンドラ"""
    
    def __init__(self, monitor, project_config: ProjectWatchConfig):
        self.monitor = monitor
        self.config = project_config
        self.logger = monitor.logger
        
        # デフォルト監視パターン
        self.default_patterns = {
            'React': ['.js', '.jsx', '.ts', '.tsx', '.css', '.scss', '.json'],
            'Vue': ['.vue', '.js', '.ts', '.css', '.scss', '.json'],
            'Angular': ['.ts', '.js', '.html', '.css', '.scss', '.json'],
            'Next.js': ['.js', '.jsx', '.ts', '.tsx', '.css', '.scss', '.json'],
            'Django': ['.py', '.html', '.css', '.js', '.json'],
            'Flask': ['.py', '.html', '.css', '.js', '.json'],
            'Express': ['.js', '.ts', '.json', '.html', '.css'],
            'Vite': ['.js', '.jsx', '.ts', '.tsx', '.vue', '.css', '.scss']
        }
        
        # 除外パターン
        self.exclude_patterns = [
            'node_modules', '.git', '__pycache__', '.venv', 'venv',
            'dist', 'build', '.next', '.nuxt', 'coverage',
            '.pyc', '.log', '.tmp', '.cache', 'screenshots'
        ]
    
    def should_watch_file(self, file_path: str) -> bool:
        """ファイルを監視対象にするかどうか判定"""
        path = Path(file_path)
        
        # 除外パターンチェック
        for exclude in self.exclude_patterns:
            if exclude in str(path):
                return False
        
        # 拡張子チェック
        watch_patterns = (self.config.watch_patterns or 
                         self.default_patterns.get(self.config.framework, []))
        
        if watch_patterns:
            return any(str(path).endswith(pattern) for pattern in watch_patterns)
        
        return False
    
    def on_modified(self, event):
        """ファイル修正イベント"""
        if not event.is_directory and self.should_watch_file(event.src_path):
            change_event = ChangeEvent(
                file_path=event.src_path,
                event_type='modified',
                project_path=self.config.project_path,
                framework=self.config.framework
            )
            self.monitor.handle_change_event(change_event)
    
    def on_created(self, event):
        """ファイル作成イベント"""
        if not event.is_directory and self.should_watch_file(event.src_path):
            change_event = ChangeEvent(
                file_path=event.src_path,
                event_type='created',
                project_path=self.config.project_path,
                framework=self.config.framework
            )
            self.monitor.handle_change_event(change_event)

class CodeChangeMonitor:
    """コード変更監視メインクラス"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or self._setup_default_logger()
        self.observers: Dict[str, Observer] = {}
        self.watch_configs: Dict[str, ProjectWatchConfig] = {}
        self.pending_changes: Dict[str, List[ChangeEvent]] = {}
        self.debounce_timers: Dict[str, threading.Timer] = {}
        self.running = False
        
    def _setup_default_logger(self) -> logging.Logger:
        """デフォルトロガー設定"""
        logger = logging.getLogger('code_change_monitor')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    async def add_project_watch(self, config: ProjectWatchConfig) -> bool:
        """プロジェクト監視を追加"""
        if not WATCHDOG_AVAILABLE:
            self.logger.error("watchdog ライブラリが利用できません")
            return False
        
        project_path = Path(config.project_path)
        if not project_path.exists():
            self.logger.error(f"プロジェクトパスが存在しません: {project_path}")
            return False
        
        project_key = str(project_path.resolve())
        
        # 既存の監視を停止
        if project_key in self.observers:
            await self.remove_project_watch(project_key)
        
        try:
            # 新しい監視を開始
            observer = Observer()
            handler = CodeChangeHandler(self, config)
            
            observer.schedule(handler, str(project_path), recursive=True)
            observer.start()
            
            self.observers[project_key] = observer
            self.watch_configs[project_key] = config
            self.pending_changes[project_key] = []
            
            self.logger.info(f"✅ プロジェクト監視開始: {config.framework} ({project_path})")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ プロジェクト監視開始エラー: {e}")
            return False
    
    async def remove_project_watch(self, project_key: str) -> bool:
        """プロジェクト監視を削除"""
        try:
            if project_key in self.observers:
                observer = self.observers[project_key]
                observer.stop()
                observer.join()
                del self.observers[project_key]
            
            if project_key in self.watch_configs:
                del self.watch_configs[project_key]
            
            if project_key in self.pending_changes:
                del self.pending_changes[project_key]
            
            if project_key in self.debounce_timers:
                self.debounce_timers[project_key].cancel()
                del self.debounce_timers[project_key]
            
            self.logger.info(f"🛑 プロジェクト監視停止: {project_key}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ プロジェクト監視停止エラー: {e}")
            return False
    
    def handle_change_event(self, event: ChangeEvent):
        """ファイル変更イベントを処理"""
        project_key = str(Path(event.project_path).resolve())
        
        if project_key not in self.pending_changes:
            return
        
        self.pending_changes[project_key].append(event)
        
        self.logger.info(f"📝 ファイル変更検知: {Path(event.file_path).name} ({event.event_type})")
        
        # デバウンスタイマーを設定
        config = self.watch_configs.get(project_key)
        if config:
            self._setup_debounce_timer(project_key, config.debounce_seconds)
    
    def _setup_debounce_timer(self, project_key: str, debounce_seconds: float):
        """デバウンスタイマーを設定"""
        # 既存のタイマーをキャンセル
        if project_key in self.debounce_timers:
            self.debounce_timers[project_key].cancel()
        
        # 新しいタイマーを設定
        timer = threading.Timer(
            debounce_seconds,
            self._process_pending_changes,
            args=[project_key]
        )
        timer.start()
        self.debounce_timers[project_key] = timer
    
    def _process_pending_changes(self, project_key: str):
        """保留中の変更を処理"""
        if project_key not in self.pending_changes:
            return
        
        changes = self.pending_changes[project_key]
        if not changes:
            return
        
        # 変更をクリア
        self.pending_changes[project_key] = []
        
        # 変更の統計
        modified_files = [c for c in changes if c.event_type == 'modified']
        created_files = [c for c in changes if c.event_type == 'created']
        
        self.logger.info(f"⚡ 変更処理開始: {len(modified_files)}修正, {len(created_files)}新規")
        
        # 非同期でスクリーンショット撮影を実行
        config = self.watch_configs.get(project_key)
        if config and config.auto_screenshot:
            # イベントループが実行中かチェックして非同期タスクを作成
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self._take_auto_screenshot(config, changes))
            except RuntimeError:
                # イベントループが実行中でない場合は新しいループで実行
                asyncio.run(self._take_auto_screenshot(config, changes))
    
    async def _take_auto_screenshot(self, config: ProjectWatchConfig, changes: List[ChangeEvent]):
        """自動スクリーンショット撮影"""
        try:
            self.logger.info(f"📸 自動スクリーンショット撮影開始: {config.framework}プロジェクト")
            
            # MCP統合を使用してスクリーンショット撮影
            from ..integrations.mcp_server import ClaudeCodeIntegration
            
            result = await ClaudeCodeIntegration.take_manual_screenshot(
                config.project_path,
                pages=['/']  # とりあえずトップページのみ
            )
            
            if result['success']:
                self.logger.info("✅ 自動スクリーンショット完了")
                
                # Claude Codeに通知
                if config.notify_claude_code:
                    await self._notify_claude_code(config, changes, result)
            else:
                self.logger.error(f"❌ 自動スクリーンショット失敗: {result.get('error', '')}")
                
        except Exception as e:
            self.logger.error(f"❌ 自動スクリーンショットエラー: {e}")
    
    async def _notify_claude_code(self, config: ProjectWatchConfig, changes: List[ChangeEvent], 
                                  screenshot_result: Dict):
        """Claude Codeに変更とスクリーンショット結果を通知"""
        try:
            notification = {
                'type': 'code_change_detected',
                'project_path': config.project_path,
                'framework': config.framework,
                'timestamp': datetime.now().isoformat(),
                'changes': {
                    'total_files': len(changes),
                    'modified_files': len([c for c in changes if c.event_type == 'modified']),
                    'created_files': len([c for c in changes if c.event_type == 'created']),
                    'file_list': [Path(c.file_path).name for c in changes[:5]]  # 最初の5ファイル
                },
                'screenshot_result': screenshot_result
            }
            
            self.logger.info(f"📡 Claude Code通知: {len(changes)}ファイル変更")
            
            # 実際の通知実装は将来のHTTP/WebSocket接続で行う
            # 現在はログ出力のみ
            self.logger.debug(f"通知内容: {json.dumps(notification, indent=2, ensure_ascii=False)}")
            
        except Exception as e:
            self.logger.error(f"❌ Claude Code通知エラー: {e}")
    
    async def start_monitoring(self):
        """監視開始"""
        if self.running:
            return
        
        self.running = True
        self.logger.info("🚀 コード変更監視システム開始")
        
        if not WATCHDOG_AVAILABLE:
            self.logger.warning("⚠️ watchdog ライブラリが利用できません。監視機能は制限されます")
    
    async def stop_monitoring(self):
        """監視停止"""
        if not self.running:
            return
        
        self.running = False
        
        # すべての監視を停止
        for project_key in list(self.observers.keys()):
            await self.remove_project_watch(project_key)
        
        # すべてのタイマーをキャンセル
        for timer in self.debounce_timers.values():
            timer.cancel()
        self.debounce_timers.clear()
        
        self.logger.info("🛑 コード変更監視システム停止")
    
    def get_status(self) -> Dict:
        """監視状況を取得"""
        return {
            'running': self.running,
            'watchdog_available': WATCHDOG_AVAILABLE,
            'watched_projects': len(self.observers),
            'project_list': [
                {
                    'path': config.project_path,
                    'framework': config.framework,
                    'auto_screenshot': config.auto_screenshot
                }
                for config in self.watch_configs.values()
            ],
            'pending_changes_count': sum(len(changes) for changes in self.pending_changes.values())
        }

# 便利関数
async def create_project_watch_config(project_path: str, framework: str = None) -> ProjectWatchConfig:
    """プロジェクト監視設定を作成"""
    if not framework:
        # プロジェクト検出を試行
        try:
            from ..detectors.project_detector import ProjectDetector
            detector = ProjectDetector()
            project_info = detector.detect_project(Path(project_path))
            framework = project_info.framework if project_info else 'unknown'
        except:
            framework = 'unknown'
    
    return ProjectWatchConfig(
        project_path=project_path,
        framework=framework,
        debounce_seconds=2.0,
        auto_screenshot=True,
        notify_claude_code=True
    )

# テスト用関数
async def test_code_change_monitor():
    """コード変更監視のテスト"""
    monitor = CodeChangeMonitor()
    
    # テスト用プロジェクト設定
    test_project = Path(__file__).parent.parent.parent / "demo_vue_project"
    config = await create_project_watch_config(str(test_project), "Vue")
    
    await monitor.start_monitoring()
    success = await monitor.add_project_watch(config)
    
    if success:
        print(f"✅ 監視開始: {test_project}")
        print("ファイルを変更してテストしてください...")
        
        # 10秒間監視
        await asyncio.sleep(10)
        
        status = monitor.get_status()
        print(f"監視状況: {status}")
    else:
        print("❌ 監視開始失敗")
    
    await monitor.stop_monitoring()

if __name__ == "__main__":
    asyncio.run(test_code_change_monitor())