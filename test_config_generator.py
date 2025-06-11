#!/usr/bin/env python3
"""
設定ファイル生成機能のテストスクリプト
"""

import sys
from pathlib import Path
import logging

# パス追加
sys.path.insert(0, str(Path(__file__).parent))

from src.analyzers.config_generator import ConfigGenerator
from src.detectors.project_detector import ProjectDetector

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_config_generation():
    print("🔧 設定ファイル生成機能のテストを開始...")
    
    generator = ConfigGenerator()
    
    # テスト用Reactプロジェクトで設定生成
    test_project_path = Path.cwd() / "test_react_project"
    
    if not test_project_path.exists():
        print("❌ テスト用プロジェクトが見つかりません")
        return
    
    print(f"📁 テスト対象: {test_project_path}")
    
    # 1. プロジェクト検出テスト
    detector = ProjectDetector()
    project_info = detector.detect_project(test_project_path)
    
    if project_info:
        print(f"✅ プロジェクト検出成功: {project_info.framework}")
    else:
        print("❌ プロジェクト検出失敗")
        return
    
    # 2. 設定生成テスト
    config = generator.generate_config(project_info)
    print("✅ 設定生成成功")
    
    # 3. 設定内容の表示
    print("\n📋 生成された設定（主要部分）:")
    print(f"  Framework: {config['project']['framework']}")
    print(f"  Dev Command: {config['project']['dev_command']}")
    print(f"  Port: {config['project']['port']}")
    print(f"  Language: {config['project']['language']}")
    
    # 4. 設定ファイル保存テスト
    config_file = generator.save_config(config, test_project_path, format="yaml")
    
    if config_file and config_file.exists():
        print(f"✅ 設定ファイル保存成功: {config_file}")
        
        # 生成された設定ファイルの内容を表示
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("\n📄 生成された設定ファイル内容:")
        print("=" * 50)
        print(content)
        print("=" * 50)
        
        # JSON形式でも保存テスト
        json_config_file = generator.save_config(config, test_project_path, format="json")
        print(f"✅ JSON設定ファイルも保存: {json_config_file}")
        
    else:
        print("❌ 設定ファイル保存失敗")
    
    # 5. カスタム設定でのテスト
    print("\n🔧 カスタム設定テスト...")
    custom_settings = {
        "testing": {
            "pages_to_test": [
                {"path": "/", "name": "Home"},
                {"path": "/about", "name": "About"},
                {"path": "/contact", "name": "Contact"}
            ]
        },
        "capture": {
            "wait_before_capture": 5000
        }
    }
    
    custom_config = generator.generate_config(project_info, custom_settings)
    print("✅ カスタム設定生成成功")
    print(f"  追加ページ数: {len(custom_config['testing']['pages_to_test'])}")
    print(f"  待機時間: {custom_config['capture']['wait_before_capture']}ms")

if __name__ == "__main__":
    test_config_generation()