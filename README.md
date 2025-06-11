# Screenshot Manager for WSL

Claude Codeで作成したWebアプリケーションの起動後画面を自動的にキャプチャし、動作確認を支援するツールです。Windows上でスクリーンショットを撮影し、WSL環境のプロジェクトフォルダに自動的に保存・整理します。

## 🎯 主要機能

### 📁 現在の機能（v1.0）
- **自動監視**: Windowsのスクリーンショットフォルダを監視し、新しい画像を自動的に検出
- **自動整理**: 日付別フォルダに自動的に整理
- **重複検出**: MD5ハッシュによる重複ファイルの自動検出と削除
- **自動クリーンアップ**: 指定日数経過後の古いスクリーンショットを自動削除
- **転送ログ**: すべての転送操作をJSON形式で記録
- **高度な撮影機能**: 特定のモニターやウィンドウのスクリーンショット撮影

### 🚀 開発中の機能（v2.0）
- **Webアプリ自動検知**: Claude Codeで作成したアプリの起動を自動検出
- **ブラウザ自動化**: 起動したWebアプリを自動的に開いてキャプチャ
- **レスポンシブテスト**: 複数の画面サイズで自動スクリーンショット
- **動作確認レポート**: スクリーンショットギャラリーとエラー検出

## 📋 使用シナリオ

### 現在の使い方
```bash
# Claude Codeでアプリを作成
claude> "Reactでタスク管理アプリを作って"

# 手動でスクリーンショット撮影
./take_screenshot.sh

# 自動的に整理・保存される
```

### 将来の使い方（v2.0）
```bash
# Claude Codeでアプリを作成
claude> "Reactでタスク管理アプリを作って"

# 自動的に以下が実行される：
# 1. Webアプリの起動検知（port 3000）
# 2. ブラウザで自動的に開く
# 3. 複数解像度でスクリーンショット
# 4. レポート生成
```

## プロジェクト構造

```
screenshot-manager/
├── screenshot_monitor.py       # メイン監視スクリプト
├── screenshot_manager.sh       # 統合管理スクリプト
├── take_screenshot.sh          # 高度なスクリーンショット撮影
├── setup.sh                   # 初回セットアップスクリプト
├── requirements.txt           # Python依存関係
├── config/                    # 設定ファイル
│   ├── config.json.template   # 設定テンプレート
│   └── config.json           # 実際の設定（自動生成）
├── screenshots/              # スクリーンショット保存先（自動生成）
├── logs/                     # ログファイル（自動生成）
├── .gitignore               # Git除外設定
├── CLAUDE.md                # プロジェクト固有ルール
├── ROADMAP.md               # 開発ロードマップ
├── WEBAPP_DETECTION.md      # Webアプリ検知機能設計
└── README.md
```

## 📦 セットアップ

### 基本セットアップ

```bash
# 1. リポジトリのクローン
git clone https://github.com/your-username/screenshot-manager.git
cd screenshot-manager

# 2. 基本機能のセットアップ
./setup.sh

# 3. 監視開始
./screenshot_manager.sh start
```

セットアップスクリプトでは以下の設定を行います：
- Windowsのユーザー名の入力
- スクリーンショットフォルダの確認
- 設定ファイルの自動生成
- 必要なディレクトリの作成
- 実行権限の設定

### 3. 設定内容の確認（オプション）

生成された設定ファイルを確認・編集する場合：

```bash
./screenshot_manager.sh config
```

## 📖 使用方法

### 基本的な監視コマンド

```bash
# 監視を開始（バックグラウンド）
./screenshot_manager.sh start

# 監視を停止
./screenshot_manager.sh stop

# 監視を再起動
./screenshot_manager.sh restart

# 状態を確認
./screenshot_manager.sh status

# ログを表示
./screenshot_manager.sh logs

# リアルタイムでログを監視
./screenshot_manager.sh logs --tail

# デバッグモード（フォアグラウンドで実行）
./screenshot_manager.sh watch

# 設定ファイルを編集
./screenshot_manager.sh config

# ヘルプを表示
./screenshot_manager.sh help
```

### 高度なスクリーンショット機能

