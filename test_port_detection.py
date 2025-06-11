#!/usr/bin/env python3
"""
ポート検知機能の単体テスト
"""

import sys
from pathlib import Path

# パス追加
sys.path.insert(0, str(Path(__file__).parent))

from src.monitors.webapp_monitor import PortMonitor
import logging

# ログレベルを設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_port_detection():
    print("🔍 ポート検知テストを開始...")
    
    # ポートモニターを作成（ポート8000のみテスト）
    monitor = PortMonitor(ports=[8000])
    
    print("📊 ポート8000の状態をチェック...")
    active_ports = monitor.check_ports()
    
    print(f"検知結果: {active_ports}")
    
    if active_ports.get(8000):
        print("✅ ポート8000が検知されました!")
        
        # 新しいアプリの検出テスト
        print("🔍 新しいアプリの検出テスト...")
        new_apps = monitor.detect_new_apps()
        
        if new_apps:
            for app in new_apps:
                print(f"✅ アプリが検出されました:")
                print(f"   URL: {app.url}")
                print(f"   ポート: {app.port}")
                print(f"   フレームワーク: {app.framework}")
                print(f"   プロセス: {app.process_name}")
                print(f"   検出時刻: {app.detected_at}")
        else:
            print("⚠️  新しいアプリとして検出されませんでした")
    else:
        print("❌ ポート8000が検知されませんでした")
        
        # デバッグ: ssコマンドの出力を確認
        import subprocess
        cmd = "ss -tln | grep -E ':8000\\s'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(f"🔧 デバッグ - ssコマンド出力: '{result.stdout.strip()}'")
        
        # curlでのテスト
        cmd2 = "curl -s http://localhost:8000 | head -1"
        result2 = subprocess.run(cmd2, shell=True, capture_output=True, text=True)
        print(f"🔧 デバッグ - curlテスト: '{result2.stdout.strip()}'")

if __name__ == "__main__":
    test_port_detection()