#!/bin/bash

# Screenshot Manager MCP サーバーのインストールスクリプト

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_CONFIG_FILE="$HOME/.config/claude/claude_desktop_config.json"

echo "Screenshot Manager MCP サーバーのインストール"
echo "================================================"

# MCPライブラリのインストール
echo "1. MCPライブラリをインストール中..."
if command -v pip3 &> /dev/null; then
    pip3 install mcp
else
    echo "エラー: pip3が見つかりません。Pythonがインストールされているか確認してください。"
    exit 1
fi

# Claude Desktop設定ディレクトリの作成
echo "2. Claude Desktop設定ディレクトリを作成中..."
mkdir -p "$(dirname "$MCP_CONFIG_FILE")"

# 既存の設定ファイルをバックアップ
if [ -f "$MCP_CONFIG_FILE" ]; then
    echo "3. 既存の設定ファイルをバックアップ中..."
    cp "$MCP_CONFIG_FILE" "${MCP_CONFIG_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
fi

# 設定ファイルの作成または更新
echo "4. MCP設定を追加中..."

# 新しい設定の作成
cat > "$MCP_CONFIG_FILE" << EOF
{
  "mcpServers": {
    "screenshot-manager": {
      "command": "python3",
      "args": ["$SCRIPT_DIR/mcp_screenshot_server.py"],
      "env": {}
    }
  }
}
EOF

echo "✓ MCP設定ファイルを作成しました: $MCP_CONFIG_FILE"

# 実行権限の確認
echo "5. 実行権限を確認中..."
chmod +x "$SCRIPT_DIR/mcp_screenshot_server.py"
chmod +x "$SCRIPT_DIR/take_screenshot.sh"
chmod +x "$SCRIPT_DIR/screenshot_manager.sh"

echo ""
echo "インストール完了！"
echo "==================="
echo ""
echo "使用方法:"
echo "1. Claude Desktopを再起動してください"
echo "2. 以下のような自然言語でスクリーンショットを操作できます："
echo "   - 「モニター一覧を表示して」"
echo "   - 「Chromeのスクリーンショットを撮って」"
echo "   - 「モニター1のスクリーンショットを撮影して」"
echo "   - 「監視を開始して」"
echo ""
echo "利用可能なツール:"
echo "- list_monitors: モニター一覧表示"
echo "- list_windows: ウィンドウ一覧表示"
echo "- take_screenshot: 全画面スクリーンショット"
echo "- take_monitor_screenshot: 指定モニターのスクリーンショット"
echo "- take_process_screenshot: 指定プロセスのスクリーンショット"
echo "- take_window_screenshot: 指定ウィンドウのスクリーンショット"
echo "- monitor_status: 監視状態確認"
echo "- start_monitor: 監視開始"
echo "- stop_monitor: 監視停止"