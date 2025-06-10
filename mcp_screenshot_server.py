#!/usr/bin/env python3

import asyncio
import json
import sys
import subprocess
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# MCPライブラリが利用できない場合の代替実装
try:
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    import mcp.server.stdio
    import mcp.types as types
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("MCPライブラリが見つかりません。スタンドアロンモードで実行します。", file=sys.stderr)
    print("MCPサーバーとして使用するには 'pip3 install mcp' を実行してください。", file=sys.stderr)

# サーバーインスタンス（MCPが利用可能な場合のみ）
if MCP_AVAILABLE:
    server = Server("screenshot-manager")

# スクリプトのパス
SCRIPT_DIR = Path(__file__).parent
TAKE_SCREENSHOT_SCRIPT = SCRIPT_DIR / "take_screenshot.sh"
SCREENSHOT_MANAGER_SCRIPT = SCRIPT_DIR / "screenshot_manager.sh"

if MCP_AVAILABLE:
    @server.list_tools()
    async def handle_list_tools() -> List[types.Tool]:
        """利用可能なツールのリストを返す"""
        return [
        types.Tool(
            name="list_monitors",
            description="利用可能なモニターの一覧を表示",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="list_windows",
            description="実行中のウィンドウの一覧を表示",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="take_screenshot",
            description="全画面のスクリーンショットを撮影",
            inputSchema={
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "保存するファイル名（オプション）",
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "保存先ディレクトリ（オプション）",
                        "default": "screenshots",
                    },
                },
            },
        ),
        types.Tool(
            name="take_monitor_screenshot",
            description="指定したモニターのスクリーンショットを撮影",
            inputSchema={
                "type": "object",
                "properties": {
                    "monitor_index": {
                        "type": "integer",
                        "description": "モニター番号（0から開始）",
                    },
                    "filename": {
                        "type": "string",
                        "description": "保存するファイル名（オプション）",
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "保存先ディレクトリ（オプション）",
                        "default": "screenshots",
                    },
                },
                "required": ["monitor_index"],
            },
        ),
        types.Tool(
            name="take_process_screenshot",
            description="指定したプロセス名のウィンドウのスクリーンショットを撮影",
            inputSchema={
                "type": "object",
                "properties": {
                    "process_name": {
                        "type": "string",
                        "description": "プロセス名（部分一致）",
                    },
                    "filename": {
                        "type": "string",
                        "description": "保存するファイル名（オプション）",
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "保存先ディレクトリ（オプション）",
                        "default": "screenshots",
                    },
                },
                "required": ["process_name"],
            },
        ),
        types.Tool(
            name="take_window_screenshot",
            description="指定したウィンドウハンドルのスクリーンショットを撮影",
            inputSchema={
                "type": "object",
                "properties": {
                    "window_handle": {
                        "type": "string",
                        "description": "ウィンドウハンドル",
                    },
                    "filename": {
                        "type": "string",
                        "description": "保存するファイル名（オプション）",
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "保存先ディレクトリ（オプション）",
                        "default": "screenshots",
                    },
                },
                "required": ["window_handle"],
            },
        ),
        types.Tool(
            name="monitor_status",
            description="スクリーンショット監視の状態を確認",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="start_monitor",
            description="スクリーンショット監視を開始",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="stop_monitor",
            description="スクリーンショット監視を停止",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]

async def run_command(command: List[str]) -> Dict[str, Any]:
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
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": "コマンドがタイムアウトしました",
            "returncode": -1,
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"エラー: {str(e)}",
            "returncode": -1,
        }

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: Optional[Dict[str, Any]]
) -> List[types.TextContent]:
    """ツールの呼び出しを処理"""
    if arguments is None:
        arguments = {}
    
    if name == "list_monitors":
        result = await run_command([str(TAKE_SCREENSHOT_SCRIPT), "--list-monitors"])
        content = result["stdout"] if result["success"] else f"エラー: {result['stderr']}"
        
    elif name == "list_windows":
        result = await run_command([str(TAKE_SCREENSHOT_SCRIPT), "--list-windows"])
        content = result["stdout"] if result["success"] else f"エラー: {result['stderr']}"
        
    elif name == "take_screenshot":
        cmd = [str(TAKE_SCREENSHOT_SCRIPT)]
        if "filename" in arguments:
            cmd.append(arguments["filename"])
        if "output_dir" in arguments:
            cmd.append(arguments["output_dir"])
        
        result = await run_command(cmd)
        content = result["stdout"] if result["success"] else f"エラー: {result['stderr']}"
        
    elif name == "take_monitor_screenshot":
        monitor_index = arguments["monitor_index"]
        cmd = [str(TAKE_SCREENSHOT_SCRIPT), "--monitor", str(monitor_index)]
        
        if "filename" in arguments:
            cmd.append(arguments["filename"])
        if "output_dir" in arguments:
            cmd.append(arguments["output_dir"])
        
        result = await run_command(cmd)
        content = result["stdout"] if result["success"] else f"エラー: {result['stderr']}"
        
    elif name == "take_process_screenshot":
        process_name = arguments["process_name"]
        cmd = [str(TAKE_SCREENSHOT_SCRIPT), "--process", process_name]
        
        if "filename" in arguments:
            cmd.append(arguments["filename"])
        if "output_dir" in arguments:
            cmd.append(arguments["output_dir"])
        
        result = await run_command(cmd)
        content = result["stdout"] if result["success"] else f"エラー: {result['stderr']}"
        
    elif name == "take_window_screenshot":
        window_handle = arguments["window_handle"]
        cmd = [str(TAKE_SCREENSHOT_SCRIPT), "--window", window_handle]
        
        if "filename" in arguments:
            cmd.append(arguments["filename"])
        if "output_dir" in arguments:
            cmd.append(arguments["output_dir"])
        
        result = await run_command(cmd)
        content = result["stdout"] if result["success"] else f"エラー: {result['stderr']}"
        
    elif name == "monitor_status":
        result = await run_command([str(SCREENSHOT_MANAGER_SCRIPT), "status"])
        content = result["stdout"] if result["success"] else f"エラー: {result['stderr']}"
        
    elif name == "start_monitor":
        result = await run_command([str(SCREENSHOT_MANAGER_SCRIPT), "start"])
        content = result["stdout"] if result["success"] else f"エラー: {result['stderr']}"
        
    elif name == "stop_monitor":
        result = await run_command([str(SCREENSHOT_MANAGER_SCRIPT), "stop"])
        content = result["stdout"] if result["success"] else f"エラー: {result['stderr']}"
        
    else:
        content = f"不明なツール: {name}"
    
    return [types.TextContent(type="text", text=content)]

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

async def main():
    if not MCP_AVAILABLE:
        await run_standalone()
        return
        
    # MCPサーバーを標準入出力で実行
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="screenshot-manager",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())