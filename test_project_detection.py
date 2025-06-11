#!/usr/bin/env python3
"""
プロジェクト検出機能のテストスクリプト
"""

import sys
from pathlib import Path
import logging

# パス追加
sys.path.insert(0, str(Path(__file__).parent))

from src.detectors.project_detector import ProjectDetector

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_project_detection():
    print("🔍 プロジェクト検出機能のテストを開始...")
    
    detector = ProjectDetector()
    
    # テスト対象ディレクトリ
    test_dirs = [
        Path.cwd(),  # 現在のディレクトリ（Screenshot Manager）
        Path.cwd() / "test_webapp",  # テスト用Webアプリ
    ]
    
    # Claude Codeプロジェクトの典型例をシミュレート
    print("\n📦 テスト用Reactプロジェクトを作成...")
    test_react_dir = Path.cwd() / "test_react_project"
    test_react_dir.mkdir(exist_ok=True)
    
    # package.jsonを作成
    package_json = {
        "name": "test-react-app",
        "version": "0.1.0",
        "private": True,
        "dependencies": {
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
            "react-scripts": "5.0.1"
        },
        "scripts": {
            "start": "react-scripts start",
            "build": "react-scripts build",
            "test": "react-scripts test",
            "eject": "react-scripts eject"
        }
    }
    
    import json
    with open(test_react_dir / "package.json", 'w') as f:
        json.dump(package_json, f, indent=2)
    
    # src/index.jsを作成
    (test_react_dir / "src").mkdir(exist_ok=True)
    with open(test_react_dir / "src" / "index.js", 'w') as f:
        f.write("import React from 'react';\nimport ReactDOM from 'react-dom';\n")
    
    test_dirs.append(test_react_dir)
    
    # 各ディレクトリでテスト
    for test_dir in test_dirs:
        print(f"\n📁 テスト対象: {test_dir}")
        
        if not test_dir.exists():
            print(f"❌ ディレクトリが存在しません: {test_dir}")
            continue
        
        project_info = detector.detect_project(test_dir)
        
        if project_info:
            print(f"✅ プロジェクト検出成功!")
            print(f"   名前: {project_info.name}")
            print(f"   フレームワーク: {project_info.framework}")
            print(f"   言語: {project_info.language}")
            print(f"   パッケージマネージャー: {project_info.package_manager}")
            print(f"   開発コマンド: {project_info.dev_command}")
            print(f"   デフォルトポート: {project_info.default_port}")
            print(f"   信頼度: {project_info.confidence:.2f}")
            if project_info.dependencies:
                print(f"   主要依存関係: {', '.join(project_info.dependencies)}")
        else:
            print(f"❌ プロジェクトが検出されませんでした")
    
    # ディレクトリスキャンテスト
    print(f"\n🔍 ディレクトリスキャンテスト: {Path.cwd()}")
    projects = detector.scan_directory(Path.cwd(), max_depth=1)
    
    if projects:
        print(f"✅ {len(projects)}個のプロジェクトを検出:")
        for i, project in enumerate(projects, 1):
            print(f"   {i}. {project.name} ({project.framework}) - {project.confidence:.2f}")
    else:
        print("❌ プロジェクトが見つかりませんでした")

if __name__ == "__main__":
    test_project_detection()