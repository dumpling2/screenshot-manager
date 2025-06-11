#!/usr/bin/env python3
"""
Playwright を使用したWebアプリケーションスクリーンショット撮影モジュール
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import asyncio

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

class PlaywrightScreenshotCapture:
    """Playwrightを使用したスクリーンショット撮影クラス"""
    
    def __init__(self, config: Dict = None, logger=None):
        self.config = config or {}
        self.logger = logger or logging.getLogger(__name__)
        self.browser = None
        self.context = None
        
    async def setup_browser(self):
        """ブラウザの初期化"""
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwrightがインストールされていません")
        
        self.playwright = await async_playwright().start()
        
        # Chromiumブラウザを起動（ヘッドレスモード）
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        
        # ブラウザコンテキスト作成
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
    
    async def capture_webapp_screenshots(self, app_info, output_dir: Path = None):
        """Webアプリのスクリーンショットを撮影"""
        if not output_dir:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir = Path(f"./screenshots/webapp_{app_info.port}_{timestamp}")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            await self.setup_browser()
            
            # メインページのスクリーンショット
            await self._capture_main_page(app_info, output_dir)
            
            # レスポンシブテスト
            await self._capture_responsive_screenshots(app_info, output_dir)
            
            # 主要ページ巡回キャプチャ
            await self._capture_page_tour(app_info, output_dir)
            
            # エラーページのチェック
            await self._check_for_errors(app_info, output_dir)
            
            # レポート生成
            self._generate_report(app_info, output_dir)
            
            self.logger.info(f"📸 スクリーンショット撮影完了: {output_dir}")
            return output_dir
            
        except Exception as e:
            self.logger.error(f"スクリーンショット撮影エラー: {e}")
            return None
        finally:
            await self.cleanup()
    
    async def _capture_main_page(self, app_info, output_dir: Path):
        """メインページのスクリーンショット"""
        page = await self.context.new_page()
        
        # コンソールエラーをキャプチャ
        console_errors = []
        page.on('console', lambda msg: console_errors.append({
            'type': msg.type,
            'text': msg.text,
            'location': msg.location
        }) if msg.type in ['error', 'warning'] else None)
        
        try:
            # ページ読み込み
            await page.goto(app_info.url, wait_until='networkidle', timeout=30000)
            
            # 待機時間
            wait_time = self.config.get('capture', {}).get('wait_before_capture', 2000)
            await page.wait_for_timeout(wait_time)
            
            # フルページスクリーンショット
            await page.screenshot(
                path=output_dir / "main_page.png",
                full_page=True
            )
            
            # ビューポートスクリーンショット
            await page.screenshot(
                path=output_dir / "viewport.png"
            )
            
            # ページ情報を保存
            page_info = {
                'url': app_info.url,
                'title': await page.title(),
                'timestamp': datetime.now().isoformat(),
                'console_errors': console_errors,
                'viewport': await page.evaluate('({width: window.innerWidth, height: window.innerHeight})')
            }
            
            with open(output_dir / "page_info.json", 'w') as f:
                json.dump(page_info, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"メインページキャプチャエラー: {e}")
        finally:
            await page.close()
    
    async def _capture_responsive_screenshots(self, app_info, output_dir: Path):
        """レスポンシブデザインのスクリーンショット"""
        viewports = self.config.get('capture', {}).get('viewports', {
            'desktop': {'width': 1920, 'height': 1080},
            'tablet': {'width': 768, 'height': 1024},
            'mobile': {'width': 375, 'height': 667}
        })
        
        for device_name, viewport in viewports.items():
            try:
                # 新しいコンテキストでビューポートを設定
                context = await self.browser.new_context(
                    viewport={'width': viewport['width'], 'height': viewport['height']}
                )
                page = await context.new_page()
                
                # ページ読み込み
                await page.goto(app_info.url, wait_until='networkidle')
                await page.wait_for_timeout(1000)
                
                # スクリーンショット
                await page.screenshot(
                    path=output_dir / f"{device_name}.png",
                    full_page=True
                )
                
                await page.close()
                await context.close()
                
            except Exception as e:
                self.logger.error(f"{device_name}スクリーンショットエラー: {e}")
                if 'context' in locals():
                    await context.close()
    
    async def _capture_page_tour(self, app_info, output_dir: Path):
        """主要ページ巡回キャプチャ"""
        pages = self.config.get('capture', {}).get('pages', ['/'])
        
        if not pages or pages == ['/']: 
            self.logger.info("主要ページ巡回: ルートページのみ（既に撮影済み）")
            return
        
        self.logger.info(f"主要ページ巡回開始: {len(pages)}ページ")
        page_tour_dir = output_dir / "page_tour"
        page_tour_dir.mkdir(exist_ok=True)
        
        page = await self.context.new_page()
        
        try:
            for i, page_path in enumerate(pages):
                try:
                    # URLを構築
                    if page_path.startswith('http'):
                        page_url = page_path  # 絶対URL
                    else:
                        page_url = f"{app_info.url.rstrip('/')}{page_path}"
                    
                    self.logger.info(f"ページ巡回 {i+1}/{len(pages)}: {page_url}")
                    
                    # ページアクセス
                    await page.goto(page_url, wait_until='networkidle', timeout=15000)
                    await page.wait_for_timeout(2000)  # ページ安定化待機
                    
                    # ページ名を生成（URL安全な文字列に変換）
                    page_name = page_path.replace('/', '_').replace('?', '_').replace('#', '_')
                    if page_name.startswith('_'):
                        page_name = page_name[1:]
                    if not page_name:
                        page_name = 'root'
                    
                    # スクリーンショット撮影
                    await page.screenshot(
                        path=page_tour_dir / f"{i+1:02d}_{page_name}.png",
                        full_page=True
                    )
                    
                    # ページ情報を保存
                    page_info = {
                        'url': page_url,
                        'path': page_path,
                        'title': await page.title(),
                        'timestamp': datetime.now().isoformat(),
                        'order': i + 1
                    }
                    
                    with open(page_tour_dir / f"{i+1:02d}_{page_name}_info.json", 'w') as f:
                        json.dump(page_info, f, indent=2, ensure_ascii=False)
                    
                    self.logger.info(f"✅ {page_path} キャプチャ完了")
                    
                except Exception as e:
                    self.logger.error(f"ページキャプチャエラー ({page_path}): {e}")
                    continue
        
        finally:
            await page.close()
        
        self.logger.info(f"主要ページ巡回完了: {page_tour_dir}")
    
    async def _check_for_errors(self, app_info, output_dir: Path):
        """エラーページの検出"""
        page = await self.context.new_page()
        
        try:
            await page.goto(app_info.url, wait_until='networkidle')
            
            # エラー要素の検索
            error_selectors = self.config.get('capture', {}).get('error_selectors', [
                '.error',
                '.alert-danger',
                '[data-testid="error-message"]'
            ])
            
            errors_found = []
            for selector in error_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        for i, element in enumerate(elements):
                            text = await element.text_content()
                            errors_found.append({
                                'selector': selector,
                                'text': text,
                                'index': i
                            })
                except:
                    continue
            
            # エラーが見つかった場合
            if errors_found:
                await page.screenshot(path=output_dir / "errors_detected.png")
                
                with open(output_dir / "errors.json", 'w') as f:
                    json.dump(errors_found, f, indent=2, ensure_ascii=False)
                
                self.logger.warning(f"エラー要素を検出: {len(errors_found)}個")
                
        except Exception as e:
            self.logger.error(f"エラー検出処理エラー: {e}")
        finally:
            await page.close()
    
    def _generate_report(self, app_info, output_dir: Path):
        """HTMLレポート生成"""
        html_content = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Webアプリ動作確認レポート - {app_info.framework}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f5f5f5; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .screenshot {{ margin: 20px 0; }}
        .screenshot img {{ max-width: 100%; border: 1px solid #ddd; border-radius: 4px; }}
        .viewport-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
        .info {{ background: #e7f3ff; padding: 15px; border-radius: 5px; margin: 10px 0; }}
        .error {{ background: #ffe7e7; padding: 15px; border-radius: 5px; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Webアプリ動作確認レポート</h1>
        <div class="info">
            <strong>URL:</strong> {app_info.url}<br>
            <strong>Framework:</strong> {app_info.framework}<br>
            <strong>検出時刻:</strong> {app_info.detected_at}<br>
            <strong>プロセス:</strong> {app_info.process_name}
        </div>
    </div>
    
    <h2>📱 レスポンシブテスト</h2>
    <div class="viewport-grid">
        <div class="screenshot">
            <h3>Desktop (1920x1080)</h3>
            <img src="desktop.png" alt="Desktop view">
        </div>
        <div class="screenshot">
            <h3>Tablet (768x1024)</h3>
            <img src="tablet.png" alt="Tablet view">
        </div>
        <div class="screenshot">
            <h3>Mobile (375x667)</h3>
            <img src="mobile.png" alt="Mobile view">
        </div>
    </div>
    
    <h2>🖥️ フルページ</h2>
    <div class="screenshot">
        <img src="main_page.png" alt="Full page screenshot">
    </div>
    
    <p><small>Generated by Screenshot Manager - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small></p>
</body>
</html>
        """
        
        with open(output_dir / "report.html", 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    async def cleanup(self):
        """リソースのクリーンアップ"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()

async def capture_webapp_async(app_info, config=None, logger=None):
    """非同期でWebアプリのスクリーンショットを撮影"""
    capturer = PlaywrightScreenshotCapture(config, logger)
    return await capturer.capture_webapp_screenshots(app_info)

def capture_webapp_sync(app_info, config=None, logger=None):
    """同期的にWebアプリのスクリーンショットを撮影"""
    if not PLAYWRIGHT_AVAILABLE:
        if logger:
            logger.error("Playwrightがインストールされていません")
        return None
    
    try:
        return asyncio.run(capture_webapp_async(app_info, config, logger))
    except Exception as e:
        if logger:
            logger.error(f"スクリーンショット撮影エラー: {e}")
        return None