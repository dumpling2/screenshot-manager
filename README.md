# Screenshot Manager

WSL上から Windows のスクリーンショットを自動的に監視・整理するツールです。

## 機能

- WSLからWindowsのスクリーンショットフォルダを直接監視
- 新しいスクリーンショットを自動的にWSL内にコピー
- 日付ごとにフォルダ分けして整理
- 重複ファイルの自動検出とスキップ
- 古いファイルの自動クリーンアップ
- 転送ログの記録
- 統合管理スクリプトによる簡単な操作

## プロジェクト構造

```
screenshot-manager/
├── screenshot_monitor.py   # メイン監視スクリプト
├── screenshot_manager.sh   # 統合管理スクリプト
├── setup.sh               # 初回セットアップスクリプト
├── config/                # 設定ファイル
│   └── config.json.template
├── screenshots/           # スクリーンショット保存先（自動生成）
├── logs/                  # ログファイル（自動生成）
├── .gitignore            # Git除外設定
└── README.md
```

## セットアップ

### 1. リポジトリのクローン

```bash
git clone https://github.com/your-username/screenshot-manager.git
cd screenshot-manager
```

### 2. 初回セットアップの実行

```bash
# セットアップスクリプトを実行
./screenshot_manager.sh setup

# または直接セットアップスクリプトを実行
./setup.sh
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

## 使用方法

### 基本的なコマンド

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

## MCP（Model Context Protocol）サーバーとしての使用

### MCPサーバーのインストール

```bash
# MCP環境の自動セットアップ
./install_mcp.sh
```

### 手動設定

1. MCPライブラリのインストール：
   ```bash
   pip3 install mcp
   ```

2. Claude Desktop設定ファイル（`~/.config/claude/claude_desktop_config.json`）に追加：
   ```json
   {
     "mcpServers": {
       "screenshot-manager": {
         "command": "python3",
         "args": ["/path/to/screenshot-manager/mcp_screenshot_server.py"],
         "env": {}
       }
     }
   }
   ```

3. Claude Desktopを再起動

### MCPツールの使用

Claude Desktop内で自然言語でスクリーンショット機能を操作できます：

```
# 使用例
「モニター一覧を表示して」
「Chromeのスクリーンショットを撮影して」
「モニター1のスクリーンショットを保存して」
「スクリーンショット監視を開始して」
```

### 利用可能なMCPツール

- `list_monitors`: 利用可能なモニター一覧表示
- `list_windows`: 実行中のウィンドウ一覧表示
- `take_screenshot`: 全画面スクリーンショット撮影
- `take_monitor_screenshot`: 指定モニターのスクリーンショット撮影
- `take_process_screenshot`: 指定プロセスのスクリーンショット撮影
- `take_window_screenshot`: 指定ウィンドウのスクリーンショット撮影
- `monitor_status`: 監視状態確認
- `start_monitor`: 監視開始
- `stop_monitor`: 監視停止

## 必要な環境

- Windows 10/11 with WSL2
- Python 3.6以上
- bash
- MCP対応クライアント（Claude Desktop等）（オプション）

## ライセンス

MIT License