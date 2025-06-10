#!/bin/bash

# WSL上からWindowsのスクリーンショットを撮影するスクリプト

# 利用可能なモニターを表示
list_monitors() {
    echo "利用可能なモニター:"
    powershell.exe -Command "
Add-Type -AssemblyName System.Windows.Forms
\$monitors = [System.Windows.Forms.Screen]::AllScreens
for (\$i = 0; \$i -lt \$monitors.Count; \$i++) {
    \$m = \$monitors[\$i]
    \$primary = if (\$m.Primary) { ' (Primary)' } else { '' }
    \$width = \$m.Bounds.Width
    \$height = \$m.Bounds.Height
    \$x = \$m.Bounds.X
    \$y = \$m.Bounds.Y
    Write-Host \"Monitor \$i\`: \$width\`x\$height at (\$x,\$y)\$primary\"
}
"
}

# 実行中のウィンドウを表示
list_windows() {
    echo "実行中のウィンドウ:"
    powershell.exe -Command "
Get-Process | Where-Object { \$_.MainWindowHandle -ne 0 -and \$_.MainWindowTitle -ne '' } | 
ForEach-Object { 
    \$handle = \$_.MainWindowHandle.ToInt64()
    \$process = \$_.ProcessName
    \$title = \$_.MainWindowTitle
    Write-Host \"Handle: \$handle, Process: \$process, Title: \$title\"
}
"
}

# 指定モニターのスクリーンショットを撮影
take_monitor_screenshot() {
    local monitor_index="$1"
    local filename="${2:-monitor${monitor_index}_$(date +%Y%m%d_%H%M%S).png}"
    local output_dir="${3:-screenshots}"
    
    mkdir -p "$output_dir"
    
    local ps_script="
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

\$monitors = [System.Windows.Forms.Screen]::AllScreens
if ($monitor_index -ge \$monitors.Count) {
    Write-Host 'Error: Monitor index $monitor_index not found'
    exit 1
}

\$monitor = \$monitors[$monitor_index]
\$bounds = \$monitor.Bounds

\$bitmap = New-Object System.Drawing.Bitmap \$bounds.Width, \$bounds.Height
\$graphic = [System.Drawing.Graphics]::FromImage(\$bitmap)
\$graphic.CopyFromScreen(\$bounds.X, \$bounds.Y, 0, 0, \$bounds.Size)

\$bitmap.Save('$filename', [System.Drawing.Imaging.ImageFormat]::Png)
\$graphic.Dispose()
\$bitmap.Dispose()

Write-Host 'Monitor $monitor_index screenshot saved: $filename'
"
    
    powershell.exe -Command "$ps_script"
    
    if [ -f "$filename" ]; then
        echo "✓ モニター${monitor_index}のスクリーンショットを保存しました: $filename"
        if [ "$output_dir" != "." ]; then
            mv "$filename" "$output_dir/"
            echo "✓ ファイルを移動しました: $output_dir/$filename"
        fi
    else
        echo "✗ スクリーンショットの作成に失敗しました"
        return 1
    fi
}

