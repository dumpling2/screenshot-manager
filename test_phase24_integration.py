#!/usr/bin/env python3
"""
Phase 2.4 統合テストスクリプト
エラーハンドリング、パフォーマンス監視、信頼性管理、高度ログシステムの包括的テスト
"""

import asyncio
import json
import sys
import time
import logging
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any

# パス追加
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.error_handler import (
    ErrorHandler, ErrorCategory, ErrorSeverity, 
    handle_errors, get_global_error_handler
)
from src.utils.performance_monitor import (
    PerformanceMonitor, PerformanceThresholds,
    get_global_performance_monitor, monitor_performance
)
from src.utils.reliability_manager import (
    ReliabilityManager, ComponentStatus, 
    get_global_reliability_manager, reliable_operation
)
from src.utils.advanced_logger import (
    AdvancedLogger, MetricType, LogLevel,
    get_global_logger, log_operation
)

class Phase24IntegrationTester:
    """Phase 2.4統合テスト"""
    
    def __init__(self):
        self.logger = AdvancedLogger("phase24_test")
        self.error_handler = ErrorHandler(self.logger.logger)
        self.performance_monitor = PerformanceMonitor(self.logger.logger)
        self.reliability_manager = ReliabilityManager(self.logger.logger)
        self.test_results = []
        
    async def test_error_handling_system(self):
        """エラーハンドリングシステムテスト"""
        print("\n1️⃣ === エラーハンドリングシステム テスト ===")
        
        test_success = True
        
        try:
            # 意図的エラー生成とハンドリング
            @handle_errors(ErrorCategory.NETWORK, ErrorSeverity.HIGH, auto_retry=False)
            def test_network_error():
                raise ConnectionError("テスト用ネットワークエラー")
            
            @handle_errors(ErrorCategory.FILESYSTEM, ErrorSeverity.MEDIUM, auto_retry=True)
            async def test_filesystem_error():
                raise FileNotFoundError("テスト用ファイルシステムエラー")
            
            # エラー発生テスト
            try:
                test_network_error()
            except ConnectionError:
                pass  # 期待されるエラー
            
            try:
                await test_filesystem_error()
            except FileNotFoundError:
                pass  # 期待されるエラー
            
            # 少し待機してからエラー統計確認
            await asyncio.sleep(0.1)
            
            # グローバルエラーハンドラからも統計取得
            global_handler = get_global_error_handler()
            global_stats = global_handler.get_error_statistics()
            
            stats = self.error_handler.get_error_statistics()
            print(f"ローカルエラー統計: {json.dumps(stats, indent=2, ensure_ascii=False)}")
            print(f"グローバルエラー統計: {json.dumps(global_stats, indent=2, ensure_ascii=False)}")
            
            # どちらかでエラーが記録されていれば成功
            total_errors = max(stats['total_errors'], global_stats['total_errors'])
            if total_errors >= 2:
                print("✅ エラーハンドリング正常動作")
            else:
                print("❌ エラーハンドリング異常")
                test_success = False
                
        except Exception as e:
            print(f"❌ エラーハンドリングテストエラー: {e}")
            test_success = False
        
        self.test_results.append(("Error Handling", test_success))
        return test_success
    
    async def test_performance_monitoring_system(self):
        """パフォーマンス監視システムテスト"""
        print("\n2️⃣ === パフォーマンス監視システム テスト ===")
        
        test_success = True
        
        try:
            # 監視開始
            await self.performance_monitor.start_monitoring(interval_seconds=1.0)
            
            # パフォーマンス測定テスト
            @self.performance_monitor.measure_execution_time("test_heavy_operation")
            async def heavy_operation():
                await asyncio.sleep(0.5)  # 重い処理をシミュレート
                return "completed"
            
            @monitor_performance("test_quick_operation")
            def quick_operation():
                time.sleep(0.1)  # 軽い処理をシミュレート
                return "done"
            
            # 複数回実行
            await heavy_operation()
            quick_operation()
            await heavy_operation()
            
            # 並列スクリーンショットテスト
            async def mock_screenshot_task():
                await asyncio.sleep(0.2)
                return f"screenshot_{time.time()}"
            
            screenshot_tasks = [
                lambda: mock_screenshot_task() for _ in range(5)
            ]
            
            results = await self.performance_monitor.optimize_concurrent_screenshots(
                screenshot_tasks, max_concurrent=3
            )
            
            # パフォーマンス要約確認
            summary = self.performance_monitor.get_performance_summary()
            print(f"パフォーマンス要約: {json.dumps(summary, indent=2, ensure_ascii=False)}")
            
            # 結果評価
            if (summary['status'] == 'active' and 
                len(results) == 5 and
                'test_heavy_operation' in summary.get('execution_times', {})):
                print("✅ パフォーマンス監視正常動作")
            else:
                print("❌ パフォーマンス監視異常")
                test_success = False
            
            await self.performance_monitor.stop_monitoring()
            
        except Exception as e:
            print(f"❌ パフォーマンス監視テストエラー: {e}")
            test_success = False
        
        self.test_results.append(("Performance Monitoring", test_success))
        return test_success
    
    async def test_reliability_management_system(self):
        """信頼性管理システムテスト"""
        print("\n3️⃣ === 信頼性管理システム テスト ===")
        
        test_success = True
        
        try:
            # テスト用コンポーネント登録
            async def healthy_component_check():
                return True
            
            async def failing_component_check():
                return False
            
            async def recovery_strategy(health):
                self.logger.info(f"復旧実行: {health.name}")
                return True
            
            # コンポーネント登録
            self.reliability_manager.register_component(
                "test_healthy_component",
                healthy_component_check,
                recovery_strategy,
                check_interval=2.0
            )
            
            self.reliability_manager.register_component(
                "test_failing_component", 
                failing_component_check,
                recovery_strategy,
                check_interval=2.0
            )
            
            # 信頼性管理開始
            await self.reliability_manager.start()
            
            # 少し待機してヘルスチェック実行
            await asyncio.sleep(5)
            
            # システム健全性確認
            health = self.reliability_manager.get_system_health()
            print(f"システム健全性: {json.dumps(health, indent=2, ensure_ascii=False)}")
            
            # 結果評価
            if (health['running'] and 
                len(health['components']) == 2 and
                'test_healthy_component' in health['components']):
                print("✅ 信頼性管理正常動作")
            else:
                print("❌ 信頼性管理異常")
                test_success = False
            
            await self.reliability_manager.stop()
            
        except Exception as e:
            print(f"❌ 信頼性管理テストエラー: {e}")
            test_success = False
        
        self.test_results.append(("Reliability Management", test_success))
        return test_success
    
    async def test_advanced_logging_system(self):
        """高度ログシステムテスト"""
        print("\n4️⃣ === 高度ログシステム テスト ===")
        
        test_success = True
        
        try:
            # 監視開始
            await self.logger.start_monitoring(interval=2.0)
            
            # 各種ログテスト
            self.logger.info("情報ログテスト", component="test", tags=["info"])
            self.logger.warning("警告ログテスト", component="test", tags=["warning"])
            self.logger.error("エラーログテスト", component="test", tags=["error"])
            
            # 操作追跡テスト
            @log_operation("test_logged_operation", self.logger)
            async def logged_operation():
                await asyncio.sleep(0.3)
                return "操作完了"
            
            result = await logged_operation()
            
            # メトリクス記録テスト
            self.logger.record_metric("test_counter", 10, MetricType.COUNTER)
            self.logger.record_metric("test_gauge", 42.5, MetricType.GAUGE, {"tag": "test"})
            
            # コンテキスト付きログ
            context = {
                "user_id": "test_user",
                "operation": "integration_test",
                "timestamp": datetime.now().isoformat()
            }
            self.logger.info("コンテキスト付きログ", component="test", context=context)
            
            # 統計確認
            stats = self.logger.get_log_statistics()
            print(f"ログ統計: {json.dumps(stats, indent=2, ensure_ascii=False)}")
            
            # 結果評価
            if (stats['log_level'] and 
                len(stats['log_files']) > 0 and
                stats['metrics_summary']):
                print("✅ 高度ログシステム正常動作")
            else:
                print("❌ 高度ログシステム異常")
                test_success = False
            
            await self.logger.stop_monitoring()
            
        except Exception as e:
            print(f"❌ 高度ログシステムテストエラー: {e}")
            test_success = False
        
        self.test_results.append(("Advanced Logging", test_success))
        return test_success
    
    async def test_integrated_scenarios(self):
        """統合シナリオテスト"""
        print("\n5️⃣ === 統合シナリオ テスト ===")
        
        test_success = True
        
        try:
            # シナリオ1: 負荷時のエラーハンドリングとパフォーマンス監視
            self.logger.info("統合シナリオ1開始: 負荷テスト", component="integration_test")
            
            await self.performance_monitor.start_monitoring(interval_seconds=1.0)
            
            @handle_errors(ErrorCategory.SCREENSHOT, ErrorSeverity.MEDIUM)
            @monitor_performance("integrated_heavy_task")
            async def integrated_heavy_task(task_id: int):
                if task_id % 3 == 0:  # 33%の確率でエラー
                    raise RuntimeError(f"タスク{task_id}でエラー発生")
                
                await asyncio.sleep(0.2)
                return f"タスク{task_id}完了"
            
            # 複数タスク並列実行
            tasks = [integrated_heavy_task(i) for i in range(10)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 結果分析
            successful = len([r for r in results if not isinstance(r, Exception)])
            failed = len(results) - successful
            
            self.logger.info(
                f"統合テスト結果: {successful}成功, {failed}失敗",
                component="integration_test",
                context={"success_rate": successful / len(results)}
            )
            
            # シナリオ2: 信頼性のある操作
            async with reliable_operation("integration_scenario_2"):
                self.logger.start_operation("reliable_operation_test")
                await asyncio.sleep(0.5)
                self.logger.end_operation("reliable_operation_test", True)
            
            await self.performance_monitor.stop_monitoring()
            
            # 統合結果評価
            if successful >= 6:  # 60%以上成功
                print("✅ 統合シナリオ正常動作")
            else:
                print("❌ 統合シナリオ異常")
                test_success = False
            
        except Exception as e:
            print(f"❌ 統合シナリオテストエラー: {e}")
            test_success = False
        
        self.test_results.append(("Integrated Scenarios", test_success))
        return test_success
    
    async def test_system_recovery_simulation(self):
        """システム復旧シミュレーションテスト"""
        print("\n6️⃣ === システム復旧シミュレーション テスト ===")
        
        test_success = True
        
        try:
            # 障害シミュレーション
            failure_count = 0
            
            async def simulated_failing_service():
                nonlocal failure_count
                failure_count += 1
                if failure_count <= 2:  # 最初の2回は失敗
                    raise ConnectionError("サービス接続失敗")
                return True  # 3回目で成功
            
            async def recovery_strategy(health):
                self.logger.info("復旧戦略実行中...", component="recovery_test")
                await asyncio.sleep(0.1)
                return True
            
            # 失敗するコンポーネント登録
            self.reliability_manager.register_component(
                "simulated_failing_service",
                simulated_failing_service,
                recovery_strategy,
                check_interval=1.0
            )
            
            await self.reliability_manager.start()
            
            # 復旧プロセス監視
            for i in range(5):
                await asyncio.sleep(1)
                health = self.reliability_manager.get_system_health()
                
                service_health = health['components'].get('simulated_failing_service', {})
                status = service_health.get('status', 'unknown')
                
                self.logger.info(
                    f"復旧監視 {i+1}/5: {status}",
                    component="recovery_test",
                    context={"iteration": i+1, "status": status}
                )
                
                if status == ComponentStatus.HEALTHY.value:
                    print("✅ システム復旧成功")
                    break
            else:
                print("❌ システム復旧タイムアウト")
                test_success = False
            
            await self.reliability_manager.stop()
            
        except Exception as e:
            print(f"❌ システム復旧シミュレーションエラー: {e}")
            test_success = False
        
        self.test_results.append(("System Recovery", test_success))
        return test_success
    
    async def run_comprehensive_test(self):
        """包括的テスト実行"""
        print("🔥 === Phase 2.4 包括的統合テスト ===")
        print(f"📅 テスト開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # 個別システムテスト
        await self.test_error_handling_system()
        await self.test_performance_monitoring_system()
        await self.test_reliability_management_system()
        await self.test_advanced_logging_system()
        
        # 統合テスト
        await self.test_integrated_scenarios()
        await self.test_system_recovery_simulation()
        
        # 結果集計
        print("\n📊 === Phase 2.4 テスト結果 ===")
        total_tests = len(self.test_results)
        passed_tests = sum(1 for _, success in self.test_results if success)
        
        print(f"実行テスト数: {total_tests}")
        print(f"成功テスト数: {passed_tests}")
        print(f"成功率: {(passed_tests / total_tests) * 100:.1f}%")
        
        print("\n詳細結果:")
        for test_name, success in self.test_results:
            status = "✅ 成功" if success else "❌ 失敗"
            print(f"  {test_name}: {status}")
        
        if passed_tests == total_tests:
            print("\n🎉 すべてのPhase 2.4テストが成功しました！")
            print("✅ エラーハンドリング・パフォーマンス最適化システムは正常に動作しています")
            print("🚀 プロダクション品質への準備が完了しました")
            return True
        else:
            failed_tests = total_tests - passed_tests
            print(f"\n❌ {failed_tests}個のテストが失敗しました")
            print("🔧 改善が必要です")
            return False
    
    async def export_test_report(self, output_file: str):
        """テストレポートエクスポート"""
        report = {
            "test_summary": {
                "timestamp": datetime.now().isoformat(),
                "total_tests": len(self.test_results),
                "passed_tests": sum(1 for _, success in self.test_results if success),
                "success_rate": (sum(1 for _, success in self.test_results if success) / len(self.test_results)) * 100
            },
            "test_results": [
                {"name": name, "success": success}
                for name, success in self.test_results
            ],
            "system_statistics": {
                "error_stats": self.error_handler.get_error_statistics(),
                "performance_summary": self.performance_monitor.get_performance_summary(),
                "log_stats": self.logger.get_log_statistics()
            }
        }
        
        Path(output_file).write_text(json.dumps(report, indent=2, ensure_ascii=False))
        print(f"📄 テストレポートエクスポート: {output_file}")

async def main():
    """メイン実行関数"""
    tester = Phase24IntegrationTester()
    
    print("🚀 Screenshot Manager Phase 2.4: 包括的統合テスト開始")
    print("=" * 60)
    
    success = await tester.run_comprehensive_test()
    
    # テストレポートエクスポート
    report_file = f"phase24_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    await tester.export_test_report(report_file)
    
    print("\n" + "=" * 60)
    if success:
        print("🌟 Phase 2.4 統合テスト完了 - すべてのシステムが正常動作")
        print("🎯 Screenshot Manager はプロダクション品質に到達しました")
    else:
        print("⚠️ Phase 2.4 統合テスト完了 - 一部システムに問題あり")

if __name__ == "__main__":
    asyncio.run(main())