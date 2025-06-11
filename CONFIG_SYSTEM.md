# 設定システム設計書

## 概要
複数プロジェクトでの並行利用を可能にする、柔軟で拡張可能な設定管理システムの設計。

## 設計原則

### 1. 設定の優先順位
1. **環境変数** (最高優先度)
2. **プロジェクト固有設定ファイル** 
3. **ユーザーグローバル設定**
4. **システムデフォルト設定**

### 2. 設定の継承・オーバーライド
- 基本設定を継承しつつ、プロジェクト固有の設定で上書きを可能にする
- 設定項目の部分的な変更を許可

## 設定ファイル構造

### 1. システムデフォルト設定
```yaml
# screenshot_lib/defaults.yaml
system:
  version: "2.0.0"
  platform: "wsl"

capture:
  save_path: "./screenshots"
  filename_format: "{app}_{timestamp}"
  timestamp_format: "%Y%m%d_%H%M%S"
  formats: ["PNG"]
  
monitor:
  check_interval: 2.0
  file_patterns: ["*.png", "*.jpg", "*.jpeg"]
  
organization:
  by_date: true
  date_format: "%Y-%m-%d"
  
cleanup:
  enabled: true
  days_to_keep: 7
  
windows:
  default_screenshot_path: "/mnt/c/Users/{username}/Pictures/Screenshots"
  
metadata:
  include_window_info: true
  include_system_info: true
  include_timestamp: true

ai_integration:
  enabled: false
  auto_analysis: false
```

### 2. ユーザーグローバル設定
```yaml
# ~/.screenshot_manager/config.yaml
user:
  name: "mikanu"
  
windows:
  username: "YourWindowsUsername"
  screenshot_path: "/mnt/c/Users/{username}/Pictures/Screenshots"
  
capture:
  save_path: "~/screenshots"
  default_format: "PNG"
  
ai_integration:
  enabled: true
  default_provider: "anthropic"
  providers:
    anthropic:
      api_key: "${ANTHROPIC_API_KEY}"
      model: "claude-3-sonnet-20240229"
```

### 3. プロジェクト固有設定
```yaml
# ./screenshot_config.yaml (プロジェクトルートに配置)
project:
  name: "AI Development Project"
  description: "AI画面分析プロジェクト"
  
# 基本設定をオーバーライド
capture:
  save_path: "./ai_screenshots"
  filename_format: "{project}_{app}_{timestamp}"
  formats: ["PNG", "JPEG"]
  
# プロジェクト固有の設定
ai_integration:
  enabled: true
  auto_analysis: true
  analysis_prompt: "この画面での開発作業を分析してください"
  
metadata:
  custom_fields:
    project_phase: "development"
    team: "AI研究チーム"
    
# フィルタリング設定
filters:
  include_apps: ["Code", "Chrome", "Terminal"]
  exclude_apps: ["Discord", "Slack"]
  
# 通知設定
notifications:
  enabled: true
  webhook_url: "https://hooks.slack.com/..."
```

## 環境変数での設定

### 基本的な環境変数
```bash
# 基本設定
export SCREENSHOT_SAVE_PATH="./my_screenshots"
export SCREENSHOT_FORMAT="JPEG"
export SCREENSHOT_QUALITY=90

# Windows関連
export WINDOWS_USERNAME="YourWindowsUser"
export WINDOWS_SCREENSHOT_PATH="/mnt/c/Users/$WINDOWS_USERNAME/Pictures/Screenshots"

# AI連携
export ANTHROPIC_API_KEY="your-api-key"
export OPENAI_API_KEY="your-openai-key"
export AI_ANALYSIS_ENABLED=true

# プロジェクト識別
export SCREENSHOT_PROJECT_ID="ai_development_2024"
export SCREENSHOT_CONFIG_PATH="./config/screenshot.yaml"
```

### 複数プロジェクト管理
```bash
# プロジェクトA用の設定
export SCREENSHOT_PROJECT_A_SAVE_PATH="./project_a/screenshots"
export SCREENSHOT_PROJECT_A_AI_PROMPT="Analyze development work for Project A"

# プロジェクトB用の設定
export SCREENSHOT_PROJECT_B_SAVE_PATH="./project_b/screenshots"
export SCREENSHOT_PROJECT_B_AI_PROMPT="Analyze UI design work for Project B"
```

## 設定管理クラス設計

