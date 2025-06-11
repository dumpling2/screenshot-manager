#!/bin/bash

# Webアプリ監視機能の依存関係をインストール

echo "🔧 Webアプリ監視機能の依存関係をインストールします..."

# Python依存関係のインストール
echo "📦 Python依存関係のインストール..."
pip3 install -r requirements.txt

# Playwrightのブラウザをインストール
echo "🌐 Playwrightブラウザのインストール..."
if python3 -c "import playwright" 2>/dev/null; then
    echo "Playwrightが見つかりました。ブラウザをインストールします..."
    python3 -m playwright install chromium
    
    # 必要なシステム依存関係をインストール
    echo "📚 システム依存関係のインストール..."
    python3 -m playwright install-deps chromium
    
    echo "✅ Playwrightのセットアップが完了しました"
else
    echo "❌ Playwrightのインストールに失敗しました"
    echo "手動でインストールしてください: pip3 install playwright"
    exit 1
fi

# 設定ファイルの準備
echo "⚙️ 設定ファイルの準備..."
if [ ! -f "config/webapp_config.json" ]; then
    echo "webapp_config.json を作成しています..."
    cp config/webapp_config.json.template config/webapp_config.json
    echo "✅ webapp_config.json を作成しました"
else
    echo "webapp_config.json は既に存在します"
fi

# 実行権限の設定
chmod +x webapp_monitor.py
chmod +x playwright_capture.py

echo ""
echo "🎉 Webアプリ監視機能のセットアップが完了しました!"
echo ""
echo "使用方法:"
echo "  基本監視:     ./webapp_monitor.py"
echo "  設定編集:     nano config/webapp_config.json"
echo "  ログ確認:     tail -f logs/webapp_monitor.log"
echo ""
echo "監視対象ポート: 3000, 3001, 5000, 5173, 5174, 8000, 8080, 4200, 4000, 8888, 9000"
echo ""