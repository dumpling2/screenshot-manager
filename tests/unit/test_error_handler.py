import pytest
import asyncio
from unittest.mock import Mock, patch
from src.utils.error_handler import (
    ErrorHandler, ErrorCategory, ErrorSeverity, 
    handle_errors, get_global_error_handler
)


class TestErrorHandler:
    """エラーハンドラーのテストクラス"""
    
    def setup_method(self):
        """テストメソッド前の準備"""
        self.error_handler = ErrorHandler()
    
    def test_error_handler_initialization(self):
        """エラーハンドラーの初期化テスト"""
        assert self.error_handler.total_errors == 0
        assert self.error_handler.resolved_errors == 0
        assert len(self.error_handler.error_history) == 0
    
    def test_record_error(self):
        """エラー記録のテスト"""
        error = Exception("テストエラー")
        context = {"test": "context"}
        
        self.error_handler.record_error(
            error, ErrorCategory.NETWORK, ErrorSeverity.HIGH, context
        )
        
        assert self.error_handler.total_errors == 1
        assert len(self.error_handler.error_history) == 1
        
        recorded_error = self.error_handler.error_history[0]
        assert recorded_error.category == ErrorCategory.NETWORK
        assert recorded_error.severity == ErrorSeverity.HIGH
        assert recorded_error.context == context
    
    def test_resolve_error(self):
        """エラー解決のテスト"""
        error = Exception("テストエラー")
        self.error_handler.record_error(
            error, ErrorCategory.FILESYSTEM, ErrorSeverity.MEDIUM
        )
        
        error_id = self.error_handler.error_history[0].id
        self.error_handler.resolve_error(error_id)
        
        assert self.error_handler.resolved_errors == 1
        assert self.error_handler.error_history[0].resolved is True
    
    def test_get_error_statistics(self):
        """エラー統計のテスト"""
        # 複数のエラーを記録
        for i in range(3):
            error = Exception(f"テストエラー{i}")
            category = ErrorCategory.SCREENSHOT if i % 2 == 0 else ErrorCategory.MCP
            severity = ErrorSeverity.HIGH if i < 2 else ErrorSeverity.LOW
            self.error_handler.record_error(error, category, severity)
        
        # 1つのエラーを解決
        first_error_id = self.error_handler.error_history[0].id
        self.error_handler.resolve_error(first_error_id)
        
        stats = self.error_handler.get_error_statistics()
        
        assert stats['total_errors'] == 3
        assert stats['resolved_errors'] == 1
        assert stats['error_categories']['screenshot'] == 2
        assert stats['error_categories']['mcp'] == 1
        assert stats['severity_distribution']['high'] == 2
        assert stats['severity_distribution']['low'] == 1


class TestErrorDecorator:
    """エラーハンドリングデコレータのテストクラス"""
    
    def test_sync_function_decorator(self):
        """同期関数デコレータのテスト"""
        @handle_errors(ErrorCategory.NETWORK, ErrorSeverity.MEDIUM)
        def failing_function():
            raise ConnectionError("ネットワークエラー")
        
        with pytest.raises(ConnectionError):
            failing_function()
        
        # グローバルハンドラーでエラーが記録されているか確認
        global_handler = get_global_error_handler()
        assert global_handler.total_errors >= 1
    
    @pytest.mark.asyncio
    async def test_async_function_decorator(self):
        """非同期関数デコレータのテスト"""
        @handle_errors(ErrorCategory.FILESYSTEM, ErrorSeverity.HIGH)
        async def failing_async_function():
            await asyncio.sleep(0.01)
            raise FileNotFoundError("ファイルが見つかりません")
        
        with pytest.raises(FileNotFoundError):
            await failing_async_function()
        
        # グローバルハンドラーでエラーが記録されているか確認
        global_handler = get_global_error_handler()
        assert global_handler.total_errors >= 1
    
    def test_decorator_with_retry(self):
        """リトライ機能付きデコレータのテスト"""
        call_count = 0
        
        @handle_errors(ErrorCategory.NETWORK, ErrorSeverity.LOW, auto_retry=True, max_retries=2)
        def sometimes_failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("一時的なネットワークエラー")
            return "成功"
        
        result = sometimes_failing_function()
        assert result == "成功"
        assert call_count == 2


class TestGlobalErrorHandler:
    """グローバルエラーハンドラーのテストクラス"""
    
    def test_global_error_handler_singleton(self):
        """グローバルエラーハンドラーのシングルトンテスト"""
        handler1 = get_global_error_handler()
        handler2 = get_global_error_handler()
        
        assert handler1 is handler2
    
    def test_global_error_recording(self):
        """グローバルエラー記録のテスト"""
        initial_count = get_global_error_handler().total_errors
        
        @handle_errors(ErrorCategory.PLAYWRIGHT, ErrorSeverity.CRITICAL)
        def critical_error_function():
            raise RuntimeError("重大なエラー")
        
        with pytest.raises(RuntimeError):
            critical_error_function()
        
        assert get_global_error_handler().total_errors > initial_count


if __name__ == "__main__":
    pytest.main([__file__, "-v"])