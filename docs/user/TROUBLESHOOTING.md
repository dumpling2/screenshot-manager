# 🔧 トラブルシューティング

Screenshot Manager for WSLでよくある問題と解決方法をまとめています。

## 🚨 よくある問題

### 📂 スクリーンショットが検出されない

#### 症状
- Windowsでスクリーンショットを撮影しても、WSLに転送されない
- ログに「新しいファイルが見つかりません」と表示される

#### 解決方法

**1. Windowsスクリーンショットフォルダの確認**
```bash
# パスが正しいか確認
ls "/mnt/c/Users/あなたのユーザー名/Pictures/Screenshots/"

# フォルダが存在しない場合は作成
mkdir -p "/mnt/c/Users/あなたのユーザー名/Pictures/Screenshots/"
```

**2. 設定ファイルの確認**
```bash
# 設定を表示
cat config/config.json

# ユーザー名が正しいか確認
# Windowsユーザー名に日本語や特殊文字が含まれている場合は手動修正
```

**3. 権限の確認**
```bash
# Windowsフォルダへのアクセス権限確認
ls -la "/mnt/c/Users/あなたのユーザー名/Pictures/"

# 権限がない場合はWindowsで権限設定を変更
```

**4. Windowsスクリーンショット設定の確認**
- Windows設定 > システム > 記憶域 > 新しいコンテンツの保存先を確認
- スクリーンショットの保存先が想定通りか確認

### 🔄 監視が開始できない

#### 症状
- `./screenshot_manager.sh start`でエラーが発生
- 「Process already running」と表示される

#### 解決方法

**1. 既存プロセスの確認**
```bash
# 状態確認
./screenshot_manager.sh status

# 強制停止
./screenshot_manager.sh stop

# プロセス確認
ps aux | grep screenshot_monitor
```

**2. PIDファイルの削除**
```bash
# 古いPIDファイルを削除
rm -f logs/monitor.pid

# 再度開始を試行
./screenshot_manager.sh start
```

**3. ログファイル権限の確認**
```bash
# ログディレクトリの権限確認
ls -la logs/

# 権限修正
chmod 755 logs/
chmod 644 logs/*.log
```

**4. Python環境の確認**
```bash
# Python3がインストールされているか確認
python3 --version

# 必要なライブラリがインストールされているか確認
python3 -c "import watchdog; print('watchdog OK')"
```

### 📸 スクリーンショット撮影が失敗する

#### 症状
- `./take_screenshot.sh`でエラーが発生
- PowerShellエラーが表示される

#### 解決方法

**1. PowerShell権限の確認**
```bash
# PowerShellが実行できるか確認
powershell.exe -Command "Get-Date"

# エラーが発生する場合はWindows側で実行ポリシーを変更
# PowerShell (管理者として実行) で:
# Set-ExecutionPolicy RemoteSigned
```

**2. スクリプト権限の確認**
```bash
# 実行権限があるか確認
ls -la take_screenshot.sh

# 権限追加
chmod +x take_screenshot.sh
```

**3. 出力ディレクトリの確認**
```bash
# screenshotsディレクトリが存在するか確認
ls -la screenshots/

# 存在しない場合は作成
mkdir -p screenshots/
```

### 🌐 Webアプリ監視が動作しない

#### 症状
- `./webapp_monitor.py`が起動しない
- ポートが検出されない

#### 解決方法

**1. 依存関係の確認**
```bash
# 依存関係をインストール
./install_webapp_deps.sh

# または手動インストール
pip3 install -r requirements.txt

# Playwrightブラウザのインストール
python3 -m playwright install chromium
```

**2. ポート監視の確認**
```bash
# 手動でポートチェック
ss -tln | grep :3000

# プロセス確認
ps aux | grep node

# 実際にWebアプリが起動しているか確認
curl http://localhost:3000
```

**3. テスト実行**
```bash
# 統合テストを実行
./test_webapp_monitor.py

# 基本機能テスト
python3 -c "from webapp_monitor import PortMonitor; print('Import OK')"
```

### 💾 ファイルがコピーされない

#### 症状
- スクリーンショットは検出されるが、ローカルにコピーされない

#### 解決方法

**1. ディスク容量の確認**
```bash
# ディスク使用量確認
df -h

# 現在のディレクトリの容量確認
du -sh .
```

