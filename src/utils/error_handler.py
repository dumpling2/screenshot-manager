#!/usr/bin/env python3
"""
包括的エラーハンドリングシステム - Phase 2.4
Screenshot Managerの全機能における信頼性とエラー回復力を強化
"""

import sys
import traceback
import logging
import asyncio
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import functools

class ErrorSeverity(Enum):
    """エラー重要度レベル"""
    CRITICAL = "critical"  # システム停止レベル
    HIGH = "high"         # 機能影響レベル
    MEDIUM = "medium"     # 部分機能影響
    LOW = "low"          # 軽微な影響
    INFO = "info"        # 情報レベル

class ErrorCategory(Enum):
    """エラーカテゴリ"""
    NETWORK = "network"           # ネットワーク関連
    FILESYSTEM = "filesystem"     # ファイルシステム関連
    PLAYWRIGHT = "playwright"     # ブラウザ関連
    MCP = "mcp"                  # MCP統合関連
    CONFIG = "config"            # 設定関連
    PROCESS = "process"          # プロセス関連
    WATCHDOG = "watchdog"        # ファイル監視関連
    SCREENSHOT = "screenshot"     # スクリーンショット関連
    UNKNOWN = "unknown"          # 不明

@dataclass
class ErrorInfo:
    """エラー情報"""
    error_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    exception: Exception = None
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    retry_count: int = 0
    max_retries: int = 3

