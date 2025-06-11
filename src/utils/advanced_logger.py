#!/usr/bin/env python3
"""
高度ログ・監視システム - Phase 2.4
構造化ログ、メトリクス収集、リアルタイム監視機能を提供
"""

import os
import json
import logging
import logging.handlers
import asyncio
import time
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from collections import deque, defaultdict
from enum import Enum
import sys
import traceback
import gzip
import re

class LogLevel(Enum):
    """ログレベル"""
    TRACE = 5
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

class MetricType(Enum):
    """メトリクスタイプ"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

@dataclass
class LogEntry:
    """構造化ログエントリ"""
    timestamp: datetime = field(default_factory=datetime.now)
    level: str = "INFO"
    message: str = ""
    component: str = ""
    function: str = ""
    file: str = ""
    line: int = 0
    thread_id: str = ""
    process_id: int = field(default_factory=os.getpid)
    context: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    duration_ms: Optional[float] = None
    error_details: Optional[Dict[str, Any]] = None

@dataclass
class MetricEntry:
    """メトリクスエントリ"""
    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)
    unit: str = ""

class StructuredFormatter(logging.Formatter):
    """構造化ログフォーマッター"""
    
    def format(self, record):
        """ログレコードをJSON形式にフォーマット"""
        log_entry = LogEntry(
            timestamp=datetime.fromtimestamp(record.created),
            level=record.levelname,
            message=record.getMessage(),
            component=getattr(record, 'component', ''),
            function=record.funcName,
            file=record.filename,
            line=record.lineno,
            thread_id=str(record.thread),
            context=getattr(record, 'context', {}),
            tags=getattr(record, 'tags', []),
            duration_ms=getattr(record, 'duration_ms', None),
            error_details=self._extract_error_details(record)
        )
        
        return json.dumps(asdict(log_entry), default=str, ensure_ascii=False)
    
    def _extract_error_details(self, record) -> Optional[Dict[str, Any]]:
        """エラー詳細抽出"""
        if record.exc_info:
            exc_type, exc_value, exc_traceback = record.exc_info
            return {
                "exception_type": exc_type.__name__ if exc_type else None,
                "exception_message": str(exc_value) if exc_value else None,
                "traceback": traceback.format_exception(exc_type, exc_value, exc_traceback)
            }
        return None

class MetricsCollector:
    """メトリクス収集器"""
    
    def __init__(self, max_entries: int = 10000):
        self.max_entries = max_entries
        self.metrics: deque = deque(maxlen=max_entries)
        self.aggregated_metrics: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self._lock = threading.RLock()
    
    def record_metric(self, name: str, value: float, 
                     metric_type: MetricType = MetricType.GAUGE,
                     tags: Dict[str, str] = None, unit: str = ""):
        """メトリクス記録"""
        with self._lock:
            entry = MetricEntry(
                name=name,
                value=value,
                metric_type=metric_type,
                tags=tags or {},
                unit=unit
            )
            self.metrics.append(entry)
            self._update_aggregated_metrics(entry)
    
    def _update_aggregated_metrics(self, entry: MetricEntry):
        """集約メトリクス更新"""
        key = entry.name
        
        if key not in self.aggregated_metrics:
            self.aggregated_metrics[key] = {
                "count": 0,
                "sum": 0,
                "min": float('inf'),
                "max": float('-inf'),
                "avg": 0,
                "last_value": 0,
                "last_updated": None
            }
        
        agg = self.aggregated_metrics[key]
        agg["count"] += 1
        agg["sum"] += entry.value
        agg["min"] = min(agg["min"], entry.value)
        agg["max"] = max(agg["max"], entry.value)
        agg["avg"] = agg["sum"] / agg["count"]
        agg["last_value"] = entry.value
        agg["last_updated"] = entry.timestamp.isoformat()
    
    def get_metrics_summary(self, metric_name: str = None) -> Dict[str, Any]:
        """メトリクス要約取得"""
        with self._lock:
            if metric_name:
                return self.aggregated_metrics.get(metric_name, {})
            return dict(self.aggregated_metrics)
    
    def get_recent_metrics(self, minutes: int = 10) -> List[MetricEntry]:
        """最近のメトリクス取得"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        with self._lock:
            return [m for m in self.metrics if m.timestamp > cutoff]

