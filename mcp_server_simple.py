#!/usr/bin/env python3

import asyncio
import json
import sys
import subprocess
from pathlib import Path

# スクリプトのパス
SCRIPT_DIR = Path(__file__).parent
TAKE_SCREENSHOT_SCRIPT = SCRIPT_DIR / "take_screenshot.sh"
SCREENSHOT_MANAGER_SCRIPT = SCRIPT_DIR / "screenshot_manager.sh"

async def run_command(command):
    """コマンドを実行して結果を返す"""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=SCRIPT_DIR,
            timeout=30
        )
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": "コマンドがタイムアウトしました",
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"エラー: {str(e)}",
        }

async def run_standalone():
    """スタンドアロンモードでの実行"""
    print("Screenshot Manager - スタンドアロンモード")
    print("利用可能なコマンド:")
    print("- list_monitors: モニター一覧表示")
    print("- list_windows: ウィンドウ一覧表示")
    print("- take_screenshot [filename]: 全画面スクリーンショット")
    print("- take_monitor [index] [filename]: モニタースクリーンショット")
    print("- take_process [name] [filename]: プロセススクリーンショット")
    print("- status: 監視状態確認")
    print("- start: 監視開始")
    print("- stop: 監視停止")
    print("- quit: 終了")
    print()
    
    while True:
        try:
            command = input("screenshot> ").strip().split()
            if not command:
                continue
                
            cmd_name = command[0]
            args = command[1:]
            
            if cmd_name == "quit":
                break
            elif cmd_name == "list_monitors":
                result = await run_command([str(TAKE_SCREENSHOT_SCRIPT), "--list-monitors"])
                print(result["stdout"] if result["success"] else f"エラー: {result['stderr']}")
            elif cmd_name == "list_windows":
                result = await run_command([str(TAKE_SCREENSHOT_SCRIPT), "--list-windows"])
                print(result["stdout"] if result["success"] else f"エラー: {result['stderr']}")
            elif cmd_name == "take_screenshot":
                cmd = [str(TAKE_SCREENSHOT_SCRIPT)]
                if args:
                    cmd.extend(args)
                result = await run_command(cmd)
                print(result["stdout"] if result["success"] else f"エラー: {result['stderr']}")
            elif cmd_name == "take_monitor":
                if not args:
                    print("使用方法: take_monitor [index] [filename]")
                    continue
                cmd = [str(TAKE_SCREENSHOT_SCRIPT), "--monitor", args[0]]
                if len(args) > 1:
                    cmd.extend(args[1:])
                result = await run_command(cmd)
                print(result["stdout"] if result["success"] else f"エラー: {result['stderr']}")
            elif cmd_name == "take_process":
                if not args:
                    print("使用方法: take_process [name] [filename]")
                    continue
                cmd = [str(TAKE_SCREENSHOT_SCRIPT), "--process", args[0]]
                if len(args) > 1:
                    cmd.extend(args[1:])
                result = await run_command(cmd)
                print(result["stdout"] if result["success"] else f"エラー: {result['stderr']}")
            elif cmd_name == "status":
                result = await run_command([str(SCREENSHOT_MANAGER_SCRIPT), "status"])
                print(result["stdout"] if result["success"] else f"エラー: {result['stderr']}")
            elif cmd_name == "start":
                result = await run_command([str(SCREENSHOT_MANAGER_SCRIPT), "start"])
                print(result["stdout"] if result["success"] else f"エラー: {result['stderr']}")
            elif cmd_name == "stop":
                result = await run_command([str(SCREENSHOT_MANAGER_SCRIPT), "stop"])
                print(result["stdout"] if result["success"] else f"エラー: {result['stderr']}")
            else:
                print(f"不明なコマンド: {cmd_name}")
                
        except KeyboardInterrupt:
            print("\n終了します。")
            break
        except EOFError:
            break

if __name__ == "__main__":
    asyncio.run(run_standalone())