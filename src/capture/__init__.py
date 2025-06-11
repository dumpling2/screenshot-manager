"""
スクリーンショット撮影・キャプチャモジュール

- playwright_capture: ブラウザ自動化による高度スクリーンショット
"""

from .playwright_capture import PlaywrightScreenshotCapture, capture_webapp_sync

__all__ = ['PlaywrightScreenshotCapture', 'capture_webapp_sync']