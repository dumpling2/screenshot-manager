#!/usr/bin/env python3
"""
パフォーマンス監視・最適化システム - Phase 2.4
システムリソース監視、処理最適化、負荷制御を提供
"""

import asyncio
import time
import psutil
import threading
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque, defaultdict
import json
import functools
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import weakref

@dataclass
class PerformanceMetric:
    """パフォーマンス指標"""
    name: str
    value: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.now)
    category: str = "general"
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ResourceUsage:
    """リソース使用量"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    disk_free_gb: float
    network_bytes_sent: int = 0
    network_bytes_recv: int = 0
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class PerformanceThresholds:
    """パフォーマンス閾値"""
    max_cpu_percent: float = 80.0
    max_memory_percent: float = 85.0
    max_disk_percent: float = 90.0
    max_execution_time: float = 30.0
    max_concurrent_tasks: int = 5

class PerformanceCache:
    """パフォーマンス向上のためのキャッシュシステム"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Any] = {}
        self._timestamps: Dict[str, datetime] = {}
        self._access_counts: Dict[str, int] = defaultdict(int)
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """キャッシュ取得"""
        with self._lock:
            if key not in self._cache:
                return None
            
            # TTL チェック
            if datetime.now() - self._timestamps[key] > timedelta(seconds=self.ttl_seconds):
                self._remove(key)
                return None
            
            self._access_counts[key] += 1
            return self._cache[key]
    
    def set(self, key: str, value: Any) -> None:
        """キャッシュ設定"""
        with self._lock:
            # サイズ制限チェック
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_least_used()
            
            self._cache[key] = value
            self._timestamps[key] = datetime.now()
            self._access_counts[key] = 1
    
    def _remove(self, key: str) -> None:
        """キャッシュ削除"""
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)
        self._access_counts.pop(key, None)
    
    def _evict_least_used(self) -> None:
        """最少使用アイテムを削除"""
        if not self._cache:
            return
        
        least_used_key = min(self._access_counts.items(), key=lambda x: x[1])[0]
        self._remove(least_used_key)
    
    def clear_expired(self) -> int:
        """期限切れアイテムをクリア"""
        with self._lock:
            expired_keys = [
                key for key, timestamp in self._timestamps.items()
                if datetime.now() - timestamp > timedelta(seconds=self.ttl_seconds)
            ]
            
            for key in expired_keys:
                self._remove(key)
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """キャッシュ統計"""
        with self._lock:
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hit_rate": sum(self._access_counts.values()) / max(len(self._cache), 1),
                "expired_items": self.clear_expired()
            }

