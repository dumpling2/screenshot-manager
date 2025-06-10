#!/bin/bash

# Screenshot Manager セットアップスクリプト

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_TEMPLATE="$SCRIPT_DIR/config/config.json.template"
CONFIG_FILE="$SCRIPT_DIR/config/config.json"

echo "====================================="
echo " Screenshot Manager セットアップ"
echo "====================================="
echo ""

# 既に設定ファイルが存在する場合の確認
if [ -f "$CONFIG_FILE" ]; then
    echo "既に設定ファイルが存在します。"
    read -p "上書きしますか？ (y/N): " overwrite
    if [[ ! "$overwrite" =~ ^[Yy]$ ]]; then
        echo "セットアップをキャンセルしました。"
        exit 0
    fi
fi

# Windowsユーザー名の取得
echo "Windowsのユーザー名を入力してください。"
echo "（通常はC:\\Users\\[ユーザー名]のユーザー名部分）"
read -p "Windowsユーザー名: " windows_username

# 入力確認
if [ -z "$windows_username" ]; then
    echo "エラー: ユーザー名が入力されていません。"
    exit 1
fi

# スクリーンショットフォルダの存在確認
screenshot_path="/mnt/c/Users/$windows_username/Pictures/Screenshots"
echo ""
echo "Windowsのスクリーンショットフォルダを確認しています..."
echo "パス: $screenshot_path"

if [ -d "$screenshot_path" ]; then
    echo "✓ スクリーンショットフォルダが見つかりました"
    
    # フォルダ内のファイル数を確認
    file_count=$(find "$screenshot_path" -type f -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" 2>/dev/null | wc -l)
    echo "  現在のスクリーンショット数: $file_count"
else
    echo "⚠ スクリーンショットフォルダが見つかりません"
    echo ""
    echo "以下の可能性があります："
    echo "1. Windowsユーザー名が正しくない"
    echo "2. スクリーンショットフォルダが別の場所にある"
    echo "3. まだスクリーンショットを撮影していない"
    echo ""
    read -p "このまま続行しますか？ (y/N): " continue_anyway
    if [[ ! "$continue_anyway" =~ ^[Yy]$ ]]; then
        echo "セットアップをキャンセルしました。"
        exit 0
    fi
fi

# カスタムパスの設定
echo ""
echo "デフォルトのスクリーンショットパスを使用しますか？"
echo "デフォルト: $screenshot_path"
read -p "デフォルトを使用 (Y/n): " use_default

if [[ "$use_default" =~ ^[Nn]$ ]]; then
    read -p "カスタムパスを入力してください: " custom_path
    if [ -n "$custom_path" ]; then
        # Windowsパスが入力された場合の変換
        if [[ "$custom_path" =~ ^[A-Za-z]: ]]; then
            # C:\path\to\folder -> /mnt/c/path/to/folder
            drive_letter=$(echo "$custom_path" | cut -c1 | tr '[:upper:]' '[:lower:]')
            path_part=$(echo "$custom_path" | cut -c3- | tr '\\' '/')
            screenshot_path="/mnt/$drive_letter$path_part"
            echo "WSLパスに変換しました: $screenshot_path"
        else
            screenshot_path="$custom_path"
        fi
    fi
fi

# 設定ファイルの生成
echo ""
echo "設定ファイルを生成しています..."

# テンプレートをコピーして置換
mkdir -p "$SCRIPT_DIR/config"
sed "s/{WINDOWS_USERNAME}/$windows_username/g" "$CONFIG_TEMPLATE" > "$CONFIG_FILE"

# screenshot_pathがデフォルトと異なる場合は更新
if [ "$screenshot_path" != "/mnt/c/Users/$windows_username/Pictures/Screenshots" ]; then
    # 一時ファイルを使用して設定を更新
    tmp_file=$(mktemp)
    jq --arg path "$screenshot_path" '.windowsScreenshotPath = $path' "$CONFIG_FILE" > "$tmp_file"
    mv "$tmp_file" "$CONFIG_FILE"
fi

echo "✓ 設定ファイルを作成しました: $CONFIG_FILE"

# 必要なディレクトリの作成
echo ""
echo "必要なディレクトリを作成しています..."
mkdir -p "$SCRIPT_DIR/screenshots"
mkdir -p "$SCRIPT_DIR/logs"
echo "✓ ディレクトリを作成しました"

# 実行権限の付与
echo ""
echo "実行権限を設定しています..."
chmod +x "$SCRIPT_DIR/screenshot_monitor.py"
chmod +x "$SCRIPT_DIR/screenshot_manager.sh"
chmod +x "$SCRIPT_DIR/setup.sh"
echo "✓ 実行権限を設定しました"

# セットアップ完了
echo ""
echo "====================================="
echo " セットアップが完了しました！"
echo "====================================="
echo ""
echo "以下のコマンドで監視を開始できます："
echo "  ./screenshot_manager.sh start"
echo ""
echo "ヘルプを表示："
echo "  ./screenshot_manager.sh help"
echo ""

# 今すぐ開始するか確認
read -p "今すぐ監視を開始しますか？ (y/N): " start_now
if [[ "$start_now" =~ ^[Yy]$ ]]; then
    echo ""
    "$SCRIPT_DIR/screenshot_manager.sh" start
fi