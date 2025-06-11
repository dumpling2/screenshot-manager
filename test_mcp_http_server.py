#!/usr/bin/env python3
"""
MCP HTTP Server テストスクリプト
HTTPエンドポイント経由でMCP機能をテスト
"""

import asyncio
import json
import sys
import time
import requests
import subprocess
from pathlib import Path
from datetime import datetime
import logging

# パス追加
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MCPHTTPTester:
    """MCP HTTP Server のテスト"""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.test_project_path = str(Path.cwd() / "demo_vue_project")
        self.logger = logging.getLogger(__name__)
        self.server_process = None
        
    def start_server(self):
        """テスト用サーバーを起動"""
        try:
            self.logger.info("🚀 MCP HTTP Server を起動中...")
            
            server_script = Path(__file__).parent / "src" / "integrations" / "mcp_http_server.py"
            
            self.server_process = subprocess.Popen([
                'python3', str(server_script), '--port', '8080'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # サーバー起動待機
            max_wait = 10
            for i in range(max_wait):
                try:
                    response = requests.get(f"{self.base_url}/", timeout=1)
                    if response.status_code == 200:
                        self.logger.info("✅ MCP HTTP Server が起動しました")
                        return True
                except requests.exceptions.ConnectionError:
                    time.sleep(1)
                    continue
            
            self.logger.error("❌ MCP HTTP Server の起動に失敗しました")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ サーバー起動エラー: {e}")
            return False
    
    def stop_server(self):
        """サーバーを停止"""
        if self.server_process:
            self.logger.info("🛑 MCP HTTP Server を停止中...")
            self.server_process.terminate()
            self.server_process.wait()
            self.logger.info("✅ サーバーを停止しました")
    
    def test_health_check(self):
        """ヘルスチェックテスト"""
        print("\n1️⃣ === ヘルスチェック テスト ===")
        
        try:
            response = requests.get(f"{self.base_url}/")
            
            print(f"URL: GET {self.base_url}/")
            print(f"ステータス: {response.status_code}")
            print(f"レスポンス: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('service') == 'Screenshot Manager MCP Server':
                    print("✅ ヘルスチェック成功")
                    return True
            
            print("❌ ヘルスチェック失敗")
            return False
            
        except Exception as e:
            print(f"❌ ヘルスチェックエラー: {e}")
            return False
    
    def test_status_endpoint(self):
        """ステータスエンドポイントテスト"""
        print("\n2️⃣ === ステータス エンドポイント テスト ===")
        
        try:
            response = requests.get(f"{self.base_url}/status")
            
            print(f"URL: GET {self.base_url}/status")
            print(f"ステータス: {response.status_code}")
            print(f"レスポンス: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'status' in data:
                    print("✅ ステータス取得成功")
                    return True
            
            print("❌ ステータス取得失敗")
            return False
            
        except Exception as e:
            print(f"❌ ステータス取得エラー: {e}")
            return False
    
    def test_project_detection_endpoint(self):
        """プロジェクト検出エンドポイントテスト"""
        print("\n3️⃣ === プロジェクト検出 エンドポイント テスト ===")
        
        try:
            data = {
                'project_path': self.test_project_path
            }
            
            response = requests.post(
                f"{self.base_url}/project/detect",
                json=data,
                headers={'Content-Type': 'application/json'}
            )
            
            print(f"URL: POST {self.base_url}/project/detect")
            print(f"入力: {json.dumps(data, indent=2, ensure_ascii=False)}")
            print(f"ステータス: {response.status_code}")
            print(f"レスポンス: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print("✅ プロジェクト検出成功")
                    return True
            
            print("❌ プロジェクト検出失敗")
            return False
            
        except Exception as e:
            print(f"❌ プロジェクト検出エラー: {e}")
            return False
    
    def test_config_generation_endpoint(self):
        """設定生成エンドポイントテスト"""
        print("\n4️⃣ === 設定生成 エンドポイント テスト ===")
        
        try:
            data = {
                'project_path': self.test_project_path,
                'format': 'yaml'
            }
            
            response = requests.post(
                f"{self.base_url}/config/generate",
                json=data,
                headers={'Content-Type': 'application/json'}
            )
            
            print(f"URL: POST {self.base_url}/config/generate")
            print(f"入力: {json.dumps(data, indent=2, ensure_ascii=False)}")
            print(f"ステータス: {response.status_code}")
            print(f"レスポンス: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print("✅ 設定生成成功")
                    return True
            
            print("❌ 設定生成失敗")
            return False
            
        except Exception as e:
            print(f"❌ 設定生成エラー: {e}")
            return False
    
    def test_auto_screenshot_endpoint(self):
        """自動スクリーンショットエンドポイントテスト"""
        print("\n5️⃣ === 自動スクリーンショット エンドポイント テスト ===")
        
        try:
            data = {
                'project_path': self.test_project_path,
                'framework': 'Vue',
                'immediate': True
            }
            
            response = requests.post(
                f"{self.base_url}/screenshot/auto",
                json=data,
                headers={'Content-Type': 'application/json'}
            )
            
            print(f"URL: POST {self.base_url}/screenshot/auto")
            print(f"入力: {json.dumps(data, indent=2, ensure_ascii=False)}")
            print(f"ステータス: {response.status_code}")
            print(f"レスポンス: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print("✅ 自動スクリーンショット成功")
                    return True
            
            print("❌ 自動スクリーンショット失敗")
            return False
            
        except Exception as e:
            print(f"❌ 自動スクリーンショットエラー: {e}")
            return False
    
    def test_manual_screenshot_endpoint(self):
        """手動スクリーンショットエンドポイントテスト"""
        print("\n6️⃣ === 手動スクリーンショット エンドポイント テスト ===")
        
        try:
            data = {
                'project_path': self.test_project_path,
                'pages': ['/', '/about'],
                'config': {
                    'viewport': {
                        'width': 1920,
                        'height': 1080
                    }
                }
            }
            
            response = requests.post(
                f"{self.base_url}/screenshot/manual",
                json=data,
                headers={'Content-Type': 'application/json'}
            )
            
            print(f"URL: POST {self.base_url}/screenshot/manual")
            print(f"入力: {json.dumps(data, indent=2, ensure_ascii=False)}")
            print(f"ステータス: {response.status_code}")
            print(f"レスポンス: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print("✅ 手動スクリーンショット成功")
                    return True
            
            print("❌ 手動スクリーンショット失敗")
            return False
            
        except Exception as e:
            print(f"❌ 手動スクリーンショットエラー: {e}")
            return False
    
    def run_comprehensive_test(self):
        """包括的テストの実行"""
        print("🌐 === MCP HTTP Server 包括的API テスト ===")
        print(f"📅 テスト開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 ベースURL: {self.base_url}")
        print(f"🎯 テスト対象プロジェクト: {self.test_project_path}")
        print("=" * 60)
        
        test_results = []
        
        # 各エンドポイントのテスト実行
        test_results.append(self.test_health_check())
        test_results.append(self.test_status_endpoint())
        test_results.append(self.test_project_detection_endpoint())
        test_results.append(self.test_config_generation_endpoint())
        test_results.append(self.test_auto_screenshot_endpoint())
        test_results.append(self.test_manual_screenshot_endpoint())
        
        # 結果集計
        print("\n📊 === HTTP API テスト結果 ===")
        total_tests = len(test_results)
        passed_tests = sum(test_results)
        
        print(f"実行テスト数: {total_tests}")
        print(f"成功テスト数: {passed_tests}")
        print(f"成功率: {(passed_tests / total_tests) * 100:.1f}%")
        
        if passed_tests == total_tests:
            print("🎉 すべてのHTTP APIテストが成功しました！")
            print("✅ MCP HTTP Server は正常に動作しています")
            return True
        else:
            failed_tests = total_tests - passed_tests
            print(f"❌ {failed_tests}個のテストが失敗しました")
            print("🔧 改善が必要です")
            return False

def main():
    """メイン実行関数"""
    tester = MCPHTTPTester()
    
    print("🚀 Screenshot Manager MCP HTTP Server テスト開始")
    print("=" * 60)
    
    # サーバー起動
    if not tester.start_server():
        print("❌ サーバー起動に失敗しました")
        return
    
    try:
        # テスト実行
        success = tester.run_comprehensive_test()
        
        print("\n" + "=" * 60)
        if success:
            print("🌟 MCP HTTP Server テスト完了 - すべてのAPIが正常動作")
        else:
            print("⚠️ MCP HTTP Server テスト完了 - 一部APIに問題あり")
            
    finally:
        # サーバー停止
        tester.stop_server()

if __name__ == "__main__":
    main()