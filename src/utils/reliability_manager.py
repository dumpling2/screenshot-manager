#!/usr/bin/env python3
"""
信頼性向上・自動復旧システム - Phase 2.4
システムの安定性確保、障害時自動復旧、ヘルスチェック機能を提供
"""

import asyncio
import time
import signal
import logging
import pickle
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Union, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import threading
import weakref
import atexit
from contextlib import asynccontextmanager

class ComponentStatus(Enum):
    """コンポーネント状態"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    FAILED = "failed"
    UNKNOWN = "unknown"

class RecoveryAction(Enum):
    """復旧アクション"""
    RESTART = "restart"
    RESET = "reset"
    REINITIALIZE = "reinitialize"
    FAILOVER = "failover"
    IGNORE = "ignore"

@dataclass
class ComponentHealth:
    """コンポーネント健全性"""
    name: str
    status: ComponentStatus
    last_check: datetime = field(default_factory=datetime.now)
    last_success: datetime = field(default_factory=datetime.now)
    failure_count: int = 0
    error_message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    recovery_attempts: int = 0
    max_recovery_attempts: int = 3

@dataclass
class SystemState:
    """システム状態"""
    timestamp: datetime = field(default_factory=datetime.now)
    component_states: Dict[str, ComponentHealth] = field(default_factory=dict)
    active_monitors: Set[str] = field(default_factory=set)
    configuration: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)

class HealthChecker:
    """ヘルスチェック機能"""
    
    def __init__(self, component_name: str, check_function: Callable, 
                 check_interval: float = 30.0, timeout: float = 10.0):
        self.component_name = component_name
        self.check_function = check_function
        self.check_interval = check_interval
        self.timeout = timeout
        self.health = ComponentHealth(component_name, ComponentStatus.UNKNOWN)
        self.running = False
        self._task = None
    
    async def start(self):
        """ヘルスチェック開始"""
        if self.running:
            return
        
        self.running = True
        self._task = asyncio.create_task(self._check_loop())
    
    async def stop(self):
        """ヘルスチェック停止"""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
    
    async def _check_loop(self):
        """ヘルスチェックループ"""
        while self.running:
            try:
                await self.perform_check()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.health.error_message = str(e)
                self.health.status = ComponentStatus.FAILED
                await asyncio.sleep(self.check_interval)
    
    async def perform_check(self) -> bool:
        """ヘルスチェック実行"""
        try:
            # タイムアウト付きでチェック関数実行
            if asyncio.iscoroutinefunction(self.check_function):
                result = await asyncio.wait_for(
                    self.check_function(), timeout=self.timeout
                )
            else:
                result = await asyncio.wait_for(
                    asyncio.to_thread(self.check_function), timeout=self.timeout
                )
            
            if result:
                self.health.status = ComponentStatus.HEALTHY
                self.health.last_success = datetime.now()
                self.health.failure_count = 0
                self.health.error_message = ""
            else:
                self._handle_failure("Health check returned False")
            
            self.health.last_check = datetime.now()
            return result
            
        except asyncio.TimeoutError:
            self._handle_failure("Health check timeout")
            return False
        except Exception as e:
            self._handle_failure(str(e))
            return False
    
    def _handle_failure(self, error_message: str):
        """失敗処理"""
        self.health.failure_count += 1
        self.health.error_message = error_message
        
        if self.health.failure_count >= 3:
            self.health.status = ComponentStatus.FAILED
        elif self.health.failure_count >= 2:
            self.health.status = ComponentStatus.UNHEALTHY
        else:
            self.health.status = ComponentStatus.DEGRADED

class AutoRecovery:
    """自動復旧機能"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or self._setup_default_logger()
        self.recovery_strategies: Dict[str, Callable] = {}
        self.recovery_history: List[Dict[str, Any]] = []
        self.max_recovery_attempts = 3
        self.recovery_cooldown = 300  # 5分
        self._last_recovery_times: Dict[str, datetime] = {}
    
    def _setup_default_logger(self) -> logging.Logger:
        """デフォルトロガー設定"""
        logger = logging.getLogger('auto_recovery')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # ファイルハンドラ
            log_dir = Path(__file__).parent.parent.parent / "logs"
            log_dir.mkdir(exist_ok=True)
            
            fh = logging.FileHandler(log_dir / 'recovery.log')
            fh.setLevel(logging.INFO)
            
            # フォーマット
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        
        return logger
    
    def register_recovery_strategy(self, component_name: str, strategy: Callable):
        """復旧戦略登録"""
        self.recovery_strategies[component_name] = strategy
        self.logger.info(f"🔧 復旧戦略登録: {component_name}")
    
    async def attempt_recovery(self, health: ComponentHealth) -> bool:
        """復旧試行"""
        component_name = health.name
        
        # クールダウンチェック
        if not self._can_attempt_recovery(component_name):
            self.logger.warning(
                f"⏰ 復旧クールダウン中: {component_name} "
                f"(残り: {self._get_cooldown_remaining(component_name):.0f}秒)"
            )
            return False
        
        # 最大試行回数チェック
        if health.recovery_attempts >= self.max_recovery_attempts:
            self.logger.error(
                f"❌ 最大復旧試行回数に達しました: {component_name} "
                f"({health.recovery_attempts}/{self.max_recovery_attempts})"
            )
            return False
        
        strategy = self.recovery_strategies.get(component_name)
        if not strategy:
            self.logger.warning(f"⚠️ 復旧戦略が見つかりません: {component_name}")
            return False
        
        health.recovery_attempts += 1
        self._last_recovery_times[component_name] = datetime.now()
        
        self.logger.info(
            f"🔄 復旧試行開始: {component_name} "
            f"({health.recovery_attempts}/{self.max_recovery_attempts})"
        )
        
        recovery_record = {
            "component": component_name,
            "timestamp": datetime.now().isoformat(),
            "attempt": health.recovery_attempts,
            "status": health.status.value,
            "error": health.error_message
        }
        
        try:
            if asyncio.iscoroutinefunction(strategy):
                success = await strategy(health)
            else:
                success = await asyncio.to_thread(strategy, health)
            
            recovery_record["success"] = success
            recovery_record["duration"] = (datetime.now() - datetime.fromisoformat(recovery_record["timestamp"])).total_seconds()
            
            if success:
                self.logger.info(f"✅ 復旧成功: {component_name}")
                health.recovery_attempts = 0  # リセット
            else:
                self.logger.warning(f"❌ 復旧失敗: {component_name}")
            
            return success
            
        except Exception as e:
            recovery_record["success"] = False
            recovery_record["error"] = str(e)
            
            self.logger.error(f"❌ 復旧戦略実行エラー: {component_name} - {e}")
            return False
            
        finally:
            self.recovery_history.append(recovery_record)
    
    def _can_attempt_recovery(self, component_name: str) -> bool:
        """復旧試行可能判定"""
        last_recovery = self._last_recovery_times.get(component_name)
        if not last_recovery:
            return True
        
        return (datetime.now() - last_recovery).total_seconds() > self.recovery_cooldown
    
    def _get_cooldown_remaining(self, component_name: str) -> float:
        """クールダウン残り時間"""
        last_recovery = self._last_recovery_times.get(component_name)
        if not last_recovery:
            return 0
        
        elapsed = (datetime.now() - last_recovery).total_seconds()
        return max(0, self.recovery_cooldown - elapsed)

