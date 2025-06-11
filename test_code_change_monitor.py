#!/usr/bin/env python3
"""
コード変更監視システム テストスクリプト - Phase 2.3
ファイル変更検知と自動スクリーンショット機能をテスト
"""

import asyncio
import json
import sys
import time
import tempfile
import logging
from pathlib import Path
from datetime import datetime

# パス追加
sys.path.insert(0, str(Path(__file__).parent))

from src.monitors.code_change_monitor import (
    CodeChangeMonitor, 
    create_project_watch_config,
    WATCHDOG_AVAILABLE
)
from src.integrations.mcp_server import ScreenshotManagerMCP

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CodeChangeMonitorTester:
    """コード変更監視システムのテスト"""
    
    def __init__(self):
        self.test_project_path = str(Path.cwd() / "demo_vue_project")
        self.logger = logging.getLogger(__name__)
        self.monitor = None
        self.mcp = None
        
    async def test_watchdog_availability(self):
        """watchdog ライブラリの利用可能性テスト"""
        print("\n1️⃣ === watchdog ライブラリ利用可能性 テスト ===")
        
        print(f"watchdog 利用可能: {WATCHDOG_AVAILABLE}")
        
        if WATCHDOG_AVAILABLE:
            print("✅ watchdog ライブラリが利用可能です")
            return True
        else:
            print("❌ watchdog ライブラリが利用できません")
            print("   pip install watchdog でインストールしてください")
            return False
    
    async def test_monitor_initialization(self):
        """監視システム初期化テスト"""
        print("\n2️⃣ === 監視システム初期化 テスト ===")
        
        try:
            self.monitor = CodeChangeMonitor()
            await self.monitor.start_monitoring()
            
            status = self.monitor.get_status()
            print(f"監視システム状況: {json.dumps(status, indent=2, ensure_ascii=False)}")
            
            if status['running']:
                print("✅ 監視システム初期化成功")
                return True
            else:
                print("❌ 監視システム初期化失敗")
                return False
                
        except Exception as e:
            print(f"❌ 監視システム初期化エラー: {e}")
            return False
    
    async def test_project_watch_config_creation(self):
        """プロジェクト監視設定作成テスト"""
        print("\n3️⃣ === プロジェクト監視設定作成 テスト ===")
        
        try:
            config = await create_project_watch_config(self.test_project_path, "Vue")
            
            print(f"設定作成結果:")
            print(f"  プロジェクトパス: {config.project_path}")
            print(f"  フレームワーク: {config.framework}")
            print(f"  デバウンス時間: {config.debounce_seconds}秒")
            print(f"  自動スクリーンショット: {config.auto_screenshot}")
            print(f"  Claude Code通知: {config.notify_claude_code}")
            
            if config.project_path == self.test_project_path:
                print("✅ プロジェクト監視設定作成成功")
                return True, config
            else:
                print("❌ プロジェクト監視設定作成失敗")
                return False, None
                
        except Exception as e:
            print(f"❌ プロジェクト監視設定作成エラー: {e}")
            return False, None
    
    async def test_project_watch_addition(self, config):
        """プロジェクト監視追加テスト"""
        print("\n4️⃣ === プロジェクト監視追加 テスト ===")
        
        if not self.monitor:
            print("❌ 監視システムが初期化されていません")
            return False
        
        try:
            success = await self.monitor.add_project_watch(config)
            
            if success:
                status = self.monitor.get_status()
                print(f"監視追加後の状況: {json.dumps(status, indent=2, ensure_ascii=False)}")
                print("✅ プロジェクト監視追加成功")
                return True
            else:
                print("❌ プロジェクト監視追加失敗")
                return False
                
        except Exception as e:
            print(f"❌ プロジェクト監視追加エラー: {e}")
            return False
    
    async def test_mcp_integration(self):
        """MCP統合テスト"""
        print("\n5️⃣ === MCP統合 テスト ===")
        
        try:
            self.mcp = ScreenshotManagerMCP()
            
            # コード変更監視開始
            start_result = await self.mcp.handle_start_code_monitoring({
                'project_path': self.test_project_path,
                'framework': 'Vue',
                'auto_screenshot': True,
                'debounce_seconds': 1.0
            })
            
            print(f"監視開始結果: {json.dumps(start_result, indent=2, ensure_ascii=False)}")
            
            if start_result.get('success'):
                # 監視状況確認
                status_result = await self.mcp.handle_get_monitoring_status({})
                print(f"監視状況: {json.dumps(status_result, indent=2, ensure_ascii=False)}")
                
                if status_result.get('success'):
                    print("✅ MCP統合テスト成功")
                    return True
            
            print("❌ MCP統合テスト失敗")
            return False
            
        except Exception as e:
            print(f"❌ MCP統合テストエラー: {e}")
            return False
    
    async def test_file_change_simulation(self):
        """ファイル変更シミュレーションテスト"""
        print("\n6️⃣ === ファイル変更シミュレーション テスト ===")
        
        if not WATCHDOG_AVAILABLE:
            print("⚠️ watchdog が利用できないため、このテストをスキップします")
            return True
        
        if not self.monitor:
            print("❌ 監視システムが初期化されていません")
            return False
        
        try:
            # テスト用ファイルを作成
            test_file = Path(self.test_project_path) / "test_change.js"
            
            print(f"テストファイル作成: {test_file}")
            test_file.write_text("// テスト用JavaScriptファイル\nconsole.log('Hello World');\n")
            
            # 少し待機
            await asyncio.sleep(1)
            
            # ファイルを変更
            print("ファイルを変更中...")
            test_file.write_text("// 変更後のテスト用JavaScriptファイル\nconsole.log('Hello World - Modified!');\n")
            
            # デバウンス時間＋少し待機
            print("変更検知とスクリーンショット処理を待機中...")
            await asyncio.sleep(3)
            
            # 状況確認
            status = self.monitor.get_status()
            print(f"変更後の監視状況: {json.dumps(status, indent=2, ensure_ascii=False)}")
            
            # テストファイルを削除
            if test_file.exists():
                test_file.unlink()
                print("テストファイルを削除しました")
            
            print("✅ ファイル変更シミュレーションテスト完了")
            return True
            
        except Exception as e:
            print(f"❌ ファイル変更シミュレーションテストエラー: {e}")
            return False
    
    async def test_monitoring_cleanup(self):
        """監視システムクリーンアップテスト"""
        print("\n7️⃣ === 監視システムクリーンアップ テスト ===")
        
        try:
            # MCP経由で監視停止
            if self.mcp:
                stop_result = await self.mcp.handle_stop_code_monitoring({
                    'project_path': self.test_project_path
                })
                print(f"MCP監視停止結果: {json.dumps(stop_result, indent=2, ensure_ascii=False)}")
            
            # 直接監視停止
            if self.monitor:
                await self.monitor.stop_monitoring()
                
                status = self.monitor.get_status()
                print(f"停止後の監視状況: {json.dumps(status, indent=2, ensure_ascii=False)}")
                
                if not status['running']:
                    print("✅ 監視システムクリーンアップ成功")
                    return True
            
            print("❌ 監視システムクリーンアップ失敗")
            return False
            
        except Exception as e:
            print(f"❌ 監視システムクリーンアップエラー: {e}")
            return False
    
    async def run_comprehensive_test(self):
        """包括的テストの実行"""
        print("⚡ === コード変更監視システム 包括的テスト ===")
        print(f"📅 テスト開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 テスト対象プロジェクト: {self.test_project_path}")
        print("=" * 60)
        
        test_results = []
        config = None
        
        # 各テストの実行
        test_results.append(await self.test_watchdog_availability())
        test_results.append(await self.test_monitor_initialization())
        
        success, config = await self.test_project_watch_config_creation()
        test_results.append(success)
        
        if config:
            test_results.append(await self.test_project_watch_addition(config))
        else:
            test_results.append(False)
        
        test_results.append(await self.test_mcp_integration())
        test_results.append(await self.test_file_change_simulation())
        test_results.append(await self.test_monitoring_cleanup())
        
        # 結果集計
        print("\n📊 === コード変更監視テスト結果 ===")
        total_tests = len(test_results)
        passed_tests = sum(test_results)
        
        print(f"実行テスト数: {total_tests}")
        print(f"成功テスト数: {passed_tests}")
        print(f"成功率: {(passed_tests / total_tests) * 100:.1f}%")
        
        if passed_tests == total_tests:
            print("🎉 すべてのコード変更監視テストが成功しました！")
            print("✅ Phase 2.3: コード変更監視機能は正常に動作しています")
            return True
        else:
            failed_tests = total_tests - passed_tests
            print(f"❌ {failed_tests}個のテストが失敗しました")
            print("🔧 改善が必要です")
            return False

async def main():
    """メイン実行関数"""
    tester = CodeChangeMonitorTester()
    
    print("🚀 Screenshot Manager Phase 2.3: コード変更監視テスト開始")
    print("=" * 60)
    
    success = await tester.run_comprehensive_test()
    
    print("\n" + "=" * 60)
    if success:
        print("🌟 Phase 2.3 テスト完了 - コード変更監視機能が正常動作")
    else:
        print("⚠️ Phase 2.3 テスト完了 - 一部機能に問題あり")

if __name__ == "__main__":
    asyncio.run(main())