class TaskQueue:
    """負荷制御のためのタスクキュー"""
    
    def __init__(self, max_concurrent: int = 5, max_queue_size: int = 100):
        self.max_concurrent = max_concurrent
        self.max_queue_size = max_queue_size
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.queue = asyncio.Queue(maxsize=max_queue_size)
        self.active_tasks = set()
        self.completed_tasks = 0
        self.failed_tasks = 0
        self._running = False
    
    async def start(self):
        """キュー処理開始"""
        self._running = True
        asyncio.create_task(self._process_queue())
    
    async def stop(self):
        """キュー処理停止"""
        self._running = False
        await self.queue.put(None)  # 終了シグナル
    
    async def submit(self, coro_func: Callable, *args, **kwargs) -> Any:
        """タスク投入"""
        if self.queue.qsize() >= self.max_queue_size:
            raise asyncio.QueueFull("Task queue is full")
        
        future = asyncio.Future()
        await self.queue.put((coro_func, args, kwargs, future))
        return await future
    
    async def _process_queue(self):
        """キュー処理"""
        while self._running:
            try:
                item = await self.queue.get()
                if item is None:  # 終了シグナル
                    break
                
                coro_func, args, kwargs, future = item
                asyncio.create_task(self._execute_task(coro_func, args, kwargs, future))
                
            except Exception as e:
                logging.error(f"Queue processing error: {e}")
    
    async def _execute_task(self, coro_func: Callable, args: tuple, kwargs: dict, future: asyncio.Future):
        """タスク実行"""
        async with self.semaphore:
            task_id = id(future)
            self.active_tasks.add(task_id)
            
            try:
                result = await coro_func(*args, **kwargs)
                future.set_result(result)
                self.completed_tasks += 1
                
            except Exception as e:
                future.set_exception(e)
                self.failed_tasks += 1
                
            finally:
                self.active_tasks.discard(task_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """キュー統計"""
        return {
            "queue_size": self.queue.qsize(),
            "active_tasks": len(self.active_tasks),
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "max_concurrent": self.max_concurrent
        }

class PerformanceMonitor:
    """パフォーマンス監視メインクラス"""
    
    def __init__(self, 
                 logger: Optional[logging.Logger] = None,
                 thresholds: Optional[PerformanceThresholds] = None):
        self.logger = logger or self._setup_default_logger()
        self.thresholds = thresholds or PerformanceThresholds()
        self.metrics_history: deque = deque(maxlen=1000)
        self.resource_history: deque = deque(maxlen=100)
        self.execution_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=50))
        self.cache = PerformanceCache()
        self.task_queue = TaskQueue(max_concurrent=self.thresholds.max_concurrent_tasks)
        self.monitoring_active = False
        self.alert_callbacks: List[Callable] = []
        self._monitor_task = None
        
    def _setup_default_logger(self) -> logging.Logger:
        """デフォルトロガー設定"""
        logger = logging.getLogger('performance_monitor')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # ファイルハンドラ
            log_dir = Path(__file__).parent.parent.parent / "logs"
            log_dir.mkdir(exist_ok=True)
            
            fh = logging.FileHandler(log_dir / 'performance.log')
            fh.setLevel(logging.INFO)
            
            # フォーマット
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        
        return logger
    
    async def start_monitoring(self, interval_seconds: float = 5.0):
        """監視開始"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        await self.task_queue.start()
        
        self._monitor_task = asyncio.create_task(
            self._monitoring_loop(interval_seconds)
        )
        
        self.logger.info("🚀 パフォーマンス監視開始")
    
    async def stop_monitoring(self):
        """監視停止"""
        if not self.monitoring_active:
            return
        
        self.monitoring_active = False
        
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        await self.task_queue.stop()
        self.logger.info("🛑 パフォーマンス監視停止")
    
    async def _monitoring_loop(self, interval: float):
        """監視ループ"""
        while self.monitoring_active:
            try:
                # リソース使用量取得
                resource_usage = self._get_resource_usage()
                self.resource_history.append(resource_usage)
                
                # 閾値チェック
                self._check_thresholds(resource_usage)
                
                # キャッシュクリーンアップ
                self.cache.clear_expired()
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(interval)
    
    def _get_resource_usage(self) -> ResourceUsage:
        """リソース使用量取得"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        try:
            network = psutil.net_io_counters()
            network_sent = network.bytes_sent
            network_recv = network.bytes_recv
        except:
            network_sent = network_recv = 0
        
        return ResourceUsage(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_mb=memory.used / (1024 * 1024),
            disk_usage_percent=disk.percent,
            disk_free_gb=disk.free / (1024 * 1024 * 1024),
            network_bytes_sent=network_sent,
            network_bytes_recv=network_recv
        )
    
    def _check_thresholds(self, resource_usage: ResourceUsage):
        """閾値チェック"""
        alerts = []
        
        if resource_usage.cpu_percent > self.thresholds.max_cpu_percent:
            alerts.append(f"高CPU使用率: {resource_usage.cpu_percent:.1f}%")
        
        if resource_usage.memory_percent > self.thresholds.max_memory_percent:
            alerts.append(f"高メモリ使用率: {resource_usage.memory_percent:.1f}%")
        
        if resource_usage.disk_usage_percent > self.thresholds.max_disk_percent:
            alerts.append(f"ディスク容量不足: {resource_usage.disk_usage_percent:.1f}%")
        
        for alert in alerts:
            self.logger.warning(f"⚠️ {alert}")
            self._trigger_alert(alert, resource_usage)
    
    def _trigger_alert(self, message: str, resource_usage: ResourceUsage):
        """アラート発火"""
        for callback in self.alert_callbacks:
            try:
                callback(message, resource_usage)
            except Exception as e:
                self.logger.error(f"Alert callback error: {e}")
    
    def measure_execution_time(self, func_name: str = None):
        """実行時間測定デコレータ"""
        def decorator(func):
            name = func_name or func.__name__
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    execution_time = time.time() - start_time
                    self._record_execution_time(name, execution_time)
            
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    execution_time = time.time() - start_time
                    self._record_execution_time(name, execution_time)
            
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return wrapper
        
        return decorator
    
    def _record_execution_time(self, func_name: str, execution_time: float):
        """実行時間記録"""
        self.execution_times[func_name].append(execution_time)
        
        # 長時間実行の警告
        if execution_time > self.thresholds.max_execution_time:
            self.logger.warning(
                f"⚠️ 長時間実行: {func_name} ({execution_time:.2f}s)"
            )
        
        # メトリクス記録
        metric = PerformanceMetric(
            name=f"{func_name}_execution_time",
            value=execution_time,
            unit="seconds",
            category="execution_time"
        )
        self.metrics_history.append(metric)
    
    async def optimize_concurrent_screenshots(self, 
                                             screenshot_tasks: List[Callable],
                                             max_concurrent: int = None) -> List[Any]:
        """並列スクリーンショット最適化"""
        max_concurrent = max_concurrent or self.thresholds.max_concurrent_tasks
        
        # リソース使用量に基づく動的調整
        current_usage = self._get_resource_usage()
        if current_usage.cpu_percent > 70:
            max_concurrent = max(1, max_concurrent // 2)
        elif current_usage.memory_percent > 80:
            max_concurrent = max(1, max_concurrent // 3)
        
        self.logger.info(f"📸 並列スクリーンショット実行: {len(screenshot_tasks)}タスク, 並列度: {max_concurrent}")
        
        # セマフォで並列度制御
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def controlled_task(task):
            async with semaphore:
                return await task()
        
        # 並列実行
        start_time = time.time()
        results = await asyncio.gather(
            *[controlled_task(task) for task in screenshot_tasks],
            return_exceptions=True
        )
        execution_time = time.time() - start_time
        
        # 結果分析
        successful = len([r for r in results if not isinstance(r, Exception)])
        failed = len(results) - successful
        
        self.logger.info(
            f"✅ 並列スクリーンショット完了: {successful}成功, {failed}失敗, "
            f"実行時間: {execution_time:.2f}s"
        )
        
        return results
    
    def add_alert_callback(self, callback: Callable):
        """アラートコールバック追加"""
        self.alert_callbacks.append(callback)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """パフォーマンス要約取得"""
        if not self.resource_history:
            return {"status": "no_data"}
        
        recent_resources = list(self.resource_history)[-10:]
        avg_cpu = sum(r.cpu_percent for r in recent_resources) / len(recent_resources)
        avg_memory = sum(r.memory_percent for r in recent_resources) / len(recent_resources)
        
        execution_stats = {}
        for func_name, times in self.execution_times.items():
            if times:
                execution_stats[func_name] = {
                    "avg_time": sum(times) / len(times),
                    "max_time": max(times),
                    "min_time": min(times),
                    "call_count": len(times)
                }
        
        return {
            "status": "active" if self.monitoring_active else "inactive",
            "resource_usage": {
                "avg_cpu_percent": avg_cpu,
                "avg_memory_percent": avg_memory,
                "current_cpu": recent_resources[-1].cpu_percent,
                "current_memory": recent_resources[-1].memory_percent,
            },
            "execution_times": execution_stats,
            "cache_stats": self.cache.get_stats(),
            "task_queue_stats": self.task_queue.get_stats(),
            "metrics_count": len(self.metrics_history),
            "thresholds": {
                "max_cpu": self.thresholds.max_cpu_percent,
                "max_memory": self.thresholds.max_memory_percent,
                "max_execution_time": self.thresholds.max_execution_time
            }
        }
    
    def export_metrics(self, file_path: str):
        """メトリクスエクスポート"""
        data = {
            "performance_summary": self.get_performance_summary(),
            "resource_history": [
                {
                    "timestamp": r.timestamp.isoformat(),
                    "cpu_percent": r.cpu_percent,
                    "memory_percent": r.memory_percent,
                    "disk_percent": r.disk_usage_percent
                }
                for r in self.resource_history
            ],
            "metrics_history": [
                {
                    "name": m.name,
                    "value": m.value,
                    "unit": m.unit,
                    "timestamp": m.timestamp.isoformat(),
                    "category": m.category
                }
                for m in self.metrics_history
            ]
        }
        
        Path(file_path).write_text(json.dumps(data, indent=2, ensure_ascii=False))
        self.logger.info(f"📊 メトリクスエクスポート完了: {file_path}")

# グローバルパフォーマンスモニター
_global_performance_monitor = None

def get_global_performance_monitor() -> PerformanceMonitor:
    """グローバルパフォーマンスモニター取得"""
    global _global_performance_monitor
    if _global_performance_monitor is None:
        _global_performance_monitor = PerformanceMonitor()
    return _global_performance_monitor

# 便利デコレータ
def monitor_performance(func_name: str = None):
    """パフォーマンス監視デコレータ"""
    monitor = get_global_performance_monitor()
    return monitor.measure_execution_time(func_name)

# テスト関数
async def test_performance_monitor():
    """パフォーマンスモニターテスト"""
    monitor = PerformanceMonitor()
    
    await monitor.start_monitoring(interval_seconds=1)
    
    # テスト用重い処理
    @monitor.measure_execution_time("test_heavy_task")
    async def heavy_task():
        await asyncio.sleep(2)
        return "completed"
    
    # 並列テスト
    tasks = [heavy_task for _ in range(3)]
    results = await monitor.optimize_concurrent_screenshots(tasks, max_concurrent=2)
    
    # 統計表示
    summary = monitor.get_performance_summary()
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    
    await monitor.stop_monitoring()

if __name__ == "__main__":
    asyncio.run(test_performance_monitor())