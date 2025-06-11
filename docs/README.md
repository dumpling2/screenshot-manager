# 📚 ドキュメント体系

Screenshot Manager for WSLの完全ドキュメント集です。目的に応じて適切なセクションをご覧ください。

## 🎯 目的別ガイド

### 👤 はじめて使う方
1. [📖 セットアップガイド](user/SETUP.md) - インストールから初期設定まで
2. [🎮 使用方法](user/USAGE.md) - 機能別の詳しい使い方
3. [🔧 トラブルシューティング](user/TROUBLESHOOTING.md) - 問題解決方法

### 👨‍💻 開発に参加したい方
1. [🤝 貢献ガイド](dev/CONTRIBUTING.md) - 開発参加の手順
2. [🏗️ アーキテクチャ](dev/ARCHITECTURE.md) - システム構成・技術仕様
3. [🗺️ ロードマップ](dev/ROADMAP.md) - 開発計画・今後の機能

### 🏛️ システム設計を知りたい方
1. [📐 設計書インデックス](design/README.md) - 設計書一覧
2. [🌐 Webアプリ監視設計](design/webapp-detection.md) - 自動検知システム
3. [🤖 AI連携設計](design/ai-integration.md) - 将来のAI機能

## 📁 ドキュメント構造

```
docs/
├── 📄 README.md                    # このファイル - ドキュメント体系の入口
│
├── 👤 user/                        # ユーザー向けドキュメント
│   ├── 📖 SETUP.md                 # 詳細セットアップガイド
│   ├── 🎮 USAGE.md                 # 機能別使用方法
│   └── 🔧 TROUBLESHOOTING.md       # トラブルシューティング
│
├── 👨‍💻 dev/                          # 開発者向けドキュメント
│   ├── 🗺️ ROADMAP.md               # 開発ロードマップ
│   ├── 🏗️ ARCHITECTURE.md          # システムアーキテクチャ
│   └── 🤝 CONTRIBUTING.md          # 開発貢献ガイド
│
└── 📐 design/                       # 設計書・技術仕様
    ├── 📄 README.md                # 設計書インデックス
    ├── 🌐 webapp-detection.md      # Webアプリ監視設計
    ├── 🤖 ai-integration.md        # AI連携機能設計
    ├── ⚙️ config-system.md         # 設定システム設計
    └── 📚 library-design.md        # ライブラリ化設計
```

## 🔍 カテゴリ別詳細

### 👤 ユーザー向けドキュメント (`user/`)

**対象**: エンドユーザー、システム管理者

| ドキュメント | 内容 | 読了時間 |
|-------------|------|----------|
| [SETUP.md](user/SETUP.md) | インストール、環境構築、初期設定 | 15分 |
| [USAGE.md](user/USAGE.md) | 基本・高度操作、設定カスタマイズ | 30分 |
| [TROUBLESHOOTING.md](user/TROUBLESHOOTING.md) | よくある問題、デバッグ方法 | 10分 |

**特徴**:
- 実用的な手順中心
- スクリーンショット・コマンド例豊富
- 初心者でも分かりやすい説明

### 👨‍💻 開発者向けドキュメント (`dev/`)

**対象**: 開発者、コントリビューター、アーキテクト

| ドキュメント | 内容 | 読了時間 |
|-------------|------|----------|
| [CONTRIBUTING.md](dev/CONTRIBUTING.md) | 開発参加方法、コーディング規約 | 20分 |
| [ARCHITECTURE.md](dev/ARCHITECTURE.md) | システム構成、技術仕様、設計思想 | 45分 |
| [ROADMAP.md](dev/ROADMAP.md) | 開発計画、フェーズ別機能 | 15分 |

**特徴**:
- 技術的な詳細説明
- コード例・設計図
- 拡張性・保守性重視

### 📐 設計書・技術仕様 (`design/`)

**対象**: アーキテクト、上級開発者、技術検討者

| ドキュメント | フェーズ | 状況 | 読了時間 |
|-------------|----------|------|----------|
| [webapp-detection.md](design/webapp-detection.md) | v2.0 | ✅ 実装済み | 30分 |
| [library-design.md](design/library-design.md) | v2.5 | 🔄 検討中 | 25分 |
| [config-system.md](design/config-system.md) | v4.0 | 📅 計画中 | 35分 |
| [ai-integration.md](design/ai-integration.md) | v5.0 | 📅 計画中 | 40分 |

**特徴**:
- 詳細な技術仕様
- 実装方針・制約事項
- 将来の拡張計画

## 🎓 学習パス

### 初心者コース
```
1. README.md (5分)
   ↓
2. user/SETUP.md (15分)
   ↓
3. user/USAGE.md (30分)
   ↓
4. 実際に使ってみる
   ↓
5. user/TROUBLESHOOTING.md (必要時)
```

### 開発者コース
```
1. README.md (5分)
   ↓
2. dev/ARCHITECTURE.md (45分)
   ↓
3. dev/CONTRIBUTING.md (20分)
   ↓
4. design/webapp-detection.md (30分)
   ↓
5. 実際にコードを読む・修正する
```

### アーキテクトコース
```
1. README.md (5分)
   ↓
2. dev/ARCHITECTURE.md (45分)
   ↓
3. dev/ROADMAP.md (15分)
   ↓
4. design/ 全ドキュメント (2時間)
   ↓
5. システム全体の設計検討
```

## 🔄 ドキュメント更新ポリシー

### 更新頻度
- **user/**: 機能追加・バグ修正時
- **dev/**: リリース毎、大きな設計変更時
- **design/**: 設計変更・新機能検討時

### 品質基準
- **正確性**: 実装と一致した内容
- **完全性**: 必要な情報を網羅
- **明確性**: 対象読者に適した説明レベル
- **最新性**: 最新の実装状況を反映

### 更新プロセス
```bash
# 1. ドキュメント編集
nano docs/user/USAGE.md

# 2. 関連ドキュメントの整合性確認
# 3. レビュー・承認
# 4. コミット・プッシュ
git add docs/
git commit -m "Docs: 使用方法ガイドを更新

新機能（Webアプリ監視）の使用例を追加"
```

## 🔗 外部リンク

### 公式リソース
- **GitHub Repository**: [screenshot-manager](https://github.com/your-username/screenshot-manager)
- **Issues**: [バグ報告・機能要望](https://github.com/your-username/screenshot-manager/issues)
- **Discussions**: [質問・議論](https://github.com/your-username/screenshot-manager/discussions)

### 技術資料
- **Python Watchdog**: https://python-watchdog.readthedocs.io/
- **Playwright**: https://playwright.dev/python/
- **WSL Documentation**: https://docs.microsoft.com/en-us/windows/wsl/

## 📝 ドキュメントへの貢献

### 改善提案
- 分かりにくい部分の指摘
- 使用例の追加提案
- 技術的な誤りの報告

### 翻訳・多言語化
現在は日本語のみですが、将来的に以下を検討：
- 英語版の作成
- 中国語版の作成

### 貢献方法
1. **Issue作成**: 改善点を報告
2. **Pull Request**: 直接修正を提案
3. **Discussion**: アイデア・質問の共有

---

**ドキュメントは生きています。実装の進捗とともに継続的に改善していきます。** 📖✨