**2. 権限の確認**
```bash
# 書き込み権限があるか確認
touch screenshots/test.txt && rm screenshots/test.txt

# ディレクトリの所有者確認
ls -la screenshots/
```

**3. 転送ログの確認**
```bash
# 転送ログを確認
tail -f logs/transfers.jsonl

# エラーメッセージの確認
grep -i error logs/monitor.log
```

## 🔍 デバッグ方法

### ログレベルの変更

```bash
# デバッグモードで実行
./screenshot_manager.sh watch

# ログを詳細表示
./screenshot_manager.sh logs --tail
```

### 手動テスト

```bash
# 1. 手動でファイルコピーテスト
cp "/mnt/c/Users/あなたのユーザー名/Pictures/Screenshots/test.png" screenshots/

# 2. 監視スクリプトを直接実行
python3 screenshot_monitor.py

# 3. 設定ファイルの妥当性チェック
python3 -c "
import json
with open('config/config.json') as f:
    config = json.load(f)
    print('Config loaded successfully:', config)
"
```

### ネットワーク・プロセス確認

```bash
# 1. ポート使用状況の確認
netstat -tlnp | grep :3000

# 2. プロセス一覧
ps aux | grep -E "(node|python|webapp)"

# 3. リソース使用量
top -p $(pgrep -f webapp_monitor)
```

## ⚠️ 一般的な注意事項

### パフォーマンスの問題

**症状**: CPU使用率が高い、動作が重い

**解決方法**:
```bash
# 監視間隔を長くする
nano config/config.json
# "checkInterval": 2 → 5

# 監視ポートを減らす
nano config/webapp_config.json
# "exclude_ports": [8888, 9000, 4000]に追加
```

### メモリ不足

**症状**: プロセスが突然終了する

**解決方法**:
```bash
# メモリ使用量確認
free -h

# 不要なプロセスを停止
./screenshot_manager.sh stop
pkill -f webapp_monitor

# スワップの確認
swapon --show
```

### ファイルサイズの問題

**症状**: ディスクがすぐに満杯になる

**解決方法**:
```bash
# 自動クリーンアップを有効化
nano config/config.json
# "autoCleanup": {"enabled": true, "daysToKeep": 3}

# 手動クリーンアップ
find screenshots/ -name "*.png" -mtime +7 -delete

# 最大ファイルサイズを制限
# "maxFileSizeMB": 10
```

## 🛠️ 高度なトラブルシューティング

### ログの詳細分析

```bash
# エラーパターンの抽出
grep -E "(ERROR|FAILED|Exception)" logs/*.log

# タイムスタンプ順でログ表示
ls logs/*.log | xargs -I {} sh -c 'echo "=== {} ==="; cat {}'

# 特定時間のログ抽出
grep "2025-06-11 12:" logs/monitor.log
```

### 設定のリセット

```bash
# 設定ファイルをバックアップ
cp config/config.json config/config.json.backup

# テンプレートから再作成
cp config/config.json.template config/config.json

# 再セットアップ
./setup.sh
```

### 完全クリーンインストール

```bash
# 1. すべてのプロセスを停止
./screenshot_manager.sh stop
pkill -f webapp_monitor

# 2. ログとスクリーンショットを削除（注意！）
rm -rf logs/* screenshots/*

# 3. 設定をリセット
rm config/config.json config/webapp_config.json

# 4. 再セットアップ
./setup.sh
./install_webapp_deps.sh
```

## 📞 サポート

上記で解決しない場合は、以下の情報とともにIssueを作成してください：

### 必要な情報

```bash
# システム情報
uname -a
python3 --version
cat /etc/os-release

# 設定情報
cat config/config.json
cat config/webapp_config.json

# ログ情報
tail -50 logs/monitor.log
tail -50 logs/webapp_monitor.log

# プロセス情報
ps aux | grep -E "(screenshot|webapp)"
```

### Issue作成先
- **バグ報告**: [GitHub Issues](https://github.com/your-username/screenshot-manager/issues)
- **機能要望**: [GitHub Discussions](https://github.com/your-username/screenshot-manager/discussions)

---

前のステップ: [🎮 使用方法](USAGE.md) | [📖 セットアップガイド](SETUP.md)