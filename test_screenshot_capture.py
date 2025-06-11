#!/usr/bin/env python3
"""
スクリーンショット撮影機能の単体テスト
"""

import sys
from pathlib import Path
import asyncio
import logging

# パス追加
sys.path.insert(0, str(Path(__file__).parent))

from src.monitors.webapp_monitor import AppInfo
from src.capture.playwright_capture import capture_webapp_sync

# ログレベルを設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_screenshot_capture():
    print("📸 スクリーンショット撮影テストを開始...")
    
    # テスト用アプリ情報
    app_info = AppInfo(
        port=8000,
        url="http://localhost:8000",
        framework="Test App",
        process_name="python3"
    )
    
    # 設定（実際の設定ファイルから読み込み）
    import json
    config_path = Path(__file__).parent / "config" / "webapp_config.json"
    
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
            print(f"📋 設定ファイルから読み込み: {config['capture']['pages']}")
    else:
        config = {
            "capture": {
                "wait_before_capture": 1000,
                "pages": ["/", "/about.html"],  # テスト用ページリスト
                "viewports": {
                    "desktop": {"width": 1920, "height": 1080},
                    "tablet": {"width": 768, "height": 1024},
                    "mobile": {"width": 375, "height": 667}
                }
            }
        }
        print("📋 デフォルト設定を使用")
    
    logger = logging.getLogger(__name__)
    
    print(f"🎯 対象URL: {app_info.url}")
    
    try:
        # スクリーンショット撮影実行
        result = capture_webapp_sync(app_info, config, logger)
        
        if result:
            print(f"✅ スクリーンショット撮影成功!")
            print(f"📁 出力ディレクトリ: {result}")
            
            # 生成されたファイルをチェック
            output_path = Path(result)
            if output_path.exists():
                files = list(output_path.glob("*"))
                print(f"📄 生成されたファイル数: {len(files)}")
                for file in files:
                    print(f"   - {file.name}")
                    
                # レポートHTMLの確認
                report_file = output_path / "report.html"
                if report_file.exists():
                    print("✅ HTMLレポートが生成されました")
                    print(f"🌐 レポートURL: file://{report_file.absolute()}")
                else:
                    print("⚠️  HTMLレポートが見つかりません")
            else:
                print(f"❌ 出力ディレクトリが見つかりません: {result}")
        else:
            print("❌ スクリーンショット撮影に失敗しました")
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_screenshot_capture()