import pytest
import asyncio
import time
import statistics
from concurrent.futures import ThreadPoolExecutor
from src.utils.performance_monitor import PerformanceMonitor
from src.utils.error_handler import ErrorHandler
from src.utils.advanced_logger import AdvancedLogger


class TestPerformanceBenchmarks:
    """パフォーマンスベンチマークテストクラス"""
    
    def setup_method(self):
        """テストメソッド前の準備"""
        self.monitor = PerformanceMonitor()
        self.error_handler = ErrorHandler()
        self.logger = AdvancedLogger()
    
    @pytest.mark.slow
    def test_error_handler_performance(self):
        """エラーハンドラーのパフォーマンステスト"""
        iterations = 1000
        start_time = time.time()
        
        for i in range(iterations):
            try:
                raise Exception(f"テストエラー {i}")
            except Exception as e:
                self.error_handler.record_error(e)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 1000回のエラー記録が2秒以内に完了することを確認
        assert duration < 2.0
        
        # 処理性能の計算
        ops_per_second = iterations / duration
        print(f"エラーハンドラー性能: {ops_per_second:.2f} ops/sec")
        
        # 最低性能基準（500 ops/sec以上）
        assert ops_per_second > 500
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_concurrent_screenshot_performance(self):
        """並列スクリーンショット性能のテスト"""
        async def mock_screenshot_task(task_id):
            # 実際のスクリーンショット処理をシミュレート
            await asyncio.sleep(0.1)  # 100ms の処理時間
            return f"screenshot_{task_id}.png"
        
        # 様々な並列度でテスト
        concurrency_levels = [1, 2, 4, 8]
        task_count = 20
        
        results = {}
        
        for concurrency in concurrency_levels:
            tasks = [lambda i=i: mock_screenshot_task(i) for i in range(task_count)]
            
            start_time = time.time()
            screenshots = await self.monitor.optimize_concurrent_screenshots(
                tasks, max_concurrent=concurrency
            )
            end_time = time.time()
            
            duration = end_time - start_time
            results[concurrency] = {
                "duration": duration,
                "throughput": task_count / duration,
                "screenshots_count": len(screenshots)
            }
            
            print(f"並列度 {concurrency}: {duration:.2f}s, "
                  f"{results[concurrency]['throughput']:.2f} tasks/sec")
        
        # 並列度が上がるにつれてスループットが向上することを確認
        assert results[4]["throughput"] > results[1]["throughput"]
        assert all(r["screenshots_count"] == task_count for r in results.values())
    
    @pytest.mark.slow
    def test_logging_performance(self):
        """ログ記録性能のテスト"""
        iterations = 5000
        start_time = time.time()
        
        for i in range(iterations):
            self.logger.info(f"パフォーマンステストログ {i}", 
                           component="performance_test",
                           context={"iteration": i, "test": "performance"})
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 5000回のログ記録が3秒以内に完了することを確認
        assert duration < 3.0
        
        ops_per_second = iterations / duration
        print(f"ログ記録性能: {ops_per_second:.2f} logs/sec")
        
        # 最低性能基準（1500 logs/sec以上）
        assert ops_per_second > 1500
    
    @pytest.mark.slow
    def test_cache_performance(self):
        """キャッシュ性能のテスト"""
        iterations = 10000
        
        # キャッシュ書き込み性能
        start_time = time.time()
        for i in range(iterations):
            self.monitor.cache_set(f"key_{i}", f"value_{i}", ttl=300)
        write_duration = time.time() - start_time
        
        # キャッシュ読み込み性能
        start_time = time.time()
        for i in range(iterations):
            value = self.monitor.cache_get(f"key_{i}")
            assert value == f"value_{i}"
        read_duration = time.time() - start_time
        
        print(f"キャッシュ書き込み性能: {iterations/write_duration:.2f} writes/sec")
        print(f"キャッシュ読み込み性能: {iterations/read_duration:.2f} reads/sec")
        
        # 性能基準
        assert (iterations / write_duration) > 5000  # 5000 writes/sec以上
        assert (iterations / read_duration) > 10000  # 10000 reads/sec以上
    
    @pytest.mark.slow
    def test_memory_usage_under_load(self):
        """負荷時のメモリ使用量テスト"""
        import psutil
        import gc
        
        # 初期メモリ使用量
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 大量のデータ処理
        large_data = []
        for i in range(1000):
            # 大きなオブジェクトを作成
            data = {
                "id": i,
                "content": "x" * 1000,  # 1KB文字列
                "metadata": {"timestamp": time.time(), "index": i}
            }
            large_data.append(data)
            
            # キャッシュにも保存
            self.monitor.cache_set(f"large_key_{i}", data, ttl=60)
            
            # エラーも記録
            if i % 100 == 0:
                try:
                    raise Exception(f"大量データ処理中のエラー {i}")
                except Exception as e:
                    self.error_handler.record_error(e)
        
        # 処理後のメモリ使用量
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # ガベージコレクション実行
        gc.collect()
        
        # クリーンアップ後のメモリ使用量
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        print(f"初期メモリ: {initial_memory:.2f} MB")
        print(f"ピークメモリ: {peak_memory:.2f} MB")
        print(f"最終メモリ: {final_memory:.2f} MB")
        print(f"メモリ増加: {peak_memory - initial_memory:.2f} MB")
        
        # メモリリークのチェック（最終メモリが初期の2倍を超えないこと）
        assert final_memory < initial_memory * 2
        
        # ピーク時のメモリ使用量が合理的な範囲内であること（100MB以下）
        assert (peak_memory - initial_memory) < 100
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_resource_monitoring_overhead(self):
        """リソース監視のオーバーヘッドテスト"""
        # 監視なしでの処理時間測定
        start_time = time.time()
        await self._cpu_intensive_task()
        no_monitoring_duration = time.time() - start_time
        
        # 監視ありでの処理時間測定
        await self.monitor.start_monitoring(interval=0.1)
        start_time = time.time()
        await self._cpu_intensive_task()
        with_monitoring_duration = time.time() - start_time
        await self.monitor.stop_monitoring()
        
        overhead = with_monitoring_duration - no_monitoring_duration
        overhead_percentage = (overhead / no_monitoring_duration) * 100
        
        print(f"監視なし: {no_monitoring_duration:.3f}s")
        print(f"監視あり: {with_monitoring_duration:.3f}s")
        print(f"オーバーヘッド: {overhead:.3f}s ({overhead_percentage:.1f}%)")
        
        # オーバーヘッドが20%以下であることを確認
        assert overhead_percentage < 20
    
    async def _cpu_intensive_task(self):
        """CPU集約的なタスクのシミュレーション"""
        # CPU負荷をかける処理
        total = 0
        for i in range(100000):
            total += i ** 2
            if i % 10000 == 0:
                await asyncio.sleep(0.001)  # 少し非同期処理を入れる
        return total
    
    @pytest.mark.slow
    def test_concurrent_error_handling(self):
        """並行エラーハンドリングの性能テスト"""
        import threading
        
        def error_generating_worker(worker_id, iterations):
            for i in range(iterations):
                try:
                    if i % 2 == 0:
                        raise ConnectionError(f"Worker {worker_id} error {i}")
                    else:
                        raise FileNotFoundError(f"Worker {worker_id} file error {i}")
                except Exception as e:
                    self.error_handler.record_error(e)
        
        # 複数スレッドで同時にエラーを生成
        threads = []
        workers = 4
        iterations_per_worker = 250
        
        start_time = time.time()
        
        for worker_id in range(workers):
            thread = threading.Thread(
                target=error_generating_worker,
                args=(worker_id, iterations_per_worker)
            )
            threads.append(thread)
            thread.start()
        
        # すべてのスレッドの完了を待機
        for thread in threads:
            thread.join()
        
        duration = time.time() - start_time
        total_errors = workers * iterations_per_worker
        
        print(f"並行エラーハンドリング: {total_errors} errors in {duration:.2f}s")
        print(f"エラー処理率: {total_errors / duration:.2f} errors/sec")
        
        # すべてのエラーが記録されていることを確認
        assert self.error_handler.total_errors >= total_errors
        
        # 性能基準（1000 errors/sec以上）
        assert (total_errors / duration) > 1000