```bash
# モニター一覧表示
./take_screenshot.sh --list-monitors

# ウィンドウ一覧表示
./take_screenshot.sh --list-windows

# 全画面スクリーンショット
./take_screenshot.sh

# 指定モニターのスクリーンショット
./take_screenshot.sh --monitor 0
./take_screenshot.sh --monitor 1 monitor1.png

# プロセス指定スクリーンショット
./take_screenshot.sh --process Chrome
./take_screenshot.sh --process Code vscode.png

# ウィンドウハンドル指定
./take_screenshot.sh --window 67938
```

### 自動起動の設定

WSLの起動時に自動的に監視を開始する場合：

1. `~/.bashrc`または`~/.zshrc`に以下を追加：
   ```bash
   # Screenshot Manager auto start
   if [ ! -f "/home/mikanu/便利アプリ/screenshot manager/logs/monitor.pid" ]; then
       /home/mikanu/便利アプリ/screenshot\ manager/screenshot_manager.sh start
   fi
   ```

2. または、cronを使用：
   ```bash
   crontab -e
   ```
   
   以下を追加：
   ```
   @reboot /home/mikanu/便利アプリ/screenshot\ manager/screenshot_manager.sh start
   ```

## 設定オプション

### config.json の詳細

- `windowsUsername`: Windowsのユーザー名
- `windowsScreenshotPath`: Windowsのスクリーンショット保存先（{username}は自動置換）
- `localScreenshotPath`: WSL内の保存先（相対パス）
- `checkInterval`: 監視間隔（秒）
- `filePattern`: 監視するファイルパターン（配列）
- `organizeByDate`: 日付別フォルダ分けの有効/無効
- `dateFormat`: 日付フォルダの形式（Python strftime形式）
- `maxFileSizeMB`: 最大ファイルサイズ（MB）
- `autoCleanup`: 自動クリーンアップ設定
  - `enabled`: 有効/無効
  - `daysToKeep`: 保持する日数

## トラブルシューティング

### スクリーンショットが検出されない

1. Windowsのスクリーンショットフォルダパスを確認：
   ```bash
   ls /mnt/c/Users/あなたのユーザー名/Pictures/Screenshots/
   ```

2. 設定ファイルのパスが正しいか確認：
   ```bash
   ./screenshot_manager.sh config
   ```

3. ログを確認：
   ```bash
   ./screenshot_manager.sh logs --tail
   ```

### 監視が開始できない

1. 既に実行中でないか確認：
   ```bash
   ./screenshot_manager.sh status
   ```

2. ログファイルの権限を確認：
   ```bash
   ls -la logs/
   ```

3. Python3がインストールされているか確認：
   ```bash
   python3 --version
   ```

### ファイルがコピーされない

1. Windowsフォルダへのアクセス権限を確認
2. ディスク容量を確認
3. 転送ログを確認：
   ```bash
   tail -f logs/transfers.jsonl
   ```

## 動作の仕組み

1. WSLから`/mnt/c`経由でWindowsのファイルシステムにアクセス
2. 指定されたスクリーンショットフォルダを定期的に監視
3. 新しいファイルを検出したら、WSL内のプロジェクトフォルダにコピー
4. ファイルは日付ごとのフォルダに自動整理
5. 重複ファイルはMD5ハッシュで検出してスキップ
6. 指定日数を経過した古いファイルは自動削除

## 🔧 必要な環境

### 基本要件
- Windows 10/11 with WSL2
- Python 3.8以上
- bash
- PowerShell（スクリーンショット撮影用）

### 将来の要件（v2.0）
- Node.js（Webアプリ検知用）
- Playwright/Selenium（ブラウザ自動化用）

## 📝 依存関係

```bash
# 必要なPythonライブラリ
pip3 install -r requirements.txt
```

### requirements.txt内容
- `watchdog>=3.0.0` - ファイル監視用

### 将来の依存関係（v2.0）
- `playwright` - ブラウザ自動化
- `requests` - HTTP監視
- `pyyaml` - 設定ファイル

## 今後の開発計画

詳細は[ROADMAP.md](ROADMAP.md)を参照してください。

### Phase 1: Webアプリ自動監視機能（開発中）
- ポート監視によるWebアプリ起動検知
- ブラウザ自動化によるスクリーンショット
- レスポンシブデザインテスト

### Phase 2: 開発ワークフロー統合
- Claude Codeとの連携強化
- コード変更時の自動再キャプチャ
- ビジュアルリグレッションテスト

## ライセンス

MIT License