class StateManager:
    """システム状態管理"""
    
    def __init__(self, state_file: str = "system_state.pickle"):
        self.state_file = Path(__file__).parent.parent.parent / "logs" / state_file
        self.state_file.parent.mkdir(exist_ok=True)
        self.current_state = SystemState()
        self.auto_save_interval = 60  # 1分
        self._save_task = None
        self._lock = threading.RLock()
    
    def save_state(self):
        """状態保存"""
        with self._lock:
            try:
                with open(self.state_file, 'wb') as f:
                    pickle.dump(self.current_state, f)
            except Exception as e:
                logging.error(f"State save error: {e}")
    
    def load_state(self) -> bool:
        """状態読み込み"""
        with self._lock:
            if not self.state_file.exists():
                return False
            
            try:
                with open(self.state_file, 'rb') as f:
                    self.current_state = pickle.load(f)
                return True
            except Exception as e:
                logging.error(f"State load error: {e}")
                return False
    
    def update_component_state(self, health: ComponentHealth):
        """コンポーネント状態更新"""
        with self._lock:
            self.current_state.component_states[health.name] = health
            self.current_state.timestamp = datetime.now()
    
    def get_component_state(self, component_name: str) -> Optional[ComponentHealth]:
        """コンポーネント状態取得"""
        with self._lock:
            return self.current_state.component_states.get(component_name)
    
    async def start_auto_save(self):
        """自動保存開始"""
        if self._save_task:
            return
        
        self._save_task = asyncio.create_task(self._auto_save_loop())
    
    async def stop_auto_save(self):
        """自動保存停止"""
        if self._save_task:
            self._save_task.cancel()
            try:
                await self._save_task
            except asyncio.CancelledError:
                pass
        
        # 最終保存
        self.save_state()
    
    async def _auto_save_loop(self):
        """自動保存ループ"""
        while True:
            try:
                await asyncio.sleep(self.auto_save_interval)
                self.save_state()
            except asyncio.CancelledError:
                break

