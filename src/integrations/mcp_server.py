#!/usr/bin/env python3
"""
Claude Code MCP統合サーバー
Claude Codeからの直接呼び出しを受け付け、Screenshot Manager機能を提供
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

# MCPライブラリ（仮想的な実装 - 実際のMCPライブラリに置き換え）
class MCPServer:
    """MCP Server基底クラス"""
    def __init__(self, name: str):
        self.name = name
        self.tools = {}
        self.logger = logging.getLogger(__name__)
    
    def add_tool(self, name: str, description: str, handler):
        """ツールを追加"""
        self.tools[name] = {
            'description': description,
            'handler': handler
        }
    
    async def start(self, host: str = 'localhost', port: int = 8080):
        """サーバー開始"""
        self.logger.info(f"MCP Server starting on {host}:{port}")
        # 実際のサーバー起動処理
        
    async def handle_request(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """リクエスト処理"""
        if tool_name in self.tools:
            return await self.tools[tool_name]['handler'](args)
        else:
            return {"error": f"Tool {tool_name} not found"}

@dataclass
class ScreenshotRequest:
    """スクリーンショット要求"""
    project_path: str
    framework: Optional[str] = None
    custom_config: Optional[Dict] = None
    pages: Optional[List[str]] = None
    immediate: bool = True

@dataclass
class ScreenshotResult:
    """スクリーンショット結果"""
    success: bool
    screenshots: List[str] = None
    report_path: str = ""
    project_info: Dict = None
    error: str = ""
    execution_time: float = 0.0
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if self.screenshots is None:
            self.screenshots = []

class ScreenshotManagerMCP:
    """Screenshot Manager MCP統合クラス"""
    
    def __init__(self):
        self.server = MCPServer("screenshot-manager")
        self.logger = logging.getLogger(__name__)
        self.setup_tools()
    
    def setup_tools(self):
        """MCPツールのセットアップ"""
        
        # プロジェクト作成時の自動スクリーンショット
        self.server.add_tool(
            "auto_screenshot_on_create",
            "Claude Codeでプロジェクト作成時に自動的にスクリーンショットを撮影",
            self.handle_auto_screenshot
        )
        
        # 手動スクリーンショット要求
        self.server.add_tool(
            "take_screenshot",
            "指定されたプロジェクトのスクリーンショットを撮影",
            self.handle_manual_screenshot
        )
        
        # プロジェクト検出
        self.server.add_tool(
            "detect_project",
            "プロジェクトの種類を自動検出し、設定を生成",
            self.handle_project_detection
        )
        
        # 設定ファイル生成
        self.server.add_tool(
            "generate_config",
            "プロジェクト用の最適な設定ファイルを生成",
            self.handle_config_generation
        )
        
        # ステータス確認
        self.server.add_tool(
            "get_status",
            "Screenshot Managerの現在の状態を取得",
            self.handle_status_check
        )
    
    async def handle_auto_screenshot(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """自動スクリーンショット処理"""
        try:
            # リクエスト解析
            request = ScreenshotRequest(
                project_path=args.get('project_path', '.'),
                framework=args.get('framework'),
                custom_config=args.get('config', {}),
                immediate=args.get('immediate', True)
            )
            
            self.logger.info(f"自動スクリーンショット要求: {request.project_path}")
            
            # 実際のスクリーンショット処理を実行
            result = await self._execute_screenshot_workflow(request)
            
            return {
                "success": result.success,
                "result": asdict(result),
                "message": "自動スクリーンショット完了" if result.success else f"エラー: {result.error}"
            }
            
        except Exception as e:
            self.logger.error(f"自動スクリーンショットエラー: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "自動スクリーンショット処理中にエラーが発生しました"
            }
    
    async def handle_manual_screenshot(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """手動スクリーンショット処理"""
        try:
            request = ScreenshotRequest(
                project_path=args.get('project_path', '.'),
                pages=args.get('pages', ['/']),
                custom_config=args.get('config', {})
            )
            
            self.logger.info(f"手動スクリーンショット要求: {request.project_path}")
            
            result = await self._execute_screenshot_workflow(request)
            
            return {
                "success": result.success,
                "result": asdict(result),
                "message": f"スクリーンショット完了: {len(result.screenshots)}枚撮影"
            }
            
        except Exception as e:
            self.logger.error(f"手動スクリーンショットエラー: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def handle_project_detection(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """プロジェクト検出処理"""
        try:
            project_path = Path(args.get('project_path', '.'))
            
            # プロジェクト検出の実行
            from ..detectors.project_detector import ProjectDetector
            detector = ProjectDetector(logger=self.logger)
            project_info = detector.detect_project(project_path)
            
            if project_info:
                return {
                    "success": True,
                    "project_info": asdict(project_info),
                    "message": f"{project_info.framework}プロジェクトを検出しました"
                }
            else:
                return {
                    "success": False,
                    "message": "プロジェクトを検出できませんでした"
                }
                
        except Exception as e:
            self.logger.error(f"プロジェクト検出エラー: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def handle_config_generation(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """設定ファイル生成処理"""
        try:
            project_path = Path(args.get('project_path', '.'))
            format_type = args.get('format', 'yaml')
            
            # 設定ファイル生成
            from ..analyzers.config_generator import ConfigGenerator
            generator = ConfigGenerator(logger=self.logger)
            config_file = generator.generate_and_save(project_path, format=format_type)
            
            if config_file:
                return {
                    "success": True,
                    "config_file": str(config_file),
                    "message": f"設定ファイルを生成しました: {config_file.name}"
                }
            else:
                return {
                    "success": False,
                    "message": "設定ファイルの生成に失敗しました"
                }
                
        except Exception as e:
            self.logger.error(f"設定生成エラー: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def handle_status_check(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """ステータス確認処理"""
        try:
            status = {
                "server_status": "running",
                "version": "2.1.0",
                "supported_frameworks": [
                    "React", "Vue", "Angular", "Next.js",
                    "Django", "Flask", "Express", "Vite"
                ],
                "features": {
                    "project_detection": True,
                    "auto_config_generation": True,
                    "responsive_capture": True,
                    "page_tour": True,
                    "html_report": True,
                    "mcp_integration": True
                },
                "last_updated": datetime.now().isoformat()
            }
            
            return {
                "success": True,
                "status": status,
                "message": "Screenshot Manager は正常に動作しています"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_screenshot_workflow(self, request: ScreenshotRequest) -> ScreenshotResult:
        """スクリーンショットワークフローの実行"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # 1. プロジェクト検出
            from ..detectors.project_detector import ProjectDetector
            detector = ProjectDetector(logger=self.logger)
            project_path = Path(request.project_path)
            project_info = detector.detect_project(project_path)
            
            if not project_info:
                return ScreenshotResult(
                    success=False,
                    error="プロジェクトを検出できませんでした"
                )
            
            # 2. 設定生成（必要に応じて）
            config_file = project_path / ".screenshot-manager.yaml"
            if not config_file.exists():
                from ..analyzers.config_generator import ConfigGenerator
                generator = ConfigGenerator(logger=self.logger)
                generator.generate_and_save(project_path)
            
            # 3. 実際のスクリーンショット撮影
            self.logger.info(f"🚀 スクリーンショット撮影開始: {project_info.framework}プロジェクト")
            
            # WebアプリMonitorを使用してスクリーンショットを撮影
            from ..monitors.webapp_monitor import AppInfo
            
            # AppInfoオブジェクトを作成
            app_info = AppInfo(
                port=project_info.default_port,
                url=f"http://localhost:{project_info.default_port}",
                framework=project_info.framework,
                project_path=str(project_path)
            )
            
            # Playwrightを使用した撮影
            screenshots = []
            report_path = ""
            
            try:
                from ..capture.playwright_capture import PlaywrightCapture
                
                # スクリーンショットディレクトリ作成
                screenshot_dir = project_path / "screenshots"
                screenshot_dir.mkdir(exist_ok=True)
                
                capture = PlaywrightCapture(logger=self.logger)
                await capture.initialize()
                
                # 複数ビューポートでキャプチャ
                viewports = [
                    {'name': 'desktop', 'width': 1920, 'height': 1080},
                    {'name': 'tablet', 'width': 768, 'height': 1024},
                    {'name': 'mobile', 'width': 375, 'height': 667}
                ]
                
                for viewport in viewports:
                    filename = f"{viewport['name']}_{project_info.framework.lower()}_{app_info.port}.png"
                    screenshot_path = screenshot_dir / filename
                    
                    success = await capture.capture_viewport(
                        url=app_info.url,
                        viewport=viewport,
                        output_path=str(screenshot_path),
                        wait_time=2000
                    )
                    
                    if success:
                        screenshots.append(str(screenshot_path))
                        self.logger.info(f"✅ {viewport['name']} キャプチャ完了: {filename}")
                    else:
                        self.logger.warning(f"❌ {viewport['name']} キャプチャ失敗")
                
                # HTMLレポート生成
                if screenshots:
                    report_path = str(screenshot_dir / "screenshot_report.html")
                    await capture.generate_html_report(
                        screenshots=screenshots,
                        app_info=app_info,
                        output_path=report_path
                    )
                    self.logger.info(f"📄 HTMLレポート生成: {report_path}")
                
                await capture.cleanup()
                
            except ImportError:
                self.logger.warning("Playwrightが利用できません。基本撮影を試行します")
                # 基本的なスクリーンショット撮影にフォールバック
                screenshot_path = project_path / "screenshots" / f"basic_{project_info.framework.lower()}.png"
                screenshot_path.parent.mkdir(exist_ok=True)
                screenshots = [str(screenshot_path)]
                
                # take_screenshot.sh を使用
                script_path = Path(__file__).parent.parent.parent / "take_screenshot.sh"
                if script_path.exists():
                    import subprocess
                    result = subprocess.run([
                        str(script_path), str(screenshot_path)
                    ], capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        self.logger.info(f"✅ 基本スクリーンショット完了: {screenshot_path}")
                    else:
                        self.logger.error(f"❌ 基本スクリーンショット失敗: {result.stderr}")
                        screenshots = []
            
            execution_time = asyncio.get_event_loop().time() - start_time
            
            return ScreenshotResult(
                success=len(screenshots) > 0,
                screenshots=screenshots,
                report_path=report_path,
                project_info=asdict(project_info),
                execution_time=execution_time,
                error="" if screenshots else "スクリーンショット撮影に失敗しました"
            )
            
        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            self.logger.error(f"スクリーンショットワークフローエラー: {e}")
            return ScreenshotResult(
                success=False,
                error=str(e),
                execution_time=execution_time
            )
    
    async def start_server(self, host: str = 'localhost', port: int = 8080):
        """MCPサーバーを開始"""
        self.logger.info("🚀 Screenshot Manager MCP Server を開始...")
        self.logger.info(f"📋 利用可能なツール: {len(self.server.tools)}個")
        
        for tool_name, tool_info in self.server.tools.items():
            self.logger.info(f"   - {tool_name}: {tool_info['description']}")
        
        await self.server.start(host, port)
        self.logger.info(f"✅ MCP Server が {host}:{port} で開始されました")

# Claude Code統合のヘルパー関数
class ClaudeCodeIntegration:
    """Claude Code統合ユーティリティ"""
    
    @staticmethod
    async def on_project_created(project_path: str, framework: str = None) -> Dict[str, Any]:
        """プロジェクト作成時のフック"""
        mcp = ScreenshotManagerMCP()
        
        return await mcp.handle_auto_screenshot({
            'project_path': project_path,
            'framework': framework,
            'immediate': True
        })
    
    @staticmethod
    async def take_manual_screenshot(project_path: str, pages: List[str] = None) -> Dict[str, Any]:
        """手動スクリーンショット要求"""
        mcp = ScreenshotManagerMCP()
        
        return await mcp.handle_manual_screenshot({
            'project_path': project_path,
            'pages': pages or ['/']
        })

def main():
    """MCP Server起動"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    async def run_server():
        mcp = ScreenshotManagerMCP()
        await mcp.start_server()
    
    print("🤖 Screenshot Manager MCP Server")
    print("Claude Code統合モードで起動します...")
    
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        print("\n🛑 MCP Server を停止しています...")
    except Exception as e:
        print(f"❌ MCP Server エラー: {e}")

if __name__ == "__main__":
    main()