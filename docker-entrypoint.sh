#!/bin/bash
set -e

echo "🚀 Screenshot Manager Docker Container Starting..."

# 環境変数のデフォルト設定
export DISPLAY=${DISPLAY:-:99}
export LOG_LEVEL=${LOG_LEVEL:-INFO}
export PORT=${PORT:-8080}

# ディレクトリの存在確認・作成
mkdir -p logs screenshots config

# 設定ファイルの初期化
if [ ! -f config/config.json ]; then
    echo "📄 設定ファイルを初期化しています..."
    cp config/config.json.template config/config.json
fi

if [ ! -f config/webapp_config.json ]; then
    cp config/webapp_config.json.template config/webapp_config.json
fi

# Xvfbを開始 (ヘッドレス環境用)
if [ "$ENV" = "production" ]; then
    echo "🖥️ 仮想ディスプレイを開始しています..."
    Xvfb :99 -screen 0 1920x1080x24 > /dev/null 2>&1 &
    XVFB_PID=$!
    echo "Xvfb PID: $XVFB_PID"
fi

# ヘルスチェックエンドポイント用の簡易サーバー準備
if [ "$1" = "health-check" ]; then
    python -c "
import http.server
import socketserver
import json
from datetime import datetime

class HealthHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            health_data = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'version': '3.0.0'
            }
            self.wfile.write(json.dumps(health_data).encode())
        else:
            self.send_response(404)
            self.end_headers()

with socketserver.TCPServer(('', 8080), HealthHandler) as httpd:
    print('Health check server running on port 8080')
    httpd.serve_forever()
"
    exit 0
fi

# メイン処理の分岐
case "$1" in
    "screenshot-monitor")
        echo "📸 スクリーンショット監視サーバーを開始..."
        exec python src/monitors/webapp_monitor.py
        ;;
    "mcp-server")
        echo "🔗 MCPサーバーを開始..."
        exec python src/integrations/mcp_server.py
        ;;
    "http-server")
        echo "🌐 HTTPサーバーを開始..."
        exec python src/integrations/mcp_http_server.py
        ;;
    "test")
        echo "🧪 テストを実行..."
        exec python -m pytest tests/ -v
        ;;
    "integration-test")
        echo "🔧 統合テストを実行..."
        exec python test_phase24_integration.py
        ;;
    "shell")
        echo "🐚 デバッグシェルを開始..."
        exec /bin/bash
        ;;
    *)
        echo "🚀 デフォルト: HTTP APIサーバーを開始..."
        exec "$@"
        ;;
esac

# クリーンアップ処理
cleanup() {
    echo "🛑 コンテナをシャットダウンしています..."
    if [ ! -z "$XVFB_PID" ]; then
        kill $XVFB_PID 2>/dev/null || true
    fi
}

trap cleanup EXIT SIGTERM SIGINT