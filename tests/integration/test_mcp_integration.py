import pytest
import asyncio
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# MCPサーバーの統合テスト
class TestMCPServerIntegration:
    """MCP サーバー統合テストクラス"""
    
    @pytest.fixture
    def temp_config_dir(self):
        """一時設定ディレクトリの作成"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # 設定ファイルの作成
            config = {
                "windowsUsername": "testuser",
                "screenshotDir": str(temp_path / "screenshots"),
                "outputDir": str(temp_path / "output")
            }
            
            config_file = temp_path / "config.json"
            with open(config_file, 'w') as f:
                json.dump(config, f)
            
            webapp_config = {
                "DEFAULT_PORTS": [3000, 5173, 8000],
                "CHECK_INTERVAL": 1.0,
                "VIEWPORTS": [
                    {"width": 1920, "height": 1080, "name": "desktop"}
                ]
            }
            
            webapp_config_file = temp_path / "webapp_config.json"
            with open(webapp_config_file, 'w') as f:
                json.dump(webapp_config, f)
            
            yield temp_path
    
    @pytest.mark.asyncio
    async def test_mcp_server_initialization(self, temp_config_dir):
        """MCPサーバー初期化のテスト"""
        with patch('src.integrations.mcp_server.Path') as mock_path:
            mock_path.return_value = temp_config_dir
            
            from src.integrations.mcp_server import ScreenshotManagerMCP
            
            mcp_server = ScreenshotManagerMCP()
            assert mcp_server.server is not None
            assert mcp_server.logger is not None
    
    @pytest.mark.asyncio
    async def test_auto_screenshot_tool(self, temp_config_dir):
        """自動スクリーンショット機能のテスト"""
        from src.integrations.mcp_server import ScreenshotManagerMCP
        
        with patch('src.integrations.mcp_server.Path') as mock_path:
            mock_path.return_value = temp_config_dir
            
            mcp_server = ScreenshotManagerMCP()
            
            # モック設定
            with patch.object(mcp_server, '_capture_webapp_screenshots', 
                            new_callable=AsyncMock) as mock_capture:
                mock_capture.return_value = {
                    "success": True,
                    "screenshots": ["test1.png", "test2.png"],
                    "message": "テスト成功"
                }
                
                # 自動スクリーンショット実行
                result = await mcp_server.handle_auto_screenshot_on_create({
                    "project_path": str(temp_config_dir)
                })
                
                assert result["success"] is True
                assert len(result["screenshots"]) == 2
                mock_capture.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_project_detection_tool(self, temp_config_dir):
        """プロジェクト検出機能のテスト"""
        from src.integrations.mcp_server import ScreenshotManagerMCP
        
        # テスト用プロジェクトファイルの作成
        package_json = temp_config_dir / "package.json"
        with open(package_json, 'w') as f:
            json.dump({
                "name": "test-project",
                "scripts": {
                    "dev": "vite",
                    "build": "vite build"
                },
                "dependencies": {
                    "react": "^18.0.0",
                    "vite": "^4.0.0"
                }
            }, f)
        
        with patch('src.integrations.mcp_server.Path') as mock_path:
            mock_path.return_value = temp_config_dir
            
            mcp_server = ScreenshotManagerMCP()
            
            result = await mcp_server.handle_detect_project({
                "project_path": str(temp_config_dir)
            })
            
            assert result["success"] is True
            assert result["framework"] == "React"
            assert result["build_tool"] == "Vite"
    
    @pytest.mark.asyncio
    async def test_config_generation_tool(self, temp_config_dir):
        """設定生成機能のテスト"""
        from src.integrations.mcp_server import ScreenshotManagerMCP
        
        with patch('src.integrations.mcp_server.Path') as mock_path:
            mock_path.return_value = temp_config_dir
            
            mcp_server = ScreenshotManagerMCP()
            
            result = await mcp_server.handle_generate_config({
                "project_path": str(temp_config_dir),
                "framework": "React",
                "port": 3000
            })
            
            assert result["success"] is True
            assert "config_path" in result
            
            # 生成された設定ファイルの確認
            config_path = Path(result["config_path"])
            assert config_path.exists()
            
            with open(config_path, 'r') as f:
                config = json.load(f)
                assert config["framework"] == "React"
                assert config["port"] == 3000
    
    @pytest.mark.asyncio
    async def test_manual_screenshot_tool(self, temp_config_dir):
        """手動スクリーンショット機能のテスト"""
        from src.integrations.mcp_server import ScreenshotManagerMCP
        
        with patch('src.integrations.mcp_server.Path') as mock_path:
            mock_path.return_value = temp_config_dir
            
            mcp_server = ScreenshotManagerMCP()
            
            with patch.object(mcp_server, '_take_manual_screenshots',
                            new_callable=AsyncMock) as mock_screenshot:
                mock_screenshot.return_value = {
                    "success": True,
                    "screenshots": ["manual1.png"],
                    "message": "手動スクリーンショット完了"
                }
                
                result = await mcp_server.handle_take_screenshot({
                    "project_path": str(temp_config_dir),
                    "pages": ["/", "/about"]
                })
                
                assert result["success"] is True
                assert len(result["screenshots"]) == 1
                mock_screenshot.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_status_tool(self, temp_config_dir):
        """ステータス取得機能のテスト"""
        from src.integrations.mcp_server import ScreenshotManagerMCP
        
        with patch('src.integrations.mcp_server.Path') as mock_path:
            mock_path.return_value = temp_config_dir
            
            mcp_server = ScreenshotManagerMCP()
            
            result = await mcp_server.handle_get_status({})
            
            assert result["success"] is True
            assert "system_info" in result
            assert "monitoring_status" in result
            assert "screenshot_stats" in result
            
            # システム情報の確認
            system_info = result["system_info"]
            assert "platform" in system_info
            assert "python_version" in system_info
            assert "memory_usage" in system_info


class TestHTTPServerIntegration:
    """HTTP サーバー統合テストクラス"""
    
    @pytest.mark.asyncio
    async def test_http_server_health_check(self):
        """HTTPサーバーヘルスチェックのテスト"""
        from src.integrations.mcp_http_server import create_app
        
        app = create_app()
        
        # テストクライアント作成（実際のHTTPリクエストではなく、アプリケーション内部テスト）
        # ここでは簡単な応答確認のみ
        assert app is not None
    
    @pytest.mark.asyncio 
    async def test_http_endpoints_structure(self):
        """HTTPエンドポイント構造のテスト"""
        from src.integrations.mcp_http_server import get_endpoints_info
        
        endpoints = get_endpoints_info()
        
        expected_endpoints = [
            "/", "/status", "/screenshot/auto", "/screenshot/manual",
            "/project/detect", "/config/generate"
        ]
        
        for endpoint in expected_endpoints:
            assert any(endpoint in ep for ep in endpoints["endpoints"])


class TestEndToEndWorkflow:
    """エンドツーエンド ワークフローテスト"""
    
    @pytest.mark.asyncio
    async def test_complete_workflow(self, temp_config_dir):
        """完全なワークフローのテスト"""
        # 1. プロジェクト検出
        # 2. 設定生成
        # 3. スクリーンショット撮影
        # 4. ステータス確認
        
        # テスト用プロジェクトセットアップ
        package_json = temp_config_dir / "package.json"
        with open(package_json, 'w') as f:
            json.dump({
                "name": "test-workflow-project",
                "dependencies": {"react": "^18.0.0"}
            }, f)
        
        from src.integrations.mcp_server import ScreenshotManagerMCP
        
        with patch('src.integrations.mcp_server.Path') as mock_path:
            mock_path.return_value = temp_config_dir
            
            mcp_server = ScreenshotManagerMCP()
            
            # 1. プロジェクト検出
            detect_result = await mcp_server.handle_detect_project({
                "project_path": str(temp_config_dir)
            })
            assert detect_result["success"] is True
            framework = detect_result["framework"]
            
            # 2. 設定生成
            config_result = await mcp_server.handle_generate_config({
                "project_path": str(temp_config_dir),
                "framework": framework,
                "port": 3000
            })
            assert config_result["success"] is True
            
            # 3. ステータス確認
            status_result = await mcp_server.handle_get_status({})
            assert status_result["success"] is True
            
            # ワークフロー全体の成功確認
            assert all([
                detect_result["success"],
                config_result["success"], 
                status_result["success"]
            ])


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])