class LogRotationManager:
    """ログローテーション管理"""
    
    def __init__(self, log_dir: Path, max_bytes: int = 10*1024*1024, 
                 backup_count: int = 5, compress: bool = True):
        self.log_dir = log_dir
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.compress = compress
        self.log_dir.mkdir(exist_ok=True)
    
    def create_rotating_handler(self, filename: str) -> logging.handlers.RotatingFileHandler:
        """ローテーションハンドラ作成"""
        log_file = self.log_dir / filename
        
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count
        )
        
        # 圧縮処理のためのカスタムローテーション
        if self.compress:
            original_doRollover = handler.doRollover
            
            def compressed_rollover():
                original_doRollover()
                # 最新のバックアップファイルを圧縮
                self._compress_backup_file(log_file)
            
            handler.doRollover = compressed_rollover
        
        return handler
    
    def _compress_backup_file(self, log_file: Path):
        """バックアップファイル圧縮"""
        backup_file = Path(f"{log_file}.1")
        if backup_file.exists():
            compressed_file = Path(f"{backup_file}.gz")
            
            try:
                with open(backup_file, 'rb') as f_in:
                    with gzip.open(compressed_file, 'wb') as f_out:
                        f_out.writelines(f_in)
                
                backup_file.unlink()  # 元ファイル削除
            except Exception as e:
                logging.error(f"ログ圧縮エラー: {e}")

