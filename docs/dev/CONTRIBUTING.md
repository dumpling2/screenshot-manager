# 🤝 開発貢献ガイド

Screenshot Manager for WSLの開発に参加していただき、ありがとうございます！

## 🚀 はじめに

### プロジェクトのミッション
Claude Codeでの開発体験を向上させる、WSL専用のスクリーンショット・動作確認ツールの開発

### 開発方針
- **ユーザーフレンドリー**: セットアップが簡単で、直感的な操作
- **高パフォーマンス**: 軽量で高速な動作
- **拡張性**: 新機能の追加が容易な設計
- **品質重視**: テストとドキュメントの充実

## 📋 開発環境のセットアップ

### 必要な環境

```bash
# 基本環境
- Windows 10/11 + WSL2
- Python 3.8+
- Git
- エディタ (VS Code推奨)

# 開発用ツール
- pytest (テスト実行)
- black (コードフォーマット)
- flake8 (静的解析)
```

### セットアップ手順

```bash
# 1. リポジトリをフォーク・クローン
git clone https://github.com/your-username/screenshot-manager.git
cd screenshot-manager

# 2. 開発環境セットアップ
./setup.sh
./install_webapp_deps.sh

# 3. 開発用ツールのインストール
pip3 install pytest black flake8

# 4. 動作確認
./test_webapp_monitor.py
```

## 🌟 貢献方法

### 1. Issue・Discussion

**バグ報告**
- 再現手順の詳細
- 環境情報（OS, Python版等）
- ログファイルの内容

**機能要望**
- 具体的な使用場面
- 期待する動作
- 技術的な制約の考慮

### 2. Pull Request

**ブランチ戦略**
```bash
main                    # 安定版ブランチ
├── feature/webapp-v2   # 新機能開発
├── fix/port-detection  # バグ修正
└── docs/architecture   # ドキュメント更新
```

**PR作成手順**
```bash
# 1. フィーチャーブランチ作成
git checkout -b feature/your-feature-name

# 2. 開発・テスト
# ... your changes ...
./test_webapp_monitor.py

# 3. コミット
git add .
git commit -m "Add: 新機能の説明

詳細な変更内容の説明"

# 4. Push・PR作成
git push origin feature/your-feature-name
```

## 📝 コーディング規約

### Python コードスタイル

**フォーマット**
```bash
# Black を使用
black *.py

# flake8 でチェック
flake8 *.py --max-line-length=88
```

**ネーミング規約**
```python
# クラス: PascalCase
class WebAppMonitor:
    pass

# 関数・変数: snake_case
def capture_screenshot():
    app_info = get_app_info()

# 定数: UPPER_SNAKE_CASE
DEFAULT_PORTS = [3000, 5000, 5173]

# プライベート: _から始める
def _internal_function():
    pass
```

**ドキュメンテーション**
```python
def capture_webapp_screenshots(app_info: AppInfo, output_dir: Path = None):
    """Webアプリのスクリーンショットを撮影
    
    Args:
        app_info: 検出されたWebアプリ情報
        output_dir: 出力ディレクトリ（Noneの場合は自動生成）
        
    Returns:
        Path: 生成されたスクリーンショットディレクトリ
        
    Raises:
        ConnectionError: Webアプリにアクセスできない場合
    """
```

### Bash スクリプトスタイル

```bash
#!/bin/bash

# 関数は snake_case
check_dependencies() {
    local dep="$1"
    command -v "$dep" >/dev/null 2>&1
}

# 変数は UPPER_CASE (グローバル) または lower_case (ローカル)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
```

## 🧪 テスト指針

### テストの種類

**1. 単体テスト**
```python
def test_port_monitor_initialization():
    monitor = PortMonitor()
    assert len(monitor.ports) > 0
    assert 3000 in monitor.ports
```

**2. 統合テスト**
```python
def test_webapp_detection_flow():
    server = start_test_server(3000)
    monitor = WebAppMonitor()
    
    # 検知テスト
    apps = monitor.detect_new_apps()
    assert len(apps) == 1
    assert apps[0].port == 3000
```

**3. エンドツーエンドテスト**
```bash
# test_e2e.sh
./webapp_monitor.py &
MONITOR_PID=$!

# テストWebアプリを起動
python3 -m http.server 3000 &
SERVER_PID=$!

# 検知を待機
sleep 5

# スクリーンショットが生成されたか確認
ls screenshots/webapp_3000_* || exit 1

# クリーンアップ
kill $MONITOR_PID $SERVER_PID
```

### テスト実行

```bash
# 統合テスト
./test_webapp_monitor.py

# 特定テスト実行
python3 -m pytest tests/test_port_monitor.py -v

# カバレッジ確認
python3 -m pytest --cov=webapp_monitor tests/
```

## 📁 プロジェクト構造

### ディレクトリ構成

```
screenshot-manager/
├── 🔧 Core Implementation/
│   ├── screenshot_monitor.py      # v1.0: ファイル監視
│   ├── webapp_monitor.py          # v2.0: Webアプリ監視  
│   ├── playwright_capture.py      # ブラウザ自動化
│   └── screenshot_manager.sh      # 統合管理
├── ⚙️ Configuration/
│   ├── config/
│   │   ├── *.json.template       # 設定テンプレート
│   │   └── *.json                # 実際の設定
├── 🧪 Testing/
│   ├── test_webapp_monitor.py     # メインテストスイート
│   └── tests/                     # 個別テストファイル
├── 📚 Documentation/
│   ├── docs/user/                 # ユーザー向け
│   ├── docs/dev/                  # 開発者向け
│   └── docs/design/               # 設計書
├── 🔧 Utilities/
│   ├── setup.sh                   # 基本セットアップ
│   ├── install_webapp_deps.sh     # 依存関係インストール
│   └── take_screenshot.sh         # 高度撮影機能
└── 📦 Distribution/
    ├── requirements.txt           # Python依存関係
    └── LICENSE                    # ライセンス
```

