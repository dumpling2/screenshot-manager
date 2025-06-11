#!/usr/bin/env python3
"""
プロジェクト自動検出機能
Claude Codeで作成されたプロジェクトの種類を自動判定し、適切な監視設定を提案
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class ProjectInfo:
    """検出されたプロジェクトの情報"""
    path: Path
    name: str
    framework: str
    language: str
    package_manager: str = ""
    dev_command: str = ""
    build_command: str = ""
    default_port: int = 0
    entry_point: str = ""
    dependencies: List[str] = None
    detected_at: str = ""
    confidence: float = 0.0
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if not self.detected_at:
            self.detected_at = datetime.now().isoformat()

class ProjectDetector:
    """プロジェクト種別の自動検出"""
    
    # フレームワーク検出パターン
    FRAMEWORK_PATTERNS = {
        # React プロジェクト
        'React': {
            'files': ['package.json'],
            'dependencies': ['react', 'react-dom'],
            'dev_dependencies': ['react-scripts', '@vitejs/plugin-react'],
            'scripts': ['start', 'dev'],
            'default_port': 3000,
            'confidence_base': 0.9
        },
        
        # Vue.js プロジェクト  
        'Vue': {
            'files': ['package.json'],
            'dependencies': ['vue'],
            'dev_dependencies': ['@vue/cli-service', 'vite', '@vitejs/plugin-vue'],
            'scripts': ['serve', 'dev'],
            'default_port': 3000,
            'confidence_base': 0.9
        },
        
        # Angular プロジェクト
        'Angular': {
            'files': ['package.json', 'angular.json'],
            'dependencies': ['@angular/core', '@angular/common'],
            'dev_dependencies': ['@angular/cli'],
            'scripts': ['start', 'serve'],
            'default_port': 4200,
            'confidence_base': 0.95
        },
        
        # Next.js プロジェクト
        'Next.js': {
            'files': ['package.json'],
            'dependencies': ['next', 'react'],
            'dev_dependencies': [],
            'scripts': ['dev', 'start'],
            'default_port': 3000,
            'confidence_base': 0.9
        },
        
        # Django プロジェクト
        'Django': {
            'files': ['manage.py', 'requirements.txt'],
            'dependencies': ['Django'],
            'patterns': ['*/settings.py', '*/wsgi.py'],
            'default_port': 8000,
            'confidence_base': 0.9
        },
        
        # Flask プロジェクト
        'Flask': {
            'files': ['app.py', 'requirements.txt'],
            'dependencies': ['Flask'],
            'patterns': ['app.py', 'main.py', 'run.py'],
            'default_port': 5000,
            'confidence_base': 0.8
        },
        
        # Express.js プロジェクト
        'Express': {
            'files': ['package.json'],
            'dependencies': ['express'],
            'patterns': ['server.js', 'app.js', 'index.js'],
            'default_port': 3000,
            'confidence_base': 0.8
        },
        
        # Vite プロジェクト（フレームワーク非依存）
        'Vite': {
            'files': ['package.json', 'vite.config.js', 'vite.config.ts'],
            'dependencies': ['vite'],
            'scripts': ['dev', 'serve'],
            'default_port': 5173,
            'confidence_base': 0.7
        }
    }
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        
    def detect_project(self, project_path: Path) -> Optional[ProjectInfo]:
        """プロジェクトを検出・分析"""
        if not project_path.exists() or not project_path.is_dir():
            return None
            
        self.logger.info(f"🔍 プロジェクト検出開始: {project_path}")
        
        # 基本情報
        project_name = project_path.name
        
        # フレームワーク検出
        framework_results = self._detect_frameworks(project_path)
        if not framework_results:
            self.logger.debug(f"フレームワークが検出されませんでした: {project_path}")
            return None
            
        # 最も信頼度の高いフレームワークを選択
        best_match = max(framework_results, key=lambda x: x['confidence'])
        
        # 詳細情報を収集
        project_info = ProjectInfo(
            path=project_path,
            name=project_name,
            framework=best_match['framework'],
            language=self._detect_language(project_path),
            package_manager=self._detect_package_manager(project_path),
            dev_command=best_match.get('dev_command', ''),
            build_command=best_match.get('build_command', ''),
            default_port=best_match.get('default_port', 0),
            entry_point=best_match.get('entry_point', ''),
            dependencies=best_match.get('dependencies', []),
            confidence=best_match['confidence']
        )
        
        self.logger.info(f"✅ プロジェクト検出完了: {project_info.framework} (信頼度: {project_info.confidence:.2f})")
        return project_info
    
    def _detect_frameworks(self, project_path: Path) -> List[Dict]:
        """フレームワークを検出"""
        results = []
        
        for framework, pattern in self.FRAMEWORK_PATTERNS.items():
            confidence = self._calculate_framework_confidence(project_path, framework, pattern)
            if confidence > 0.3:  # 閾値以上の場合のみ候補として追加
                result = {
                    'framework': framework,
                    'confidence': confidence,
                    'default_port': pattern.get('default_port', 3000)
                }
                
                # 開発コマンドを推定
                result['dev_command'] = self._detect_dev_command(project_path, pattern)
                result['build_command'] = self._detect_build_command(project_path, pattern)
                result['entry_point'] = self._detect_entry_point(project_path, pattern)
                result['dependencies'] = self._extract_dependencies(project_path, pattern)
                
                results.append(result)
        
        return results
    
    def _calculate_framework_confidence(self, project_path: Path, framework: str, pattern: Dict) -> float:
        """フレームワーク検出の信頼度を計算"""
        confidence = 0.0
        base_confidence = pattern.get('confidence_base', 0.5)
        
        # 必須ファイルの存在確認
        required_files = pattern.get('files', [])
        file_score = 0.0
        for file_name in required_files:
            if (project_path / file_name).exists():
                file_score += 1.0
        
        if required_files:
            file_score = file_score / len(required_files)
            confidence += file_score * 0.4
        
        # package.json の依存関係確認（Node.js系）
        if (project_path / 'package.json').exists():
            package_score = self._check_package_dependencies(project_path, pattern)
            confidence += package_score * 0.4
        
        # requirements.txt の依存関係確認（Python系）
        if (project_path / 'requirements.txt').exists():
            requirements_score = self._check_requirements_dependencies(project_path, pattern)
            confidence += requirements_score * 0.4
        
        # パターンファイルの存在確認
        if 'patterns' in pattern:
            pattern_score = self._check_file_patterns(project_path, pattern['patterns'])
            confidence += pattern_score * 0.2
        
        # ベース信頼度を適用
        confidence = confidence * base_confidence
        
        return min(confidence, 1.0)
    
    def _check_package_dependencies(self, project_path: Path, pattern: Dict) -> float:
        """package.json の依存関係をチェック"""
        try:
            with open(project_path / 'package.json', 'r') as f:
                package_data = json.load(f)
            
            dependencies = package_data.get('dependencies', {})
            dev_dependencies = package_data.get('devDependencies', {})
            all_deps = {**dependencies, **dev_dependencies}
            
            # 必要な依存関係の存在確認
            required_deps = pattern.get('dependencies', [])
            dev_deps = pattern.get('dev_dependencies', [])
            
            score = 0.0
            total_checks = len(required_deps) + len(dev_deps)
            
            if total_checks == 0:
                return 0.0
            
            for dep in required_deps:
                if dep in all_deps:
                    score += 1.0
            
            for dep in dev_deps:
                if dep in all_deps:
                    score += 1.0
            
            return score / total_checks
            
        except Exception as e:
            self.logger.debug(f"package.json 読み込みエラー: {e}")
            return 0.0
    
    def _check_requirements_dependencies(self, project_path: Path, pattern: Dict) -> float:
        """requirements.txt の依存関係をチェック"""
        try:
            with open(project_path / 'requirements.txt', 'r') as f:
                requirements = f.read().lower()
            
            required_deps = pattern.get('dependencies', [])
            if not required_deps:
                return 0.0
            
            score = 0.0
            for dep in required_deps:
                if dep.lower() in requirements:
                    score += 1.0
            
            return score / len(required_deps)
            
        except Exception as e:
            self.logger.debug(f"requirements.txt 読み込みエラー: {e}")
            return 0.0
    
    def _check_file_patterns(self, project_path: Path, patterns: List[str]) -> float:
        """ファイルパターンの存在確認"""
        score = 0.0
        for pattern in patterns:
            if list(project_path.glob(pattern)):
                score += 1.0
        
        return score / len(patterns) if patterns else 0.0
    
    def _detect_language(self, project_path: Path) -> str:
        """プログラミング言語を検出"""
        if (project_path / 'package.json').exists():
            return 'JavaScript'
        elif (project_path / 'requirements.txt').exists() or (project_path / 'pyproject.toml').exists():
            return 'Python'
        elif (project_path / 'composer.json').exists():
            return 'PHP'
        elif (project_path / 'Gemfile').exists():
            return 'Ruby'
        elif (project_path / 'go.mod').exists():
            return 'Go'
        else:
            return 'Unknown'
    
    def _detect_package_manager(self, project_path: Path) -> str:
        """パッケージマネージャーを検出"""
        if (project_path / 'yarn.lock').exists():
            return 'yarn'
        elif (project_path / 'package-lock.json').exists():
            return 'npm'
        elif (project_path / 'pnpm-lock.yaml').exists():
            return 'pnpm'
        elif (project_path / 'requirements.txt').exists():
            return 'pip'
        elif (project_path / 'Pipfile').exists():
            return 'pipenv'
        else:
            return 'unknown'
    
    def _detect_dev_command(self, project_path: Path, pattern: Dict) -> str:
        """開発コマンドを検出"""
        if (project_path / 'package.json').exists():
            try:
                with open(project_path / 'package.json', 'r') as f:
                    package_data = json.load(f)
                
                scripts = package_data.get('scripts', {})
                preferred_scripts = pattern.get('scripts', ['dev', 'start', 'serve'])
                
                for script in preferred_scripts:
                    if script in scripts:
                        return f"npm run {script}"
                
                return "npm start"  # デフォルト
                
            except Exception:
                pass
        
        return ""
    
    def _detect_build_command(self, project_path: Path, pattern: Dict) -> str:
        """ビルドコマンドを検出"""
        if (project_path / 'package.json').exists():
            try:
                with open(project_path / 'package.json', 'r') as f:
                    package_data = json.load(f)
                
                scripts = package_data.get('scripts', {})
                if 'build' in scripts:
                    return "npm run build"
                
            except Exception:
                pass
        
        return ""
    
    def _detect_entry_point(self, project_path: Path, pattern: Dict) -> str:
        """エントリーポイントを検出"""
        common_entries = ['index.js', 'app.js', 'server.js', 'main.js', 'src/index.js', 'src/main.js']
        
        for entry in common_entries:
            if (project_path / entry).exists():
                return entry
        
        return ""
    
    def _extract_dependencies(self, project_path: Path, pattern: Dict) -> List[str]:
        """依存関係を抽出"""
        dependencies = []
        
        if (project_path / 'package.json').exists():
            try:
                with open(project_path / 'package.json', 'r') as f:
                    package_data = json.load(f)
                
                deps = package_data.get('dependencies', {})
                dev_deps = package_data.get('devDependencies', {})
                
                # 主要な依存関係のみ抽出（フレームワーク関連）
                important_deps = pattern.get('dependencies', []) + pattern.get('dev_dependencies', [])
                for dep in important_deps:
                    if dep in deps or dep in dev_deps:
                        dependencies.append(dep)
                
            except Exception:
                pass
        
        return dependencies
    
    def scan_directory(self, base_path: Path, max_depth: int = 2) -> List[ProjectInfo]:
        """ディレクトリを再帰的にスキャンしてプロジェクトを検出"""
        projects = []
        
        def _scan_recursive(path: Path, current_depth: int):
            if current_depth > max_depth:
                return
            
            if not path.is_dir():
                return
            
            # 現在のディレクトリでプロジェクト検出を試行
            project_info = self.detect_project(path)
            if project_info:
                projects.append(project_info)
                return  # プロジェクトが見つかったら、そのサブディレクトリはスキップ
            
            # サブディレクトリを探索
            try:
                for sub_path in path.iterdir():
                    if sub_path.is_dir() and not sub_path.name.startswith('.'):
                        _scan_recursive(sub_path, current_depth + 1)
            except PermissionError:
                self.logger.debug(f"Permission denied: {path}")
        
        _scan_recursive(base_path, 0)
        return projects

def main():
    """テスト実行"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    detector = ProjectDetector()
    
    # 現在のディレクトリからプロジェクトを検出
    current_dir = Path.cwd()
    project_info = detector.detect_project(current_dir)
    
    if project_info:
        print("🎯 プロジェクト検出結果:")
        print(json.dumps(asdict(project_info), indent=2, ensure_ascii=False, default=str))
    else:
        print("❌ プロジェクトが検出されませんでした")

if __name__ == "__main__":
    main()