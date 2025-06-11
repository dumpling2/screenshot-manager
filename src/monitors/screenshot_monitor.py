#!/usr/bin/env python3

import os
import json
import time
import shutil
import hashlib
import logging
from pathlib import Path
from datetime import datetime
import threading
import signal
import sys

class ScreenshotMonitor:
    def __init__(self, config_path='config/config.json'):
        self.config_path = Path(__file__).parent / config_path
        self.setup_logging()
        self.load_config()
        self.processed_files = {}
        self.running = True
        
    def load_config(self):
        """設定ファイルを読み込む"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            # 設定ファイルが存在しない場合はエラー
            self.logger.error(f"設定ファイルが見つかりません: {self.config_path}")
            self.logger.error("初回セットアップを実行してください: ./setup.sh")
            sys.exit(1)
            
        # Windows パスの展開
        self.windows_screenshot_path = Path(
            self.config['windowsScreenshotPath'].format(
                username=self.config['windowsUsername']
            )
        )
        self.local_screenshot_path = Path(__file__).parent / self.config['localScreenshotPath']
        
    def save_config(self):
        """設定ファイルを保存"""
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
            
    def setup_logging(self):
        """ログ設定"""
        log_dir = Path(__file__).parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'monitor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def get_file_hash(self, file_path):
        """ファイルのMD5ハッシュを計算"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            self.logger.error(f"Error calculating hash for {file_path}: {e}")
            return None
            
    def is_valid_screenshot(self, file_path):
        """有効なスクリーンショットファイルかチェック"""
        file_path = Path(file_path)
        
        # パターンマッチング
        matched = False
        for pattern in self.config['filePattern']:
            if file_path.match(pattern):
                matched = True
                break
                
        if not matched:
            return False
            
        # ファイルサイズチェック
        try:
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            if file_size_mb > self.config['maxFileSizeMB']:
                self.logger.warning(f"File too large: {file_path} ({file_size_mb:.2f}MB)")
                return False
        except Exception as e:
            self.logger.error(f"Error checking file size for {file_path}: {e}")
            return False
            
        return True
        
    def get_target_path(self, source_file):
        """転送先のパスを生成"""
        source_path = Path(source_file)
        
        if self.config['organizeByDate']:
            # ファイルの更新日時を取得
            file_time = os.path.getmtime(source_file)
            date_str = datetime.fromtimestamp(file_time).strftime(self.config['dateFormat'])
            target_dir = self.local_screenshot_path / date_str
        else:
            target_dir = self.local_screenshot_path
            
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # タイムスタンプ付きのファイル名を生成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name_parts = source_path.stem.split('_')
        
        # すでにタイムスタンプが付いている場合はそのまま使用
        if len(name_parts) > 1 and name_parts[-1].isdigit() and len(name_parts[-1]) >= 8:
            target_name = source_path.name
        else:
            target_name = f"{source_path.stem}_{timestamp}{source_path.suffix}"
            
        return target_dir / target_name
        
    def copy_screenshot(self, source_path):
        """スクリーンショットをコピー"""
        try:
            target_path = self.get_target_path(source_path)
            
            # 同名ファイルが存在する場合
            if target_path.exists():
                source_hash = self.get_file_hash(source_path)
                target_hash = self.get_file_hash(target_path)
                
                if source_hash == target_hash:
                    self.logger.info(f"Duplicate file skipped: {source_path}")
                    return True
                else:
                    # 番号を付けて別名で保存
                    counter = 1
                    base_path = target_path
                    while target_path.exists():
                        target_path = base_path.parent / f"{base_path.stem}_{counter}{base_path.suffix}"
                        counter += 1
                        
            # ファイルをコピー
            shutil.copy2(source_path, target_path)
            self.logger.info(f"Copied: {source_path} -> {target_path}")
            
            # 転送ログを記録
            self.log_transfer(source_path, target_path, success=True)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error copying {source_path}: {e}")
            self.log_transfer(source_path, None, success=False, error=str(e))
            return False
            
    def log_transfer(self, source, destination, success, error=None):
        """転送ログを記録"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "source": str(source),
            "destination": str(destination) if destination else None,
            "success": success,
            "error": error
        }
        
        log_file = Path(__file__).parent / 'logs' / 'transfers.jsonl'
        with open(log_file, 'a') as f:
            json.dump(log_entry, f)
            f.write('\n')
            
    def scan_and_copy(self):
        """スクリーンショットフォルダをスキャンして新しいファイルをコピー"""
        if not self.windows_screenshot_path.exists():
            self.logger.warning(f"Screenshot folder not found: {self.windows_screenshot_path}")
            return
            
        try:
            # 最近のファイルのみチェック（過去5分以内）
            current_time = time.time()
            cutoff_time = current_time - (5 * 60)
            
            for file_path in self.windows_screenshot_path.iterdir():
                if not file_path.is_file():
                    continue
                    
                if not self.is_valid_screenshot(file_path):
                    continue
                    
                # 古いファイルはスキップ
                if os.path.getmtime(file_path) < cutoff_time:
                    continue
                    
                # ハッシュ値で処理済みチェック
                file_hash = self.get_file_hash(file_path)
                if file_hash and file_hash not in self.processed_files:
                    if self.copy_screenshot(file_path):
                        self.processed_files[file_hash] = True
                        
                        # メモリ節約のため古いエントリを削除
                        if len(self.processed_files) > 100:
                            # 最も古い50個を削除
                            keys_to_remove = list(self.processed_files.keys())[:50]
                            for key in keys_to_remove:
                                del self.processed_files[key]
                                
        except Exception as e:
            self.logger.error(f"Error during scan: {e}")
            
    def cleanup_old_files(self):
        """古いファイルを削除"""
        if not self.config['autoCleanup']['enabled']:
            return
            
        from datetime import timedelta
        
        days_to_keep = self.config['autoCleanup']['daysToKeep']
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        deleted_count = 0
        
        for root, dirs, files in os.walk(self.local_screenshot_path):
            for file in files:
                file_path = Path(root) / file
                if file_path.is_file():
                    try:
                        file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                        if file_time < cutoff_date:
                            file_path.unlink()
                            self.logger.info(f"Deleted old file: {file_path}")
                            deleted_count += 1
                    except Exception as e:
                        self.logger.error(f"Error deleting {file_path}: {e}")
                        
        # 空のディレクトリを削除
        for root, dirs, files in os.walk(self.local_screenshot_path, topdown=False):
            for dir_name in dirs:
                dir_path = Path(root) / dir_name
                try:
                    if not any(dir_path.iterdir()):
                        dir_path.rmdir()
                        self.logger.info(f"Removed empty directory: {dir_path}")
                except Exception as e:
                    self.logger.error(f"Error removing directory {dir_path}: {e}")
                    
        if deleted_count > 0:
            self.logger.info(f"Deleted {deleted_count} old files")
            
    def run(self):
        """メインループ"""
        self.logger.info("Screenshot Monitor started")
        self.logger.info(f"Watching: {self.windows_screenshot_path}")
        self.logger.info(f"Destination: {self.local_screenshot_path}")
        
        # クリーンアップスレッド
        def cleanup_worker():
            while self.running:
                self.cleanup_old_files()
                # 1日に1回実行
                time.sleep(86400)
                
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
        
        # メインループ
        while self.running:
            self.scan_and_copy()
            time.sleep(self.config['checkInterval'])
            
    def stop(self):
        """監視を停止"""
        self.running = False
        self.logger.info("Screenshot Monitor stopped")


def signal_handler(signum, frame):
    """シグナルハンドラー"""
    print("\nStopping monitor...")
    monitor.stop()
    sys.exit(0)


if __name__ == '__main__':
    # シグナルハンドラーの設定
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # モニター起動
    monitor = ScreenshotMonitor()
    monitor.run()