### ファイル命名規約

- **Python**: `snake_case.py`
- **Bash**: `kebab-case.sh`
- **設定**: `config_name.json`
- **テスト**: `test_module_name.py`
- **ドキュメント**: `TITLE.md`

## 🔄 開発フロー

### Git ワークフロー

```bash
# 1. 最新のmainブランチを取得
git checkout main
git pull upstream main

# 2. フィーチャーブランチ作成
git checkout -b feature/add-error-detection

# 3. 開発・テスト
# ... 実装 ...
./test_webapp_monitor.py

# 4. コミット
git add .
git commit -m "Add: エラー要素の自動検出機能

- CSSセレクタによるエラー要素検出
- エラー発見時の専用スクリーンショット
- エラー情報のJSON出力機能"

# 5. Push・PR
git push origin feature/add-error-detection
```

### コミットメッセージ規約

**プレフィックス**
- `Add:` 新機能追加
- `Fix:` バグ修正
- `Update:` 既存機能の改善
- `Docs:` ドキュメント更新
- `Refactor:` リファクタリング
- `Test:` テスト追加・修正

**例**
```
Add: Webアプリフレームワーク自動検出機能

- HTML解析によるReact/Vue/Angular判定
- HTTPヘッダーからExpress/Flask/Django検出
- 未知のフレームワークのフォールバック処理

Fixes #123
```

## 🎯 開発優先事項

### Phase 2 (v3.0) 開発項目

**高優先度**
- [ ] Claude Code連携API開発
- [ ] コード変更検知システム
- [ ] ビジュアルリグレッションテスト

**中優先度**
- [ ] 設定UI（Web界面）
- [ ] プラグインシステム
- [ ] パフォーマンス最適化

**低優先度**
- [ ] クラウドストレージ連携
- [ ] AI画像解析
- [ ] RESTful API

### 新規貢献者向けタスク

**Good First Issue**
- [ ] ドキュメントの改善
- [ ] テストケースの追加
- [ ] エラーメッセージの多言語化
- [ ] 設定オプションの追加

**Help Wanted**
- [ ] macOS対応
- [ ] Docker化
- [ ] VS Code拡張機能
- [ ] GitHub Actions CI/CD

## 🔍 コードレビュー指針

### レビュー観点

**機能性**
- [ ] 要件を満たしているか
- [ ] エラーハンドリングは適切か
- [ ] パフォーマンスに問題はないか

**保守性**
- [ ] コードは読みやすいか
- [ ] 適切にモジュール化されているか
- [ ] ドキュメントは充実しているか

**品質**
- [ ] テストは十分か
- [ ] セキュリティ問題はないか
- [ ] 既存機能に影響はないか

### レビューコメント例

```
# 良い例
LGTM! ポート検知ロジックが明確で、エラーハンドリングも適切です。

# 改善提案
この部分をasync/awaitにすることで、パフォーマンスが向上する可能性があります。

# 質問
この設定項目は、どのような場面で使用することを想定していますか？
```

## 📊 品質基準

### 最低基準

- [ ] 全テストがパス
- [ ] flake8チェックをパス
- [ ] 新機能にはテストを追加
- [ ] 破壊的変更は明記

### 推奨基準

- [ ] カバレッジ80%以上
- [ ] ドキュメント更新
- [ ] パフォーマンステスト
- [ ] 使用例の提供

## 🎉 リリースプロセス

### バージョン管理

**セマンティックバージョニング**
- `MAJOR.MINOR.PATCH`
- 例: `v2.1.3`

**タグ付け**
```bash
git tag -a v2.1.0 -m "Release v2.1.0: Webアプリ自動検知機能追加"
git push origin v2.1.0
```

### リリースノート

```markdown
## v2.1.0 - 2025-06-11

### ✨ 新機能
- Webアプリケーション自動検知機能
- Playwrightによる高度スクリーンショット撮影
- レスポンシブデザインテスト

### 🐛 バグ修正
- ポート監視での文字化け問題を修正
- メモリリーク問題を解決

### ⚠️ 破壊的変更
- `config.json`の形式を変更（自動マイグレーション対応）
```

## 🤝 コミュニティ

### 連絡手段

- **GitHub Issues**: バグ報告・機能要望
- **GitHub Discussions**: 一般的な議論
- **Pull Requests**: コード貢献

### 行動規範

1. **尊重**: 多様な意見・バックグラウンドを尊重
2. **建設的**: 批判は具体的で建設的に
3. **協力**: チーム全体の成功を重視
4. **学習**: 新しいことを学ぶ姿勢を持つ

## 🎓 学習リソース

### 技術スタック

**Python**
- [Python公式ドキュメント](https://docs.python.org/)
- [Watchdog ライブラリ](https://python-watchdog.readthedocs.io/)

**Playwright**
- [Playwright for Python](https://playwright.dev/python/)
- [Async/Await パターン](https://docs.python.org/3/library/asyncio.html)

**WSL**
- [WSL公式ドキュメント](https://docs.microsoft.com/en-us/windows/wsl/)
- [Linux-Windowsファイルシステム連携](https://docs.microsoft.com/en-us/windows/wsl/filesystems)

### プロジェクト固有

- [📖 セットアップガイド](../user/SETUP.md)
- [🎮 使用方法](../user/USAGE.md)
- [🏗️ アーキテクチャ](ARCHITECTURE.md)
- [🗺️ ロードマップ](ROADMAP.md)

---

**開発に参加していただき、ありがとうございます！質問がある場合は、お気軽にIssueまたはDiscussionで連絡ください。** 🚀