class ReliabilityManager:
    """信頼性管理メインクラス"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or self._setup_default_logger()
        self.health_checkers: Dict[str, HealthChecker] = {}
        self.auto_recovery = AutoRecovery(logger)
        self.state_manager = StateManager()
        self.running = False
        self.graceful_shutdown_handlers: List[Callable] = []
        self._monitoring_task = None
        
        # シグナルハンドラ設定
        self._setup_signal_handlers()
        atexit.register(self._emergency_shutdown)
    
    def _setup_default_logger(self) -> logging.Logger:
        """デフォルトロガー設定"""
        logger = logging.getLogger('reliability_manager')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # ファイルハンドラ
            log_dir = Path(__file__).parent.parent.parent / "logs"
            log_dir.mkdir(exist_ok=True)
            
            fh = logging.FileHandler(log_dir / 'reliability.log')
            fh.setLevel(logging.INFO)
            
            # コンソールハンドラ
            ch = logging.StreamHandler()
            ch.setLevel(logging.WARNING)
            
            # フォーマット
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            fh.setFormatter(formatter)
            ch.setFormatter(formatter)
            
            logger.addHandler(fh)
            logger.addHandler(ch)
        
        return logger
    
    def _setup_signal_handlers(self):
        """シグナルハンドラ設定"""
        if threading.current_thread() is threading.main_thread():
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """シグナルハンドラ"""
        self.logger.info(f"🛑 シグナル受信: {signum}")
        asyncio.create_task(self.graceful_shutdown())
    
    def register_component(self, component_name: str, 
                          health_check_func: Callable,
                          recovery_strategy: Callable = None,
                          check_interval: float = 30.0) -> HealthChecker:
        """コンポーネント登録"""
        checker = HealthChecker(
            component_name, health_check_func, check_interval
        )
        self.health_checkers[component_name] = checker
        
        if recovery_strategy:
            self.auto_recovery.register_recovery_strategy(
                component_name, recovery_strategy
            )
        
        self.logger.info(f"📋 コンポーネント登録: {component_name}")
        return checker
    
    def add_graceful_shutdown_handler(self, handler: Callable):
        """グレースフル・シャットダウンハンドラ追加"""
        self.graceful_shutdown_handlers.append(handler)
    
    async def start(self):
        """信頼性管理開始"""
        if self.running:
            return
        
        self.running = True
        
        # 状態復元
        if self.state_manager.load_state():
            self.logger.info("💾 システム状態を復元しました")
        
        # ヘルスチェッカー開始
        for checker in self.health_checkers.values():
            await checker.start()
        
        # 状態管理開始
        await self.state_manager.start_auto_save()
        
        # 監視タスク開始
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        self.logger.info("🚀 信頼性管理システム開始")
    
    async def stop(self):
        """信頼性管理停止"""
        if not self.running:
            return
        
        await self.graceful_shutdown()
    
    async def graceful_shutdown(self):
        """グレースフル・シャットダウン"""
        if not self.running:
            return
        
        self.logger.info("🛑 グレースフル・シャットダウン開始")
        
        # シャットダウンハンドラ実行
        for handler in self.graceful_shutdown_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler()
                else:
                    await asyncio.to_thread(handler)
            except Exception as e:
                self.logger.error(f"シャットダウンハンドラエラー: {e}")
        
        self.running = False
        
        # 監視タスク停止
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        # ヘルスチェッカー停止
        for checker in self.health_checkers.values():
            await checker.stop()
        
        # 状態保存
        await self.state_manager.stop_auto_save()
        
        self.logger.info("✅ グレースフル・シャットダウン完了")
    
    def _emergency_shutdown(self):
        """緊急シャットダウン"""
        self.logger.warning("🚨 緊急シャットダウン実行")
        self.state_manager.save_state()
    
    async def _monitoring_loop(self):
        """監視ループ"""
        while self.running:
            try:
                # 各コンポーネントの状態チェック
                for checker in self.health_checkers.values():
                    health = checker.health
                    
                    # 状態更新
                    self.state_manager.update_component_state(health)
                    
                    # 復旧が必要な場合
                    if health.status in [ComponentStatus.UNHEALTHY, ComponentStatus.FAILED]:
                        await self.auto_recovery.attempt_recovery(health)
                
                await asyncio.sleep(10)  # 10秒間隔
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"監視ループエラー: {e}")
                await asyncio.sleep(10)
    
    def get_system_health(self) -> Dict[str, Any]:
        """システム健全性取得"""
        component_statuses = {}
        overall_status = ComponentStatus.HEALTHY
        
        for name, checker in self.health_checkers.items():
            health = checker.health
            component_statuses[name] = {
                "status": health.status.value,
                "last_check": health.last_check.isoformat(),
                "last_success": health.last_success.isoformat(),
                "failure_count": health.failure_count,
                "error_message": health.error_message,
                "recovery_attempts": health.recovery_attempts
            }
            
            # 全体ステータス決定
            if health.status == ComponentStatus.FAILED:
                overall_status = ComponentStatus.FAILED
            elif health.status == ComponentStatus.UNHEALTHY and overall_status != ComponentStatus.FAILED:
                overall_status = ComponentStatus.UNHEALTHY
            elif health.status == ComponentStatus.DEGRADED and overall_status == ComponentStatus.HEALTHY:
                overall_status = ComponentStatus.DEGRADED
        
        return {
            "overall_status": overall_status.value,
            "components": component_statuses,
            "recovery_history": self.auto_recovery.recovery_history[-10:],  # 最新10件
            "system_uptime": (datetime.now() - self.state_manager.current_state.timestamp).total_seconds(),
            "running": self.running
        }

# グローバル信頼性マネージャ
_global_reliability_manager = None

def get_global_reliability_manager() -> ReliabilityManager:
    """グローバル信頼性マネージャ取得"""
    global _global_reliability_manager
    if _global_reliability_manager is None:
        _global_reliability_manager = ReliabilityManager()
    return _global_reliability_manager

# 便利関数
@asynccontextmanager
async def reliable_operation(component_name: str = "operation"):
    """信頼性のある操作のコンテキストマネージャ"""
    manager = get_global_reliability_manager()
    
    try:
        yield manager
    except Exception as e:
        manager.logger.error(f"操作エラー: {component_name} - {e}")
        raise
    finally:
        # クリーンアップ処理
        pass

# テスト関数
async def test_reliability_manager():
    """信頼性マネージャテスト"""
    manager = ReliabilityManager()
    
    # テスト用ヘルスチェック
    async def test_health_check():
        return True
    
    async def test_recovery(health):
        return True
    
    # コンポーネント登録
    manager.register_component(
        "test_component",
        test_health_check,
        test_recovery,
        check_interval=5.0
    )
    
    # 開始
    await manager.start()
    
    # 少し待機
    await asyncio.sleep(10)
    
    # 健全性確認
    health = manager.get_system_health()
    print(json.dumps(health, indent=2, ensure_ascii=False))
    
    # 停止
    await manager.stop()

if __name__ == "__main__":
    asyncio.run(test_reliability_manager())