class TestStressTests:
    """ストレステストクラス"""
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_sustained_load(self):
        """持続的負荷テスト"""
        monitor = PerformanceMonitor()
        logger = AdvancedLogger()
        
        # 30秒間の持続的負荷
        duration = 10  # テスト時間を10秒に短縮
        end_time = time.time() + duration
        
        await monitor.start_monitoring(interval=0.5)
        
        iteration = 0
        while time.time() < end_time:
            # 様々な操作を実行
            iteration += 1
            
            # ログ記録
            logger.info(f"持続的負荷テスト iteration {iteration}",
                       component="stress_test")
            
            # キャッシュ操作
            monitor.cache_set(f"stress_key_{iteration}", 
                            f"stress_value_{iteration}", ttl=30)
            
            # エラーシミュレーション（10回に1回）
            if iteration % 10 == 0:
                try:
                    raise Exception(f"ストレステストエラー {iteration}")
                except Exception as e:
                    ErrorHandler().record_error(e)
            
            # 短い待機
            await asyncio.sleep(0.01)
        
        await monitor.stop_monitoring()
        
        print(f"持続的負荷テスト完了: {iteration} iterations")
        
        # システムが安定していることを確認
        summary = monitor.get_performance_summary()
        assert summary["status"] == "inactive"  # 正常停止
        assert summary["resource_usage"]["current_cpu"] < 90  # CPU 90%未満
        assert summary["resource_usage"]["current_memory"] < 90  # メモリ 90%未満


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto", "-m", "not slow"])