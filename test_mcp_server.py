#!/usr/bin/env python3
"""
MCP Server 機能テストスクリプト
Claude Codeからの呼び出しをシミュレートして各ツールの動作を確認
"""

import sys
import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime

# パス追加
sys.path.insert(0, str(Path(__file__).parent))

from src.integrations.mcp_server import ScreenshotManagerMCP, ClaudeCodeIntegration

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MCPServerTester:
    """MCP Server機能のテスト"""
    
    def __init__(self):
        self.mcp = ScreenshotManagerMCP()
        self.test_project_path = str(Path.cwd() / "demo_vue_project")
        self.logger = logging.getLogger(__name__)
        
    async def test_project_detection_tool(self):
        """プロジェクト検出ツールのテスト"""
        print("\n1️⃣ === プロジェクト検出ツール テスト ===")
        
        test_args = {
            'project_path': self.test_project_path
        }
        
        result = await self.mcp.handle_project_detection(test_args)
        
        print(f"入力: {test_args}")
        # JSON serializable に変換して表示
        def convert_for_json(obj):
            if hasattr(obj, '__dict__'):
                return {k: str(v) if hasattr(v, '__fspath__') else v for k, v in obj.__dict__.items()}
            return str(obj) if hasattr(obj, '__fspath__') else obj
        
        try:
            print(f"結果: {json.dumps(result, indent=2, ensure_ascii=False, default=convert_for_json)}")
        except Exception as e:
            print(f"結果: {result} (JSON変換エラー: {e})")
        
        if result['success']:
            print("✅ プロジェクト検出成功")
        else:
            print("❌ プロジェクト検出失敗")
            
        return result['success']
    
    async def test_config_generation_tool(self):
        """設定ファイル生成ツールのテスト"""
        print("\n2️⃣ === 設定ファイル生成ツール テスト ===")
        
        test_args = {
            'project_path': self.test_project_path,
            'format': 'yaml'
        }
        
        result = await self.mcp.handle_config_generation(test_args)
        
        print(f"入力: {test_args}")
        # JSON serializable に変換して表示
        def convert_for_json(obj):
            if hasattr(obj, '__dict__'):
                return {k: str(v) if hasattr(v, '__fspath__') else v for k, v in obj.__dict__.items()}
            return str(obj) if hasattr(obj, '__fspath__') else obj
        
        try:
            print(f"結果: {json.dumps(result, indent=2, ensure_ascii=False, default=convert_for_json)}")
        except Exception as e:
            print(f"結果: {result} (JSON変換エラー: {e})")
        
        if result['success']:
            print("✅ 設定ファイル生成成功")
        else:
            print("❌ 設定ファイル生成失敗")
            
        return result['success']
    
    async def test_status_check_tool(self):
        """ステータス確認ツールのテスト"""
        print("\n3️⃣ === ステータス確認ツール テスト ===")
        
        test_args = {}
        
        result = await self.mcp.handle_status_check(test_args)
        
        print(f"入力: {test_args}")
        # JSON serializable に変換して表示
        def convert_for_json(obj):
            if hasattr(obj, '__dict__'):
                return {k: str(v) if hasattr(v, '__fspath__') else v for k, v in obj.__dict__.items()}
            return str(obj) if hasattr(obj, '__fspath__') else obj
        
        try:
            print(f"結果: {json.dumps(result, indent=2, ensure_ascii=False, default=convert_for_json)}")
        except Exception as e:
            print(f"結果: {result} (JSON変換エラー: {e})")
        
        if result['success']:
            print("✅ ステータス確認成功")
        else:
            print("❌ ステータス確認失敗")
            
        return result['success']
    
    async def test_auto_screenshot_tool(self):
        """自動スクリーンショットツールのテスト"""
        print("\n4️⃣ === 自動スクリーンショット ツール テスト ===")
        
        test_args = {
            'project_path': self.test_project_path,
            'framework': 'Vue',
            'immediate': True
        }
        
        result = await self.mcp.handle_auto_screenshot(test_args)
        
        print(f"入力: {test_args}")
        # JSON serializable に変換して表示
        def convert_for_json(obj):
            if hasattr(obj, '__dict__'):
                return {k: str(v) if hasattr(v, '__fspath__') else v for k, v in obj.__dict__.items()}
            return str(obj) if hasattr(obj, '__fspath__') else obj
        
        try:
            print(f"結果: {json.dumps(result, indent=2, ensure_ascii=False, default=convert_for_json)}")
        except Exception as e:
            print(f"結果: {result} (JSON変換エラー: {e})")
        
        if result['success']:
            print("✅ 自動スクリーンショット成功")
        else:
            print("❌ 自動スクリーンショット失敗")
            
        return result['success']
    
    async def test_manual_screenshot_tool(self):
        """手動スクリーンショットツールのテスト"""
        print("\n5️⃣ === 手動スクリーンショット ツール テスト ===")
        
        test_args = {
            'project_path': self.test_project_path,
            'pages': ['/', '/about'],
            'config': {
                'viewport': {
                    'width': 1920,
                    'height': 1080
                }
            }
        }
        
        result = await self.mcp.handle_manual_screenshot(test_args)
        
        print(f"入力: {test_args}")
        # JSON serializable に変換して表示
        def convert_for_json(obj):
            if hasattr(obj, '__dict__'):
                return {k: str(v) if hasattr(v, '__fspath__') else v for k, v in obj.__dict__.items()}
            return str(obj) if hasattr(obj, '__fspath__') else obj
        
        try:
            print(f"結果: {json.dumps(result, indent=2, ensure_ascii=False, default=convert_for_json)}")
        except Exception as e:
            print(f"結果: {result} (JSON変換エラー: {e})")
        
        if result['success']:
            print("✅ 手動スクリーンショット成功")
        else:
            print("❌ 手動スクリーンショット失敗")
            
        return result['success']
    
    async def test_claude_code_integration(self):
        """Claude Code統合ヘルパーのテスト"""
        print("\n6️⃣ === Claude Code統合ヘルパー テスト ===")
        
        # プロジェクト作成時のフック
        print("📂 プロジェクト作成時のフック...")
        result1 = await ClaudeCodeIntegration.on_project_created(
            self.test_project_path, 
            'Vue'
        )
        print(f"プロジェクト作成フック結果: {result1['success']}")
        
        # 手動スクリーンショット要求
        print("📸 手動スクリーンショット要求...")
        result2 = await ClaudeCodeIntegration.take_manual_screenshot(
            self.test_project_path,
            ['/', '/about']
        )
        print(f"手動スクリーンショット結果: {result2['success']}")
        
        return result1['success'] and result2['success']
    
    async def test_server_tool_registry(self):
        """サーバーツール登録の確認"""
        print("\n7️⃣ === サーバーツール登録 確認 ===")
        
        tools = self.mcp.server.tools
        print(f"登録済みツール数: {len(tools)}")
        
        for tool_name, tool_info in tools.items():
            print(f"  - {tool_name}: {tool_info['description']}")
        
        expected_tools = [
            'auto_screenshot_on_create',
            'take_screenshot', 
            'detect_project',
            'generate_config',
            'get_status'
        ]
        
        all_registered = all(tool in tools for tool in expected_tools)
        
        if all_registered:
            print("✅ すべての必要なツールが登録されています")
        else:
            missing = [tool for tool in expected_tools if tool not in tools]
            print(f"❌ 未登録ツール: {missing}")
            
        return all_registered
    
    async def run_comprehensive_test(self):
        """包括的テストの実行"""
        print("🧪 === MCP Server 包括的機能テスト ===")
        print(f"📅 テスト開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 テスト対象プロジェクト: {self.test_project_path}")
        print("=" * 60)
        
        test_results = []
        
        # 各ツールのテスト実行
        test_results.append(await self.test_server_tool_registry())
        test_results.append(await self.test_project_detection_tool())
        test_results.append(await self.test_config_generation_tool())
        test_results.append(await self.test_status_check_tool())
        test_results.append(await self.test_auto_screenshot_tool())
        test_results.append(await self.test_manual_screenshot_tool())
        test_results.append(await self.test_claude_code_integration())
        
        # 結果集計
        print("\n📊 === テスト結果 ===")
        total_tests = len(test_results)
        passed_tests = sum(test_results)
        
        print(f"実行テスト数: {total_tests}")
        print(f"成功テスト数: {passed_tests}")
        print(f"成功率: {(passed_tests / total_tests) * 100:.1f}%")
        
        if passed_tests == total_tests:
            print("🎉 すべてのテストが成功しました！")
            print("✅ MCP Server は正常に動作しています")
            return True
        else:
            failed_tests = total_tests - passed_tests
            print(f"❌ {failed_tests}個のテストが失敗しました")
            print("🔧 改善が必要です")
            return False

async def main():
    """メイン実行関数"""
    tester = MCPServerTester()
    
    print("🚀 Screenshot Manager MCP Server テスト開始")
    print("=" * 60)
    
    success = await tester.run_comprehensive_test()
    
    print("\n" + "=" * 60)
    if success:
        print("🌟 MCP Server テスト完了 - すべての機能が正常動作")
    else:
        print("⚠️ MCP Server テスト完了 - 一部機能に問題あり")

if __name__ == "__main__":
    asyncio.run(main())