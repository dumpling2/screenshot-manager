import pytest
import asyncio
import time
from unittest.mock import Mock, patch
from src.utils.performance_monitor import PerformanceMonitor, ResourceUsage


class TestPerformanceMonitor:
    """パフォーマンス監視のテストクラス"""
    
    def setup_method(self):
        """テストメソッド前の準備"""
        self.monitor = PerformanceMonitor()
    
    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self):
        """監視開始・停止のテスト"""
        # 監視開始
        await self.monitor.start_monitoring(interval=0.1)
        assert self.monitor.monitoring_active is True
        
        # 少し待機
        await asyncio.sleep(0.2)
        
        # 監視停止
        await self.monitor.stop_monitoring()
        assert self.monitor.monitoring_active is False
    
    def test_get_resource_usage(self):
        """リソース使用量取得のテスト"""
        usage = self.monitor._get_resource_usage()
        
        assert isinstance(usage, ResourceUsage)
        assert 0 <= usage.cpu_percent <= 100
        assert 0 <= usage.memory_percent <= 100
        assert usage.available_memory > 0
        assert usage.disk_usage_percent >= 0
    
    @pytest.mark.asyncio
    async def test_optimize_concurrent_screenshots(self):
        """並列スクリーンショット最適化のテスト"""
        async def mock_screenshot_task(task_id):
            await asyncio.sleep(0.1)
            return f"スクリーンショット{task_id}完了"
        
        tasks = [
            lambda: mock_screenshot_task(i) for i in range(5)
        ]
        
        results = await self.monitor.optimize_concurrent_screenshots(tasks, max_concurrent=3)
        
        assert len(results) == 5
        for i, result in enumerate(results):
            assert result == f"スクリーンショット{i}完了"
    
    def test_record_execution_time(self):
        """実行時間記録のテスト"""
        operation_name = "test_operation"
        
        # 実行時間記録
        start_time = time.time()
        time.sleep(0.1)  # 0.1秒待機
        self.monitor.record_execution_time(operation_name, start_time)
        
        # 記録確認
        summary = self.monitor.get_performance_summary()
        assert operation_name in summary['execution_times']
        
        exec_time_info = summary['execution_times'][operation_name]
        assert exec_time_info['call_count'] == 1
        assert 0.08 <= exec_time_info['avg_time'] <= 0.15  # 0.1秒前後
    
    def test_cache_operations(self):
        """キャッシュ操作のテスト"""
        key = "test_key"
        value = {"data": "test_data"}
        
        # キャッシュに保存
        self.monitor.cache_set(key, value, ttl=60)
        
        # キャッシュから取得
        cached_value = self.monitor.cache_get(key)
        assert cached_value == value
        
        # 存在しないキーの取得
        assert self.monitor.cache_get("nonexistent_key") is None
        
        # キャッシュ削除
        self.monitor.cache_delete(key)
        assert self.monitor.cache_get(key) is None
    
    def test_cache_expiration(self):
        """キャッシュ有効期限のテスト"""
        key = "expiring_key"
        value = "expiring_value"
        
        # 短いTTLでキャッシュに保存
        self.monitor.cache_set(key, value, ttl=0.1)
        
        # すぐに取得（存在する）
        assert self.monitor.cache_get(key) == value
        
        # TTL経過後（存在しない）
        time.sleep(0.2)
        assert self.monitor.cache_get(key) is None
    
    def test_get_performance_summary(self):
        """パフォーマンス要約取得のテスト"""
        summary = self.monitor.get_performance_summary()
        
        required_keys = [
            'status', 'resource_usage', 'execution_times',
            'cache_stats', 'task_queue_stats', 'metrics_count', 'thresholds'
        ]
        
        for key in required_keys:
            assert key in summary
        
        # リソース使用量の確認
        resource_usage = summary['resource_usage']
        assert 'avg_cpu_percent' in resource_usage
        assert 'avg_memory_percent' in resource_usage
        assert 'current_cpu' in resource_usage
        assert 'current_memory' in resource_usage
        
        # キャッシュ統計の確認
        cache_stats = summary['cache_stats']
        assert 'size' in cache_stats
        assert 'max_size' in cache_stats
        assert 'hit_rate' in cache_stats
    
    @pytest.mark.asyncio
    async def test_resource_threshold_monitoring(self):
        """リソース閾値監視のテスト"""
        # 閾値を低く設定
        self.monitor.cpu_threshold = 1.0  # 1%に設定
        self.monitor.memory_threshold = 1.0  # 1%に設定
        
        # 監視開始
        await self.monitor.start_monitoring(interval=0.1)
        await asyncio.sleep(0.2)
        
        # 監視停止
        await self.monitor.stop_monitoring()
        
        # 閾値を超えたかどうかの確認（通常は超える）
        summary = self.monitor.get_performance_summary()
        resource_usage = summary['resource_usage']
        
        # CPUまたはメモリ使用率が閾値を超えていることを想定
        assert (resource_usage['current_cpu'] > 1.0 or 
                resource_usage['current_memory'] > 1.0)


class TestResourceUsage:
    """ResourceUsageデータクラスのテスト"""
    
    def test_resource_usage_creation(self):
        """ResourceUsage作成のテスト"""
        usage = ResourceUsage(
            cpu_percent=50.5,
            memory_percent=75.2,
            available_memory=1024 * 1024 * 1024,  # 1GB
            disk_usage_percent=80.0
        )
        
        assert usage.cpu_percent == 50.5
        assert usage.memory_percent == 75.2
        assert usage.available_memory == 1024 * 1024 * 1024
        assert usage.disk_usage_percent == 80.0
    
    def test_resource_usage_validation(self):
        """ResourceUsage値検証のテスト"""
        # 正常値
        usage = ResourceUsage(0.0, 0.0, 100, 0.0)
        assert usage.cpu_percent == 0.0
        
        # 境界値
        usage = ResourceUsage(100.0, 100.0, 0, 100.0)
        assert usage.cpu_percent == 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])