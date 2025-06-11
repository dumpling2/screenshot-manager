# Screenshot Manager - 開発ロードマップ

## プロジェクト概要
Claude Codeで作成したWebアプリケーションの起動後画面を自動的にキャプチャし、動作確認を支援するツール。

## 現状（v1.0 - 基本機能完成）
- ✅ スクリーンショット自動監視・整理
- ✅ 高度なスクリーンショット撮影（モニター指定、ウィンドウ指定）
- ✅ 日付別整理、重複検出、自動クリーンアップ
- ✅ WSL-Windows連携

## Phase 1: Webアプリ自動監視機能（v2.0） - 優先度：高
**目標**: Claude Codeで作成したWebアプリの起動を検知し、自動的にスクリーンショットを撮影

### 機能追加
- [ ] **Webアプリ起動検知**
  - ポート監視（3000, 5000, 5173, 8000, 8080等）
  - プロセス監視（node, python, ruby等）
  - ログファイル監視
- [ ] **ブラウザ自動化**
  - Selenium/Playwright統合
  - 自動的にlocalhost:portにアクセス
  - ページロード完了待機
- [ ] **スマートキャプチャ**
  - 初回起動時の全画面キャプチャ
  - エラー画面の自動検出
  - 主要ページの巡回キャプチャ

### 利用例
```python
# Webアプリ監視開始
from screenshot_lib import WebAppMonitor

monitor = WebAppMonitor()
monitor.watch_ports([3000, 5000, 5173, 8000])  # 一般的なWebアプリポート
monitor.on_app_detected(lambda app_info: {
    'url': app_info.url,
    'screenshots': monitor.capture_app_screens(app_info)
})
```

### 想定ワークフロー
```bash
# 1. Claude Codeでアプリ作成
claude> "Reactでシンプルなタスク管理アプリを作って"

# 2. Screenshot Managerが自動検知
[INFO] Detected new web app on port 3000
[INFO] Opening browser: http://localhost:3000
[INFO] Capturing initial screen...
[INFO] Screenshots saved: ./screenshots/webapp_20250611_123456/

# 3. 開発者は画面を確認
```

## Phase 2: 開発ワークフロー統合（v3.0） - 優先度：高
**目標**: Claude Codeとの連携を強化し、開発効率を向上

### 機能追加
- [ ] **Claude Code連携**
  - プロジェクト作成時の自動設定
  - コード変更検知→再起動→スクリーンショット
  - エラー発生時の自動キャプチャ
- [ ] **テスト自動化**
  - 複数ブラウザでの動作確認
  - レスポンシブデザインテスト（複数解像度）
  - ビジュアルリグレッションテスト
- [ ] **レポート生成**
  - 動作確認レポート（HTML/PDF）
  - スクリーンショットギャラリー
  - エラー画面の自動分類

### 統合例
```yaml
# .screenshot-manager.yaml (プロジェクトルート)
webapp:
  watch_command: "npm run dev"
  port: 3000
  capture_on:
    - startup
    - code_change
    - error
  pages_to_test:
    - "/"
    - "/about"
    - "/dashboard"
  browsers:
    - chrome
    - firefox
  resolutions:
    - [1920, 1080]
    - [768, 1024]  # iPad
    - [375, 667]   # iPhone
```

## Phase 3: CI/CD統合（v4.0） - 優先度：中
**目標**: 継続的な品質保証を実現

### 機能追加
- [ ] **GitHub Actions統合**
  - PR作成時の自動スクリーンショット
  - 変更前後の比較
  - レビュー用のコメント自動投稿
- [ ] **Docker対応**
  - ヘッドレスブラウザ環境
  - 再現可能なテスト環境
- [ ] **自動デプロイ後確認**
  - ステージング環境のキャプチャ
  - 本番環境との差分検出

### CI/CD例
```yaml
# .github/workflows/screenshot-test.yml
name: Visual Testing
on: [push, pull_request]
jobs:
  screenshot:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Start app and capture
        run: |
          ./screenshot_manager.sh ci-test
      - name: Upload screenshots
        uses: actions/upload-artifact@v2
        with:
          name: screenshots
          path: ./screenshots/
```

## Phase 4: AI分析・フィードバック機能（v5.0） - 優先度：低
**目標**: スクリーンショットからの自動フィードバック生成

### 機能追加
- [ ] **UI/UX分析**
  - デザインの一貫性チェック
  - アクセシビリティ検証
  - ユーザビリティ問題の指摘
- [ ] **エラー診断**
  - エラー画面の自動分類
  - 修正提案の生成
  - 類似問題の検索
- [ ] **開発提案**
  - 改善点の自動提案
  - ベストプラクティスとの比較

## 技術的検討事項

### Webアプリ検知の実装方針
1. **ポート監視**: `netstat`や`ss`コマンドでリスニングポートを定期チェック
2. **プロセス監視**: 開発サーバープロセス（webpack-dev-server等）の検出
3. **ファイル監視**: package.json、webpack.config.js等の存在確認

### ブラウザ自動化の選択
- **Selenium**: 安定性重視、多ブラウザ対応
- **Playwright**: モダン、高速、デバッグ機能充実
- **Puppeteer**: Chrome特化、軽量

### スクリーンショット戦略
1. **初回起動**: フルページキャプチャ
2. **変更検知**: 差分のある部分のみ
3. **エラー時**: コンソールログも含めて保存

## 開発スケジュール目安
- **Phase 1**: 1-2週間（最優先）
- **Phase 2**: 2-3週間  
- **Phase 3**: 2-3週間
- **Phase 4**: 3-4週間

## 次のアクション
1. Webアプリ起動検知機能の実装
2. ブラウザ自動化ライブラリの選定
3. Claude Codeとの連携仕様策定
4. プロトタイプ作成とテスト

---
*最終更新: 2025-06-11*