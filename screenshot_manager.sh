#!/bin/bash

# Screenshot Manager - 統合管理スクリプト
# WSL上からスクリーンショットの監視と管理を行います

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONITOR_SCRIPT="$SCRIPT_DIR/screenshot_monitor.py"
PID_FILE="$SCRIPT_DIR/logs/monitor.pid"
LOG_FILE="$SCRIPT_DIR/logs/manager.log"

# ログディレクトリの作成
mkdir -p "$SCRIPT_DIR/logs"

# ログ出力関数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# ヘルプ表示
show_help() {
    echo "Screenshot Manager - WSL上でWindowsのスクリーンショットを管理"
    echo ""
    echo "使用方法: $0 [コマンド] [オプション]"
    echo ""
    echo "コマンド:"
    echo "  setup       - 初回セットアップを実行"
    echo "  start       - バックグラウンドで監視を開始"
    echo "  stop        - 監視を停止"
    echo "  restart     - 監視を再起動"
    echo "  status      - 監視の状態を確認"
    echo "  watch       - フォアグラウンドで監視を実行（デバッグ用）"
    echo "  organize    - スクリーンショットを手動で整理"
    echo "  cleanup     - 古いファイルを削除"
    echo "  config      - 設定ファイルを編集"
    echo "  logs        - ログを表示"
    echo "  screenshot  - WSLからスクリーンショットを撮影"
    echo "  help        - このヘルプを表示"
    echo ""
    echo "オプション:"
    echo "  --tail      - ログ表示時に最新のログを追跡"
    echo "  --lines N   - ログ表示時の行数を指定（デフォルト: 50）"
}

# プロセスが実行中か確認
is_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$PID_FILE"
        fi
    fi
    return 1
}

# 監視を開始
start_monitor() {
    # 設定ファイルの存在確認
    if [ ! -f "$SCRIPT_DIR/config/config.json" ]; then
        echo "エラー: 設定ファイルが見つかりません。"
        echo "初回セットアップを実行してください："
        echo "  ./screenshot_manager.sh setup"
        return 1
    fi
    
    if is_running; then
        log "監視は既に実行中です (PID: $(cat "$PID_FILE"))"
        return 1
    fi
    
    log "スクリーンショット監視を開始します..."
    
    # Python仮想環境がある場合はアクティベート
    if [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
        source "$SCRIPT_DIR/venv/bin/activate"
    fi
    
    # バックグラウンドで実行
    nohup python3 "$MONITOR_SCRIPT" > "$LOG_FILE" 2>&1 &
    PID=$!
    echo $PID > "$PID_FILE"
    
    sleep 2
    
    if is_running; then
        log "監視を開始しました (PID: $PID)"
        return 0
    else
        log "監視の開始に失敗しました"
        return 1
    fi
}

# 監視を停止
stop_monitor() {
    if ! is_running; then
        log "監視は実行されていません"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    log "監視を停止します (PID: $PID)..."
    
    kill -TERM "$PID" 2>/dev/null
    
    # プロセスが終了するまで待機（最大10秒）
    for i in {1..10}; do
        if ! ps -p "$PID" > /dev/null 2>&1; then
            rm -f "$PID_FILE"
            log "監視を停止しました"
            return 0
        fi
        sleep 1
    done
    
    # 強制終了
    kill -KILL "$PID" 2>/dev/null
    rm -f "$PID_FILE"
    log "監視を強制停止しました"
    return 0
}

# 監視の状態を確認
check_status() {
    if is_running; then
        PID=$(cat "$PID_FILE")
        echo "監視は実行中です (PID: $PID)"
        echo ""
        echo "プロセス情報:"
        ps -p "$PID" -o pid,ppid,user,start,time,command
    else
        echo "監視は停止しています"
    fi
    
    echo ""
    echo "スクリーンショット統計:"
    if [ -d "$SCRIPT_DIR/screenshots" ]; then
        total_files=$(find "$SCRIPT_DIR/screenshots" -type f | wc -l)
        total_size=$(du -sh "$SCRIPT_DIR/screenshots" 2>/dev/null | cut -f1)
        echo "  総ファイル数: $total_files"
        echo "  総サイズ: $total_size"
        
        if [ "$total_files" -gt 0 ]; then
            echo ""
            echo "最近のスクリーンショット:"
            find "$SCRIPT_DIR/screenshots" -type f -printf '%T@ %p\n' | sort -rn | head -5 | cut -d' ' -f2- | while read -r file; do
                echo "  - $(basename "$file") ($(date -r "$file" '+%Y-%m-%d %H:%M:%S'))"
            done
        fi
    else
        echo "  スクリーンショットフォルダが見つかりません"
    fi
}

# ログを表示
show_logs() {
    lines=50
    follow=false
    
    # オプション解析
    while [[ $# -gt 0 ]]; do
        case $1 in
            --tail)
                follow=true
                shift
                ;;
            --lines)
                lines=$2
                shift 2
                ;;
            *)
                shift
                ;;
        esac
    done
    
    echo "=== 監視ログ ==="
    if [ -f "$LOG_FILE" ]; then
        if [ "$follow" = true ]; then
            tail -f "$LOG_FILE"
        else
            tail -n "$lines" "$LOG_FILE"
        fi
    else
        echo "ログファイルが見つかりません"
    fi
    
    echo ""
    echo "=== 転送ログ ==="
    if [ -f "$SCRIPT_DIR/logs/transfers.jsonl" ]; then
        echo "最近の転送:"
        tail -n 10 "$SCRIPT_DIR/logs/transfers.jsonl" | while read -r line; do
            timestamp=$(echo "$line" | jq -r '.timestamp' 2>/dev/null)
            source=$(echo "$line" | jq -r '.source' 2>/dev/null | xargs basename)
            success=$(echo "$line" | jq -r '.success' 2>/dev/null)
            if [ "$success" = "true" ]; then
                echo "  ✓ $timestamp: $source"
            else
                echo "  ✗ $timestamp: $source (失敗)"
            fi
        done
    fi
}