### ConfigManager実装
```python
# screenshot_lib/config.py
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigManager:
    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self._config = {}
        self._load_all_configs()
    
    def _load_all_configs(self):
        """全ての設定を優先順位に従って読み込み"""
        # 1. システムデフォルト
        self._config = self._load_default_config()
        
        # 2. ユーザーグローバル設定
        user_config = self._load_user_config()
        self._merge_config(user_config)
        
        # 3. プロジェクト固有設定
        project_config = self._load_project_config()
        self._merge_config(project_config)
        
        # 4. 環境変数での上書き
        self._apply_environment_overrides()
    
    def get(self, key: str, default: Any = None) -> Any:
        """設定値の取得（ドット記法対応）"""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set_project_override(self, key: str, value: Any):
        """プロジェクト固有の設定を一時的に上書き"""
        keys = key.split('.')
        target = self._config
        
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        
        target[keys[-1]] = value
```

### 使用例
```python
# 基本利用
from screenshot_lib import ConfigManager, ScreenshotCapture

config = ConfigManager()
capture = ScreenshotCapture(config=config)

# プロジェクト固有設定での利用
config = ConfigManager(project_root="./my_ai_project")
save_path = config.get('capture.save_path')  # "./my_ai_project/screenshots"

# 設定の動的変更
config.set_project_override('ai_integration.enabled', True)
```

## プロジェクト別の設定例

### Web開発プロジェクト
```yaml
# web_project/screenshot_config.yaml
project:
  name: "Web Development"
  type: "frontend"

capture:
  save_path: "./design_screenshots"
  filename_format: "{page}_{viewport}_{timestamp}"
  
filters:
  include_apps: ["Chrome", "Firefox", "Safari"]
  min_window_size: [800, 600]
  
ai_integration:
  analysis_prompt: "このWebページのUI/UXを分析してください"
  custom_fields:
    page_type: "unknown"
    design_stage: "development"
```

### データ分析プロジェクト
```yaml  
# data_project/screenshot_config.yaml
project:
  name: "Data Analysis"
  type: "research"

capture:
  save_path: "./analysis_screenshots"
  filename_format: "analysis_{dataset}_{timestamp}"
  
filters:
  include_apps: ["JupyterLab", "RStudio", "Tableau"]
  
ai_integration:
  analysis_prompt: "このデータ分析の内容を要約してください"
  auto_analysis: true
  schedule:
    interval: 3600  # 1時間ごと
    active_hours: [9, 18]  # 9:00-18:00のみ
```

## 設定の検証とバリデーション

### 設定検証機能
```python
class ConfigValidator:
    def __init__(self, config: ConfigManager):
        self.config = config
    
    def validate(self) -> Dict[str, List[str]]:
        """設定の妥当性チェック"""
        errors = {}
        
        # 必須項目のチェック
        required_fields = [
            'windows.username',
            'capture.save_path'
        ]
        
        for field in required_fields:
            if not self.config.get(field):
                errors.setdefault('missing', []).append(field)
        
        # パスの存在チェック
        windows_path = self.config.get('windows.screenshot_path')
        if windows_path and not Path(windows_path).exists():
            errors.setdefault('invalid_path', []).append(windows_path)
        
        # AI設定のチェック
        if self.config.get('ai_integration.enabled'):
            api_key = self.config.get('ai_integration.providers.anthropic.api_key')
            if not api_key or api_key.startswith('${'):
                errors.setdefault('missing_api_key', []).append('anthropic')
        
        return errors
```

## 設定移行・アップグレード

### 設定マイグレーション
```python
class ConfigMigrator:
    def __init__(self):
        self.migrations = [
            self._migrate_v1_to_v2,
            self._migrate_v2_to_v3
        ]
    
    def migrate_config(self, config_path: Path) -> bool:
        """古い設定ファイルを新しい形式に移行"""
        # バックアップ作成
        backup_path = config_path.with_suffix('.yaml.backup')
        shutil.copy2(config_path, backup_path)
        
        # マイグレーション実行
        for migration in self.migrations:
            try:
                migration(config_path)
            except Exception as e:
                # 失敗時はバックアップから復元
                shutil.copy2(backup_path, config_path)
                raise e
        
        return True
```

## CLIでの設定管理

### 設定管理コマンド
```bash
# 現在の設定を表示
./screenshot_manager.sh config show

# 設定を対話的に変更
./screenshot_manager.sh config setup

# プロジェクト固有設定の初期化
./screenshot_manager.sh config init --project-name "My AI Project"

# 設定の妥当性チェック
./screenshot_manager.sh config validate

# 設定のリセット
./screenshot_manager.sh config reset --scope user|project|all
```

---
*設計完了: 2025-06-11*