# 指定ウィンドウのスクリーンショットを撮影
take_window_screenshot() {
    local window_handle="$1"
    local filename="${2:-window_$(date +%Y%m%d_%H%M%S).png}"
    local output_dir="${3:-screenshots}"
    
    mkdir -p "$output_dir"
    
    local ps_script="
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type -TypeDefinition '
using System;
using System.Drawing;
using System.Runtime.InteropServices;

public class Win32 {
    [DllImport(\"user32.dll\")]
    public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
    
    [DllImport(\"user32.dll\")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);
    
    [DllImport(\"user32.dll\")]
    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT {
        public int Left;
        public int Top;
        public int Right;
        public int Bottom;
    }
}
'

\$hWnd = [IntPtr]$window_handle
\$rect = New-Object Win32+RECT

if ([Win32]::GetWindowRect(\$hWnd, [ref]\$rect)) {
    # ウィンドウを前面に表示
    [Win32]::ShowWindow(\$hWnd, 9)  # SW_RESTORE
    [Win32]::SetForegroundWindow(\$hWnd)
    Start-Sleep -Milliseconds 200
    
    \$width = \$rect.Right - \$rect.Left
    \$height = \$rect.Bottom - \$rect.Top
    
    if (\$width -gt 0 -and \$height -gt 0) {
        \$bitmap = New-Object System.Drawing.Bitmap \$width, \$height
        \$graphic = [System.Drawing.Graphics]::FromImage(\$bitmap)
        \$graphic.CopyFromScreen(\$rect.Left, \$rect.Top, 0, 0, \$bitmap.Size)
        
        \$bitmap.Save('$filename', [System.Drawing.Imaging.ImageFormat]::Png)
        \$graphic.Dispose()
        \$bitmap.Dispose()
        
        Write-Host 'Window screenshot saved: $filename'
    } else {
        Write-Host 'Error: Invalid window dimensions'
        exit 1
    }
} else {
    Write-Host 'Error: Could not get window rectangle'
    exit 1
}
"
    
    powershell.exe -Command "$ps_script"
    
    if [ -f "$filename" ]; then
        echo "✓ ウィンドウのスクリーンショットを保存しました: $filename"
        if [ "$output_dir" != "." ]; then
            mv "$filename" "$output_dir/"
            echo "✓ ファイルを移動しました: $output_dir/$filename"
        fi
    else
        echo "✗ スクリーンショットの作成に失敗しました"
        return 1
    fi
}

# プロセス名でウィンドウのスクリーンショットを撮影
take_process_screenshot() {
    local process_name="$1"
    local filename="${2:-${process_name}_$(date +%Y%m%d_%H%M%S).png}"
    local output_dir="${3:-screenshots}"
    
    mkdir -p "$output_dir"
    
    echo "プロセス '$process_name' のウィンドウを検索中..."
    
    # より簡単なアプローチでウィンドウハンドルを取得
    local window_handle=$(powershell.exe -Command "
try {
    \$processes = Get-Process '*$process_name*' -ErrorAction Stop | Where-Object { \$_.MainWindowHandle -ne 0 }
    if (\$processes) {
        \$process = \$processes[0]
        Write-Host \$process.MainWindowHandle.ToInt64()
    } else {
        Write-Host '0'
    }
} catch {
    Write-Host '0'
}
" | tr -d '\r')
    
    if [ "$window_handle" != "0" ] && [ -n "$window_handle" ]; then
        echo "ウィンドウが見つかりました (Handle: $window_handle)"
        take_window_screenshot "$window_handle" "$filename" "$output_dir"
    else
        echo "✗ プロセス '$process_name' のウィンドウが見つかりませんでした"
        echo "ヒント: ./take_screenshot.sh --list-windows で利用可能なウィンドウを確認してください"
        return 1
    fi
}

# 全画面スクリーンショットを撮影
take_screenshot() {
    local filename="${1:-screenshot_$(date +%Y%m%d_%H%M%S).png}"
    local output_dir="${2:-screenshots}"
    
    mkdir -p "$output_dir"
    
    local ps_script="
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

\$Screen = [System.Windows.Forms.SystemInformation]::VirtualScreen
\$Width = \$Screen.Width
\$Height = \$Screen.Height
\$Left = \$Screen.Left
\$Top = \$Screen.Top

\$bitmap = New-Object System.Drawing.Bitmap \$Width, \$Height
\$graphic = [System.Drawing.Graphics]::FromImage(\$bitmap)
\$graphic.CopyFromScreen(\$Left, \$Top, 0, 0, \$bitmap.Size)

\$bitmap.Save('$filename', [System.Drawing.Imaging.ImageFormat]::Png)
\$graphic.Dispose()
\$bitmap.Dispose()

Write-Host 'Screenshot saved: $filename'
"
    
    powershell.exe -Command "$ps_script"
    
    if [ -f "$filename" ]; then
        echo "✓ スクリーンショットを保存しました: $filename"
        if [ "$output_dir" != "." ]; then
            mv "$filename" "$output_dir/"
            echo "✓ ファイルを移動しました: $output_dir/$filename"
        fi
    else
        echo "✗ スクリーンショットの作成に失敗しました"
        return 1
    fi
}

# 使用方法表示
show_usage() {
    echo "WSL Screenshot Tool"
    echo ""
    echo "使用方法:"
    echo "  $0 [オプション] [ファイル名] [出力ディレクトリ]"
    echo ""
    echo "オプション:"
    echo "  --list-monitors, -lm        利用可能なモニターを表示"
    echo "  --list-windows, -lw         実行中のウィンドウを表示"
    echo "  --monitor N, -m N           指定モニター（0,1,2...）のスクリーンショット"
    echo "  --window HANDLE, -w HANDLE  指定ウィンドウハンドルのスクリーンショット"
    echo "  --process NAME, -p NAME     指定プロセス名のウィンドウスクリーンショット"
    echo "  --help, -h                  このヘルプを表示"
    echo ""
    echo "例:"
    echo "  $0                           # 全画面スクリーンショット"
    echo "  $0 --list-monitors           # モニター一覧を表示"
    echo "  $0 --monitor 1               # モニター1のスクリーンショット"
    echo "  $0 --process chrome          # Chromeのウィンドウスクリーンショット"
    echo "  $0 --window 123456           # ハンドル123456のウィンドウスクリーンショット"
    echo "  $0 myscreen.png              # ファイル名を指定して全画面撮影"
    echo "  $0 --monitor 1 monitor1.png  # モニター1をmonitor1.pngで保存"
}

# メイン処理
case "$1" in
    --list-monitors|-lm)
        list_monitors
        ;;
    --list-windows|-lw)
        list_windows
        ;;
    --monitor|-m)
        shift
        monitor_index="$1"
        shift
        if [ -z "$monitor_index" ]; then
            echo "エラー: モニター番号を指定してください"
            echo "使用方法: $0 --monitor N [ファイル名] [出力ディレクトリ]"
            exit 1
        fi
        take_monitor_screenshot "$monitor_index" "$1" "$2"
        ;;
    --window|-w)
        shift
        window_handle="$1"
        shift
        if [ -z "$window_handle" ]; then
            echo "エラー: ウィンドウハンドルを指定してください"
            echo "使用方法: $0 --window HANDLE [ファイル名] [出力ディレクトリ]"
            exit 1
        fi
        take_window_screenshot "$window_handle" "$1" "$2"
        ;;
    --process|-p)
        shift
        process_name="$1"
        shift
        if [ -z "$process_name" ]; then
            echo "エラー: プロセス名を指定してください"
            echo "使用方法: $0 --process NAME [ファイル名] [出力ディレクトリ]"
            exit 1
        fi
        take_process_screenshot "$process_name" "$1" "$2"
        ;;
    --help|-h|help)
        show_usage
        ;;
    *)
        # デフォルトは全画面スクリーンショット
        take_screenshot "$1" "$2"
        ;;
esac