class AlertManager:
    """アラート管理"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.alert_rules: List[Dict[str, Any]] = []
        self.alert_callbacks: List[Callable] = []
        self.alert_history: deque = deque(maxlen=1000)
        self.suppressed_alerts: Dict[str, datetime] = {}
        self.suppression_duration = 300  # 5分
    
    def add_alert_rule(self, name: str, condition: Callable, 
                      severity: str = "warning", message: str = ""):
        """アラートルール追加"""
        rule = {
            "name": name,
            "condition": condition,
            "severity": severity,
            "message": message,
            "enabled": True
        }
        self.alert_rules.append(rule)
    
    def add_alert_callback(self, callback: Callable):
        """アラートコールバック追加"""
        self.alert_callbacks.append(callback)
    
    def check_alerts(self, context: Dict[str, Any]):
        """アラートチェック"""
        for rule in self.alert_rules:
            if not rule["enabled"]:
                continue
            
            try:
                if rule["condition"](context):
                    self._trigger_alert(rule, context)
            except Exception as e:
                self.logger.error(f"アラートルール実行エラー: {rule['name']} - {e}")
    
    def _trigger_alert(self, rule: Dict[str, Any], context: Dict[str, Any]):
        """アラート発火"""
        alert_key = f"{rule['name']}_{rule['severity']}"
        
        # 抑制チェック
        if self._is_suppressed(alert_key):
            return
        
        alert = {
            "name": rule["name"],
            "severity": rule["severity"],
            "message": rule["message"],
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
        
        self.alert_history.append(alert)
        self.suppressed_alerts[alert_key] = datetime.now()
        
        # コールバック実行
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                self.logger.error(f"アラートコールバックエラー: {e}")
    
    def _is_suppressed(self, alert_key: str) -> bool:
        """アラート抑制チェック"""
        if alert_key not in self.suppressed_alerts:
            return False
        
        last_alert = self.suppressed_alerts[alert_key]
        return (datetime.now() - last_alert).total_seconds() < self.suppression_duration

class AdvancedLogger:
    """高度ログシステム"""
    
    def __init__(self, name: str = "screenshot_manager", 
                 log_dir: str = None, log_level: str = "INFO"):
        self.name = name
        self.log_dir = Path(log_dir) if log_dir else Path(__file__).parent.parent.parent / "logs"
        self.log_level = getattr(logging, log_level.upper())
        
        # コンポーネント初期化
        self.rotation_manager = LogRotationManager(self.log_dir)
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        
        # ロガー設定
        self.logger = self._setup_logger()
        
        # 監視タスク
        self._monitoring_task = None
        self._monitoring_active = False
        
        # パフォーマンス追跡
        self._operation_start_times: Dict[str, float] = {}
    
    def _setup_logger(self) -> logging.Logger:
        """ロガー設定"""
        logger = logging.getLogger(self.name)
        logger.setLevel(self.log_level)
        
        # 既存ハンドラクリア
        logger.handlers.clear()
        
        # 構造化ログファイルハンドラ
        structured_handler = self.rotation_manager.create_rotating_handler("structured.log")
        structured_handler.setFormatter(StructuredFormatter())
        structured_handler.setLevel(logging.DEBUG)
        logger.addHandler(structured_handler)
        
        # 人間読み取り可能ログファイルハンドラ
        readable_handler = self.rotation_manager.create_rotating_handler("readable.log")
        readable_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        readable_handler.setFormatter(readable_formatter)
        readable_handler.setLevel(logging.INFO)
        logger.addHandler(readable_handler)
        
        # コンソールハンドラ
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.WARNING)
        logger.addHandler(console_handler)
        
        return logger
    
    def log(self, level: str, message: str, component: str = "", 
            context: Dict[str, Any] = None, tags: List[str] = None,
            duration_ms: float = None):
        """構造化ログ記録"""
        log_level = getattr(logging, level.upper(), logging.INFO)
        
        # 追加情報を設定
        extra = {
            'component': component,
            'context': context or {},
            'tags': tags or [],
            'duration_ms': duration_ms
        }
        
        self.logger.log(log_level, message, extra=extra)
        
        # メトリクス記録
        if duration_ms is not None:
            self.metrics_collector.record_metric(
                f"{component}_duration",
                duration_ms,
                MetricType.TIMER,
                {"component": component},
                "ms"
            )
    
    def info(self, message: str, **kwargs):
        """情報ログ"""
        self.log("INFO", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """警告ログ"""
        self.log("WARNING", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """エラーログ"""
        self.log("ERROR", message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """重要ログ"""
        self.log("CRITICAL", message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """デバッグログ"""
        self.log("DEBUG", message, **kwargs)
    
    def start_operation(self, operation_name: str, context: Dict[str, Any] = None):
        """操作開始記録"""
        self._operation_start_times[operation_name] = time.time()
        self.info(
            f"操作開始: {operation_name}",
            component="operation_tracker",
            context=context or {},
            tags=["operation_start"]
        )
    
    def end_operation(self, operation_name: str, success: bool = True, 
                     context: Dict[str, Any] = None):
        """操作終了記録"""
        start_time = self._operation_start_times.pop(operation_name, None)
        duration_ms = None
        
        if start_time:
            duration_ms = (time.time() - start_time) * 1000
        
        status = "成功" if success else "失敗"
        level = "INFO" if success else "ERROR"
        
        self.log(
            level,
            f"操作{status}: {operation_name}",
            component="operation_tracker",
            context=context or {},
            tags=["operation_end", "success" if success else "failure"],
            duration_ms=duration_ms
        )
    
    def record_metric(self, name: str, value: float, 
                     metric_type: MetricType = MetricType.GAUGE,
                     tags: Dict[str, str] = None, unit: str = ""):
        """メトリクス記録"""
        self.metrics_collector.record_metric(name, value, metric_type, tags, unit)
    
    def set_log_level(self, level: str):
        """ログレベル動的変更"""
        new_level = getattr(logging, level.upper(), logging.INFO)
        self.logger.setLevel(new_level)
        self.log_level = new_level
        self.info(f"ログレベル変更: {level}")
    
    async def start_monitoring(self, interval: float = 60.0):
        """監視開始"""
        if self._monitoring_active:
            return
        
        self._monitoring_active = True
        self._monitoring_task = asyncio.create_task(
            self._monitoring_loop(interval)
        )
        self.info("監視システム開始", component="advanced_logger")
    
    async def stop_monitoring(self):
        """監視停止"""
        if not self._monitoring_active:
            return
        
        self._monitoring_active = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        self.info("監視システム停止", component="advanced_logger")
    
    async def _monitoring_loop(self, interval: float):
        """監視ループ"""
        while self._monitoring_active:
            try:
                # システム状態チェック
                context = self._get_system_context()
                
                # アラートチェック
                self.alert_manager.check_alerts(context)
                
                # 定期メトリクス記録
                self._record_system_metrics()
                
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.error(f"監視ループエラー: {e}", component="advanced_logger")
                await asyncio.sleep(interval)
    
    def _get_system_context(self) -> Dict[str, Any]:
        """システムコンテキスト取得"""
        return {
            "timestamp": datetime.now().isoformat(),
            "log_level": logging.getLevelName(self.log_level),
            "metrics_count": len(self.metrics_collector.metrics),
            "alert_count": len(self.alert_manager.alert_history)
        }
    
    def _record_system_metrics(self):
        """システムメトリクス記録"""
        # ログファイルサイズ
        for log_file in self.log_dir.glob("*.log"):
            if log_file.exists():
                size_mb = log_file.stat().st_size / (1024 * 1024)
                self.record_metric(
                    f"log_file_size",
                    size_mb,
                    MetricType.GAUGE,
                    {"file": log_file.name},
                    "MB"
                )
    
    def get_log_statistics(self) -> Dict[str, Any]:
        """ログ統計取得"""
        return {
            "log_level": logging.getLevelName(self.log_level),
            "log_directory": str(self.log_dir),
            "metrics_summary": self.metrics_collector.get_metrics_summary(),
            "recent_alerts": list(self.alert_manager.alert_history)[-10:],
            "log_files": [
                {
                    "name": f.name,
                    "size_mb": f.stat().st_size / (1024 * 1024),
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                }
                for f in self.log_dir.glob("*.log")
                if f.exists()
            ]
        }
    
    def export_logs(self, output_file: str, start_time: datetime = None, 
                   end_time: datetime = None, level_filter: str = None):
        """ログエクスポート"""
        start_time = start_time or (datetime.now() - timedelta(hours=24))
        end_time = end_time or datetime.now()
        
        exported_logs = []
        structured_log_file = self.log_dir / "structured.log"
        
        if structured_log_file.exists():
            with open(structured_log_file, 'r') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line)
                        log_time = datetime.fromisoformat(log_entry['timestamp'])
                        
                        # 時間フィルター
                        if not (start_time <= log_time <= end_time):
                            continue
                        
                        # レベルフィルター
                        if level_filter and log_entry['level'] != level_filter:
                            continue
                        
                        exported_logs.append(log_entry)
                        
                    except (json.JSONDecodeError, KeyError):
                        continue
        
        # エクスポート
        with open(output_file, 'w') as f:
            json.dump(exported_logs, f, indent=2, ensure_ascii=False)
        
        self.info(f"ログエクスポート完了: {len(exported_logs)}件", 
                 component="advanced_logger")

# グローバルロガー
_global_advanced_logger = None

def get_global_logger() -> AdvancedLogger:
    """グローバル高度ロガー取得"""
    global _global_advanced_logger
    if _global_advanced_logger is None:
        _global_advanced_logger = AdvancedLogger()
    return _global_advanced_logger

# 便利デコレータ
def log_operation(operation_name: str = None, logger: AdvancedLogger = None):
    """操作ログデコレータ"""
    def decorator(func):
        nonlocal operation_name
        if operation_name is None:
            operation_name = func.__name__
        
        if logger is None:
            log = get_global_logger()
        else:
            log = logger
        
        def wrapper(*args, **kwargs):
            log.start_operation(operation_name)
            try:
                result = func(*args, **kwargs)
                log.end_operation(operation_name, True)
                return result
            except Exception as e:
                log.end_operation(operation_name, False, {"error": str(e)})
                raise
        
        async def async_wrapper(*args, **kwargs):
            log.start_operation(operation_name)
            try:
                result = await func(*args, **kwargs)
                log.end_operation(operation_name, True)
                return result
            except Exception as e:
                log.end_operation(operation_name, False, {"error": str(e)})
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper
    
    return decorator

# テスト関数
async def test_advanced_logger():
    """高度ロガーテスト"""
    logger = AdvancedLogger()
    
    # 監視開始
    await logger.start_monitoring(interval=5.0)
    
    # テストログ
    logger.info("テスト開始", component="test", tags=["test"])
    logger.record_metric("test_metric", 42.5, MetricType.GAUGE)
    
    # 操作追跡テスト
    logger.start_operation("test_operation")
    await asyncio.sleep(1)
    logger.end_operation("test_operation", True)
    
    # 統計表示
    stats = logger.get_log_statistics()
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    # 停止
    await logger.stop_monitoring()

if __name__ == "__main__":
    asyncio.run(test_advanced_logger())