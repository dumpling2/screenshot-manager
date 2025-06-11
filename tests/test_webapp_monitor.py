#!/usr/bin/env python3
"""
Webアプリ監視機能のテストスクリプト
"""

import sys
import time
import threading
import subprocess
from pathlib import Path
import json

# 親ディレクトリをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

def start_test_server(port=3000):
    """テスト用のHTTPサーバーを起動"""
    print(f"🚀 テストサーバーをポート{port}で起動中...")
    
    try:
        # Pythonの簡易HTTPサーバーを起動
        process = subprocess.Popen([
            'python3', '-m', 'http.server', str(port)
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # サーバーの起動を少し待つ
        time.sleep(2)
        
        # サーバーが起動しているかチェック
        import requests
        response = requests.get(f"http://localhost:{port}", timeout=5)
        print(f"✅ テストサーバー起動成功 - ステータス: {response.status_code}")
        return process
        
    except Exception as e:
        print(f"❌ テストサーバー起動失敗: {e}")
        return None

def test_port_detection():
    """ポート検知機能のテスト"""
    print("\n🔍 ポート検知機能をテストします...")
    
    # テストサーバーを起動
    server_process = start_test_server(3000)
    
    if not server_process:
        print("❌ テストサーバーの起動に失敗しました")
        return False
    
    try:
        # webapp_monitorをインポート
        from src.monitors.webapp_monitor import PortMonitor
        
        # ポートモニターを作成
        monitor = PortMonitor(ports=[3000])
        
        # ポートチェック
        active_ports = monitor.check_ports()
        
        if active_ports.get(3000):
            print("✅ ポート3000の検知成功!")
            
            # 新しいアプリの検出テスト
            new_apps = monitor.detect_new_apps()
            
            if new_apps:
                app = new_apps[0]
                print(f"✅ アプリ検出成功:")
                print(f"   URL: {app.url}")
                print(f"   ポート: {app.port}")
                print(f"   フレームワーク: {app.framework}")
                return True
            else:
                print("⚠️ 新しいアプリとして検出されませんでした")
                return False
        else:
            print("❌ ポート3000が検出されませんでした")
            return False
            
    except Exception as e:
        print(f"❌ ポート検知テストエラー: {e}")
        return False
    finally:
        # テストサーバーを停止
        if server_process:
            server_process.terminate()
            server_process.wait()
            print("🛑 テストサーバーを停止しました")

def test_config_loading():
    """設定ファイル読み込みのテスト"""
    print("\n⚙️ 設定ファイル読み込みをテストします...")
    
    try:
        from src.monitors.webapp_monitor import WebAppMonitor
        
        # 設定ファイルが存在しない場合でもデフォルト設定で動作することを確認
        monitor = WebAppMonitor()
        
        print(f"✅ 設定読み込み成功:")
        print(f"   チェック間隔: {monitor.config.get('check_interval')}秒")
        print(f"   監視ポート数: {len(monitor.monitored_ports)}個")
        print(f"   監視ポート: {monitor.monitored_ports}")
        
        return True
        
    except Exception as e:
        print(f"❌ 設定読み込みテストエラー: {e}")
        return False

def test_webapp_config():
    """Webapp設定ファイルのテスト"""
    print("\n📄 Webapp設定ファイルをテストします...")
    
    config_path = Path("config/webapp_config.json")
    
    if not config_path.exists():
        print("⚠️ webapp_config.json が存在しません。テンプレートから作成します...")
        
        template_path = Path("config/webapp_config.json.template")
        if template_path.exists():
            import shutil
            shutil.copy(template_path, config_path)
            print("✅ webapp_config.json を作成しました")
        else:
            print("❌ テンプレートファイルが見つかりません")
            return False
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        print("✅ 設定ファイル読み込み成功:")
        print(f"   チェック間隔: {config.get('check_interval')}秒")
        print(f"   起動タイムアウト: {config.get('startup_timeout')}秒")
        print(f"   ビューポート数: {len(config.get('capture', {}).get('viewports', {}))}")
        
        return True
        
    except Exception as e:
        print(f"❌ 設定ファイルテストエラー: {e}")
        return False

def main():
    """メインテスト関数"""
    print("🧪 Webアプリ監視機能のテストを開始します...")
    print("=" * 50)
    
    # テスト結果を記録
    results = {
        'config_loading': test_config_loading(),
        'webapp_config': test_webapp_config(),
        'port_detection': test_port_detection()
    }
    
    print("\n" + "=" * 50)
    print("📊 テスト結果:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n結果: {passed}/{total} テスト成功")
    
    if passed == total:
        print("🎉 すべてのテストが成功しました!")
        print("\n次のステップ:")
        print("1. Claude Codeでテスト用Webアプリを作成")
        print("2. ./webapp_monitor.py を実行")
        print("3. 自動的にスクリーンショットが撮影されることを確認")
    else:
        print("⚠️ 一部のテストが失敗しました")
        print("エラーを確認してください")
    
    return passed == total

if __name__ == "__main__":
    main()