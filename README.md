# Screenshot Manager for WSL

Claude Codeで作成したWebアプリケーションの起動後画面を自動的にキャプチャし、動作確認を支援するツールです。

<p align="center">
  <img src="https://img.shields.io/badge/Platform-WSL2-blue" alt="Platform">
  <img src="https://img.shields.io/badge/Python-3.8+-green" alt="Python">
  <img src="https://img.shields.io/badge/Status-Active Development-orange" alt="Status">
</p>

## 🎯 主要機能

### ✨ 現在利用可能な機能
- 📁 **自動スクリーンショット管理**: Windows→WSL自動転送・整理
- 🎯 **高度撮影機能**: モニター・ウィンドウ指定撮影
- 🔍 **重複検出**: 自動重複ファイル削除
- 🧹 **自動クリーンアップ**: 古いファイルの自動削除

### 🚀 新機能（v2.0 - 開発中）
- 🌐 **Webアプリ自動検知**: Claude Codeアプリの起動を自動検出
- 🤖 **ブラウザ自動化**: 自動アクセス・マルチデバイステスト
- 📊 **動作確認レポート**: HTML形式の見やすいレポート

## 🚀 クイックスタート

```bash
# 1. リポジトリをクローン
git clone https://github.com/your-username/screenshot-manager.git
cd screenshot-manager

# 2. セットアップ
./setup.sh

# 3. 基本監視開始
./screenshot_manager.sh start

# 4. Webアプリ監視（新機能）
./scripts/install_webapp_deps.sh  # 初回のみ
python3 src/monitors/webapp_monitor.py
```

## 📋 使用シナリオ

### 現在の使い方
```bash
# Claude Codeでアプリを作成
claude> "Reactでタスク管理アプリを作って"

# 手動スクリーンショット
./take_screenshot.sh

# 自動的に整理・保存される ✓
```

### 新機能での使い方（v2.0）
```bash
# Claude Codeでアプリを作成
claude> "Reactでタスク管理アプリを作って"

# 自動的に以下が実行される：
# 1. Webアプリの起動検知 🔍
# 2. ブラウザで自動オープン 🌐
# 3. 複数解像度でキャプチャ 📱💻
# 4. レポート生成 📊
```

## 📖 ドキュメント

| カテゴリ | ドキュメント | 内容 |
|---------|-------------|------|
| **👤 ユーザー向け** | [📖 セットアップガイド](docs/user/SETUP.md) | 詳細インストール手順 |
| | [🎮 使用方法](docs/user/USAGE.md) | 機能別の使い方 |
| | [🔧 トラブルシューティング](docs/user/TROUBLESHOOTING.md) | よくある問題と解決法 |
| **👨‍💻 開発者向け** | [🗺️ ロードマップ](docs/dev/ROADMAP.md) | 開発計画・今後の機能 |
| | [🏗️ アーキテクチャ](docs/dev/ARCHITECTURE.md) | システム構成・技術仕様 |
| **📐 設計書** | [🌐 Webアプリ検知](docs/design/webapp-detection.md) | 自動検知システム設計 |

## 🔧 必要な環境

- **OS**: Windows 10/11 + WSL2
- **Python**: 3.8以上
- **その他**: PowerShell, bash

### 新機能用（v2.0）
- **Node.js**: Webアプリ検知用
- **Playwright**: ブラウザ自動化用

## ⚡ 主要コマンド

```bash
# 基本監視
./screenshot_manager.sh start|stop|status

# 高度撮影
./take_screenshot.sh --monitor 0
./take_screenshot.sh --process Chrome

# Webアプリ監視（新機能）
python3 src/monitors/webapp_monitor.py

# テスト
python3 tests/test_webapp_monitor.py
```

## 🤝 貢献・サポート

- 🐛 **バグ報告**: [Issues](https://github.com/your-username/screenshot-manager/issues)
- 💡 **機能要望**: [Discussions](https://github.com/your-username/screenshot-manager/discussions)
- 📖 **開発に参加**: [開発ガイド](docs/dev/CONTRIBUTING.md)

## 📊 開発状況

| Phase | 機能 | 状況 |
|-------|------|------|
| ✅ v1.0 | 基本スクリーンショット管理 | **完成** |
| 🚧 v2.0 | Webアプリ自動検知 | **開発中** |
| 📅 v3.0 | Claude Code連携強化 | 計画中 |
| 📅 v4.0 | CI/CD統合 | 計画中 |

## 📄 ライセンス

MIT License - 詳細は [LICENSE](LICENSE) をご覧ください。

---

<p align="center">
  <strong>🎉 Claude Codeでの開発を、より効率的に！</strong>
</p>