# メイン処理
case "$1" in
    setup)
        # セットアップを実行
        "$SCRIPT_DIR/setup.sh"
        ;;
    start)
        start_monitor
        ;;
    stop)
        stop_monitor
        ;;
    restart)
        stop_monitor
        sleep 2
        start_monitor
        ;;
    status)
        check_status
        ;;
    watch)
        # 設定ファイルの存在確認
        if [ ! -f "$SCRIPT_DIR/config/config.json" ]; then
            echo "エラー: 設定ファイルが見つかりません。"
            echo "初回セットアップを実行してください："
            echo "  ./screenshot_manager.sh setup"
            exit 1
        fi
        # フォアグラウンドで実行
        if [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
            source "$SCRIPT_DIR/venv/bin/activate"
        fi
        python3 "$MONITOR_SCRIPT"
        ;;
    organize)
        # 手動整理（将来的に実装）
        echo "手動整理機能は開発中です"
        ;;
    cleanup)
        # 手動クリーンアップ（将来的に実装）
        echo "手動クリーンアップ機能は開発中です"
        ;;
    config)
        # 設定ファイルを編集
        if [ ! -f "$SCRIPT_DIR/config/config.json" ]; then
            echo "設定ファイルが見つかりません。"
            echo "初回セットアップを実行してください："
            echo "  ./screenshot_manager.sh setup"
            exit 1
        fi
        ${EDITOR:-nano} "$SCRIPT_DIR/config/config.json"
        ;;
    logs)
        shift
        show_logs "$@"
        ;;
    screenshot)
        # スクリーンショット撮影
        shift
        "$SCRIPT_DIR/take_screenshot.sh" "$@"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "不明なコマンド: $1"
        echo "使用方法: $0 {setup|start|stop|restart|status|watch|organize|cleanup|config|logs|screenshot|help}"
        exit 1
        ;;
esac