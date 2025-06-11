# 📖 セットアップガイド

Screenshot Manager for WSLの詳細インストール手順です。

## 📋 前提条件

### 必須環境
- **Windows 10/11** with WSL2
- **Python 3.8以上** 
- **PowerShell** (Windowsに標準搭載)
- **bash** (WSLに標準搭載)

### 環境確認

```bash
# Python バージョン確認
python3 --version  # 3.8以上である必要があります

# WSL環境確認
uname -a  # Linuxカーネル情報が表示されます

# Windows連携確認
ls /mnt/c/Users/  # Windowsユーザーフォルダが見えることを確認
```

## 🚀 基本セットアップ

### 1. リポジトリのクローン

```bash
# SSHを使用する場合
git clone git@github.com:your-username/screenshot-manager.git
cd screenshot-manager

# HTTPSを使用する場合  
git clone https://github.com/your-username/screenshot-manager.git
cd screenshot-manager
```

### 2. 自動セットアップ

```bash
# セットアップスクリプト実行
./setup.sh
```

#### セットアップで実行される内容
- Python依存関係のインストール
- Windowsユーザー名の入力・設定
- スクリーンショットフォルダの確認
- 設定ファイルの自動生成
- 必要なディレクトリの作成
- 実行権限の設定

### 3. 設定の確認

```bash
# 設定ファイルを確認
cat config/config.json

# 設定内容の例：
{
  "windowsUsername": "YourWindowsUsername",
  "windowsScreenshotPath": "/mnt/c/Users/{username}/Pictures/Screenshots",
  "localScreenshotPath": "screenshots",
  "checkInterval": 2,
  "organizeByDate": true
}
```

## 🌐 Webアプリ監視機能のセットアップ（v2.0新機能）

### 1. 依存関係のインストール

```bash
# Webアプリ監視機能の依存関係を自動インストール
./scripts/install_webapp_deps.sh
```

#### インストールされる内容
- **requests**: HTTP通信用
- **playwright**: ブラウザ自動化用
- **Chromiumブラウザ**: Playwrightが使用
- **システム依存関係**: ブラウザ実行に必要

### 2. Webアプリ監視設定

```bash
# 設定ファイルを確認・編集
nano config/webapp_config.json
```

設定例：
```json
{
  "check_interval": 2,
  "additional_ports": [3333, 4444],
  "exclude_ports": [8888],
  "startup_timeout": 30,
  "capture": {
    "wait_before_capture": 2000,
    "viewports": {
      "desktop": {"width": 1920, "height": 1080},
      "tablet": {"width": 768, "height": 1024},
      "mobile": {"width": 375, "height": 667}
    }
  }
}
```

## 🧪 動作テスト

### 基本機能のテスト

```bash
# 1. 基本監視機能のテスト
./screenshot_manager.sh status

# 2. 手動スクリーンショット撮影テスト
./take_screenshot.sh

# 3. 監視開始
./screenshot_manager.sh start

# 4. 状態確認
./screenshot_manager.sh status
```

### Webアプリ監視機能のテスト

```bash
# 1. 統合テスト実行
python3 tests/test_webapp_monitor.py

# 期待される出力：
# ✅ webapp_monitor.py の基本的なインポートテスト成功
# ✅ PortMonitor初期化成功 - 監視ポート: 11個
# ✅ ポートチェック成功 - アクティブ: 0/11個
# 🎉 すべてのテストが成功しました!

# 2. 実際の監視開始
python3 src/monitors/webapp_monitor.py
```

## 📁 プロジェクト構造の確認

セットアップ後、以下の構造になっていることを確認してください：

```
screenshot-manager/
├── 📁 config/              # 設定ファイル
│   ├── config.json         # 基本設定
│   └── webapp_config.json  # Webアプリ監視設定
├── 📁 screenshots/         # スクリーンショット保存先
├── 📁 logs/               # ログファイル
├── 📁 docs/               # ドキュメント
├── 🔧 screenshot_manager.sh # 管理スクリプト
├── 📁 src/                  # ソースコード
│   ├── monitors/          # 監視モジュール
│   └── capture/           # キャプチャモジュール
├── 📁 scripts/             # スクリプト集
├── 📁 tests/               # テストファイル
└── 📄 README.md           # 概要
```

## ⚡ 自動起動設定（オプション）

### WSL起動時の自動実行

1. **~/.bashrcに追加**
   ```bash
   # Screenshot Manager auto start
   if [ ! -f "/path/to/screenshot-manager/logs/monitor.pid" ]; then
       /path/to/screenshot-manager/screenshot_manager.sh start
   fi
   ```

2. **cronを使用**
   ```bash
   crontab -e
   
   # 以下を追加
   @reboot /path/to/screenshot-manager/screenshot_manager.sh start
   ```

## 🔧 カスタマイズ

### よく変更される設定

```json
{
  "checkInterval": 2,           // 監視間隔（秒）
  "organizeByDate": true,       // 日付別フォルダ分け
  "autoCleanup": {
    "enabled": true,
    "daysToKeep": 7            // 保持日数
  },
  "maxFileSizeMB": 50          // 最大ファイルサイズ
}
```

### 監視ポートの追加

```json
{
  "additional_ports": [3333, 4444, 7000],  // 追加で監視するポート
  "exclude_ports": [8888, 9000]            // 除外するポート
}
```

## ❗ 注意事項

1. **Windowsユーザー名**: 日本語や特殊文字を含む場合は、手動で設定ファイルを編集してください
2. **権限**: WSLからWindowsファイルへのアクセス権限が必要です
3. **ディスク容量**: スクリーンショットファイルのサイズにご注意ください
4. **パフォーマンス**: 監視間隔を短くしすぎるとCPU使用率が上がります

## ✅ セットアップ完了チェックリスト

- [ ] Python 3.8以上がインストールされている
- [ ] WSL2が正常に動作している
- [ ] リポジトリがクローンされている
- [ ] `./setup.sh`が正常に完了している
- [ ] 設定ファイルが正しく生成されている
- [ ] 基本テストが成功している
- [ ] Webアプリ監視機能がインストールされている（必要な場合）
- [ ] テストスクリプトが成功している

---

次のステップ: [🎮 使用方法](USAGE.md) | [🔧 トラブルシューティング](TROUBLESHOOTING.md)