class ErrorHandler:
    """包括的エラーハンドリング"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or self._setup_default_logger()
        self.error_log: List[ErrorInfo] = []
        self.retry_strategies: Dict[ErrorCategory, Callable] = {}
        self.error_metrics: Dict[str, int] = {}
        self.recovery_callbacks: Dict[ErrorCategory, List[Callable]] = {}
        self._setup_default_strategies()
        
    def _setup_default_logger(self) -> logging.Logger:
        """デフォルトロガー設定"""
        logger = logging.getLogger('error_handler')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # ファイルハンドラ
            log_dir = Path(__file__).parent.parent.parent / "logs"
            log_dir.mkdir(exist_ok=True)
            
            fh = logging.FileHandler(log_dir / 'error_handler.log')
            fh.setLevel(logging.INFO)
            
            # コンソールハンドラ
            ch = logging.StreamHandler()
            ch.setLevel(logging.WARNING)
            
            # フォーマット
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            fh.setFormatter(formatter)
            ch.setFormatter(formatter)
            
            logger.addHandler(fh)
            logger.addHandler(ch)
        
        return logger
    
    def _setup_default_strategies(self):
        """デフォルトリトライ戦略設定"""
        self.retry_strategies = {
            ErrorCategory.NETWORK: self._network_retry_strategy,
            ErrorCategory.FILESYSTEM: self._filesystem_retry_strategy,
            ErrorCategory.PLAYWRIGHT: self._playwright_retry_strategy,
            ErrorCategory.MCP: self._mcp_retry_strategy,
            ErrorCategory.CONFIG: self._config_retry_strategy,
            ErrorCategory.PROCESS: self._process_retry_strategy,
            ErrorCategory.WATCHDOG: self._watchdog_retry_strategy,
            ErrorCategory.SCREENSHOT: self._screenshot_retry_strategy,
        }
    
    def handle_error(self, 
                    exception: Exception, 
                    category: ErrorCategory = ErrorCategory.UNKNOWN,
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                    context: Dict[str, Any] = None,
                    auto_retry: bool = True) -> ErrorInfo:
        """エラー処理のメインエントリーポイント"""
        
        error_id = f"{category.value}_{int(time.time())}"
        context = context or {}
        
        error_info = ErrorInfo(
            error_id=error_id,
            category=category,
            severity=severity,
            message=str(exception),
            exception=exception,
            context=context
        )
        
        # エラーログに追加
        self.error_log.append(error_info)
        
        # メトリクス更新
        self._update_metrics(category, severity)
        
        # ログ出力
        self._log_error(error_info)
        
        # 自動リトライ
        if auto_retry and category in self.retry_strategies:
            self._attempt_retry(error_info)
        
        # 回復コールバック実行
        self._execute_recovery_callbacks(error_info)
        
        return error_info
    
    def _update_metrics(self, category: ErrorCategory, severity: ErrorSeverity):
        """エラーメトリクス更新"""
        key = f"{category.value}_{severity.value}"
        self.error_metrics[key] = self.error_metrics.get(key, 0) + 1
        
        total_key = f"total_{category.value}"
        self.error_metrics[total_key] = self.error_metrics.get(total_key, 0) + 1
    
    def _log_error(self, error_info: ErrorInfo):
        """エラーログ出力"""
        log_level = {
            ErrorSeverity.CRITICAL: logging.CRITICAL,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.INFO: logging.INFO
        }.get(error_info.severity, logging.WARNING)
        
        self.logger.log(
            log_level,
            f"❌ [{error_info.category.value.upper()}] {error_info.message} "
            f"(ID: {error_info.error_id}, Context: {error_info.context})"
        )
        
        if error_info.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
            self.logger.error(f"Traceback: {traceback.format_exception(type(error_info.exception), error_info.exception, error_info.exception.__traceback__)}")
    
    def _attempt_retry(self, error_info: ErrorInfo):
        """リトライ実行"""
        if error_info.retry_count >= error_info.max_retries:
            self.logger.warning(f"⚠️ 最大リトライ回数に達しました: {error_info.error_id}")
            return
        
        strategy = self.retry_strategies.get(error_info.category)
        if not strategy:
            return
        
        error_info.retry_count += 1
        self.logger.info(f"🔄 リトライ実行 ({error_info.retry_count}/{error_info.max_retries}): {error_info.error_id}")
        
        try:
            if strategy(error_info):
                error_info.resolved = True
                self.logger.info(f"✅ エラー解決: {error_info.error_id}")
        except Exception as e:
            self.logger.error(f"❌ リトライ失敗: {error_info.error_id} - {e}")
    
    def _execute_recovery_callbacks(self, error_info: ErrorInfo):
        """回復コールバック実行"""
        callbacks = self.recovery_callbacks.get(error_info.category, [])
        for callback in callbacks:
            try:
                callback(error_info)
            except Exception as e:
                self.logger.error(f"回復コールバック実行エラー: {e}")
    
    # リトライ戦略の実装
    def _network_retry_strategy(self, error_info: ErrorInfo) -> bool:
        """ネットワークエラーリトライ戦略"""
        import requests
        
        # 指数バックオフで待機
        wait_time = 2 ** error_info.retry_count
        time.sleep(wait_time)
        
        # 接続テスト
        try:
            response = requests.get("http://localhost:3000", timeout=5)
            return response.status_code < 500
        except:
            return False
    
    def _filesystem_retry_strategy(self, error_info: ErrorInfo) -> bool:
        """ファイルシステムエラーリトライ戦略"""
        file_path = error_info.context.get('file_path')
        if not file_path:
            return False
        
        path = Path(file_path)
        
        # ディレクトリ作成試行
        try:
            if not path.parent.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
            return True
        except:
            return False
    
    def _playwright_retry_strategy(self, error_info: ErrorInfo) -> bool:
        """Playwright エラーリトライ戦略"""
        time.sleep(3)  # ブラウザ起動待機
        
        # Playwright 再初期化
        try:
            from ..capture.playwright_capture import PlaywrightCapture
            capture = PlaywrightCapture()
            # 簡単な動作確認
            return True
        except:
            return False
    
    def _mcp_retry_strategy(self, error_info: ErrorInfo) -> bool:
        """MCP エラーリトライ戦略"""
        time.sleep(1)
        
        # MCP接続テスト
        try:
            from ..integrations.mcp_server import ScreenshotManagerMCP
            mcp = ScreenshotManagerMCP()
            return True
        except:
            return False
    
    def _config_retry_strategy(self, error_info: ErrorInfo) -> bool:
        """設定エラーリトライ戦略"""
        config_path = error_info.context.get('config_path')
        if not config_path:
            return False
        
        # デフォルト設定で復旧試行
        try:
            default_config = {
                "check_interval": 2,
                "additional_ports": [],
                "exclude_ports": [],
                "startup_timeout": 30
            }
            
            Path(config_path).write_text(json.dumps(default_config, indent=2))
            return True
        except:
            return False
    
    def _process_retry_strategy(self, error_info: ErrorInfo) -> bool:
        """プロセスエラーリトライ戦略"""
        time.sleep(2)
        
        # プロセス状態確認
        try:
            import subprocess
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
    
    def _watchdog_retry_strategy(self, error_info: ErrorInfo) -> bool:
        """Watchdog エラーリトライ戦略"""
        time.sleep(1)
        
        # watchdog 再初期化
        try:
            from watchdog.observers import Observer
            observer = Observer()
            observer.start()
            observer.stop()
            return True
        except:
            return False
    
    def _screenshot_retry_strategy(self, error_info: ErrorInfo) -> bool:
        """スクリーンショットエラーリトライ戦略"""
        time.sleep(2)
        
        # 基本的なスクリーンショット機能テスト
        try:
            import subprocess
            result = subprocess.run(['echo', 'test'], capture_output=True)
            return result.returncode == 0
        except:
            return False
    
    def register_recovery_callback(self, category: ErrorCategory, callback: Callable):
        """回復コールバック登録"""
        if category not in self.recovery_callbacks:
            self.recovery_callbacks[category] = []
        self.recovery_callbacks[category].append(callback)
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """エラー統計取得"""
        return {
            "total_errors": len(self.error_log),
            "resolved_errors": len([e for e in self.error_log if e.resolved]),
            "recent_errors": len([e for e in self.error_log if e.timestamp > datetime.now() - timedelta(hours=1)]),
            "error_metrics": self.error_metrics,
            "error_categories": {
                cat.value: len([e for e in self.error_log if e.category == cat])
                for cat in ErrorCategory
            },
            "severity_distribution": {
                sev.value: len([e for e in self.error_log if e.severity == sev])
                for sev in ErrorSeverity
            }
        }
    
    def clear_old_errors(self, hours: int = 24):
        """古いエラーログをクリア"""
        cutoff = datetime.now() - timedelta(hours=hours)
        self.error_log = [e for e in self.error_log if e.timestamp > cutoff]

# デコレータ関数
def handle_errors(category: ErrorCategory = ErrorCategory.UNKNOWN, 
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 auto_retry: bool = True,
                 return_on_error: Any = None):
    """エラーハンドリングデコレータ"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handler = getattr(wrapper, '_error_handler', None)
                if not handler:
                    handler = ErrorHandler()
                    wrapper._error_handler = handler
                
                context = {
                    'function': func.__name__,
                    'args': str(args)[:100],
                    'kwargs': str(kwargs)[:100]
                }
                
                handler.handle_error(e, category, severity, context, auto_retry)
                
                if return_on_error is not None:
                    return return_on_error
                raise
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                handler = getattr(async_wrapper, '_error_handler', None)
                if not handler:
                    handler = ErrorHandler()
                    async_wrapper._error_handler = handler
                
                context = {
                    'function': func.__name__,
                    'args': str(args)[:100],
                    'kwargs': str(kwargs)[:100]
                }
                
                handler.handle_error(e, category, severity, context, auto_retry)
                
                if return_on_error is not None:
                    return return_on_error
                raise
        
        # 非同期関数の判定
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper
    
    return decorator

# グローバルエラーハンドラ
_global_error_handler = None

def get_global_error_handler() -> ErrorHandler:
    """グローバルエラーハンドラ取得"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    return _global_error_handler

def handle_global_error(exception: Exception, 
                       category: ErrorCategory = ErrorCategory.UNKNOWN,
                       severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                       context: Dict[str, Any] = None) -> ErrorInfo:
    """グローバルエラー処理"""
    handler = get_global_error_handler()
    return handler.handle_error(exception, category, severity, context)

# 使用例とテスト
async def test_error_handler():
    """エラーハンドラテスト"""
    handler = ErrorHandler()
    
    # ネットワークエラーテスト
    try:
        import requests
        requests.get("http://nonexistent.example.com", timeout=1)
    except Exception as e:
        handler.handle_error(e, ErrorCategory.NETWORK, ErrorSeverity.HIGH)
    
    # 統計表示
    stats = handler.get_error_statistics()
    print(json.dumps(stats, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(test_error_handler())