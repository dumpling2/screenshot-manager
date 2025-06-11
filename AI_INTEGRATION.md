# AI連携機能設計書

## 概要
AI画面確認システムとして、スクリーンショットの撮影から分析、結果管理までを統合的に行う機能拡張の設計書。

## Phase 2: AI連携機能の詳細設計

### 1. 画像前処理機能

#### 1.1 AI用画像最適化
```python
from screenshot_lib import ScreenshotCapture

# AI分析用の最適化された撮影
capture = ScreenshotCapture(ai_mode=True)
result = capture.capture_for_ai(
    # 解像度の最適化
    target_resolution=(1024, 768),
    # 品質とファイルサイズのバランス
    quality=85,
    # フォーマット指定
    format='JPEG',
    # 前処理オプション
    preprocessing={
        'normalize_brightness': True,
        'enhance_contrast': True,
        'remove_noise': False
    }
)
```

#### 1.2 マルチフォーマット対応
```python
# 用途別フォーマット出力
result = capture.capture_multi_format(
    formats=['PNG', 'JPEG', 'WebP'],
    sizes=[(1920, 1080), (1024, 768), (512, 384)],
    purpose='ai_analysis'
)
# result = {
#   'original': {'path': '...', 'size': (1920, 1080), 'format': 'PNG'},
#   'ai_optimized': {'path': '...', 'size': (1024, 768), 'format': 'JPEG'},
#   'thumbnail': {'path': '...', 'size': (512, 384), 'format': 'WebP'}
# }
```

### 2. OCRテキスト抽出機能

#### 2.1 基本OCR機能
```python
from screenshot_lib import ScreenshotCapture, OCRExtractor

# OCR付きスクリーンショット
capture = ScreenshotCapture()
ocr = OCRExtractor(engine='tesseract')  # tesseract, easyocr, paddleocr

result = capture.capture_with_ocr(
    ocr_engine=ocr,
    languages=['jpn', 'eng'],
    extract_regions=True  # テキスト領域の座標も抽出
)
# result = {
#   'image_path': '...',
#   'text_content': 'extracted text...',
#   'text_regions': [
#     {'text': 'Hello', 'bbox': (100, 50, 200, 80), 'confidence': 0.95},
#     {'text': 'こんにちは', 'bbox': (100, 100, 250, 130), 'confidence': 0.92}
#   ],
#   'metadata': {...}
# }
```

#### 2.2 構造化テキスト抽出
```python
# UI要素の識別
result = capture.capture_with_ui_analysis(
    detect_elements=['buttons', 'text_fields', 'menus', 'dialogs'],
    structure_analysis=True
)
# result['ui_elements'] = [
#   {'type': 'button', 'text': 'Submit', 'bbox': (...)},
#   {'type': 'text_field', 'text': 'Enter your name', 'bbox': (...)}
# ]
```

### 3. AI分析結果管理

#### 3.1 分析履歴の保存
```python
from screenshot_lib import AnalysisManager

manager = AnalysisManager(storage_path='./ai_analysis')

# 分析結果の保存
analysis_id = manager.save_analysis(
    screenshot_path='./screenshots/image.png',
    analysis_result={
        'description': 'Chrome browser showing GitHub repository',
        'detected_objects': ['browser_window', 'code_editor', 'file_tree'],
        'text_content': 'extracted text...',
        'confidence_score': 0.87,
        'ai_model': 'claude-3-sonnet',
        'analysis_timestamp': '2025-06-11T12:34:56Z'
    },
    tags=['web_development', 'github', 'code_review']
)

# 分析履歴の検索
results = manager.search_analysis(
    tags=['github'],
    date_range=('2025-06-01', '2025-06-11'),
    confidence_min=0.8
)
```

#### 3.2 分析結果の可視化
```python
# 分析結果の可視化（HTMLレポート生成）
report = manager.generate_report(
    analysis_ids=[analysis_id],
    include_images=True,
    include_stats=True,
    format='html'
)
```

### 4. バッチ処理機能

#### 4.1 スケジューリング
```python
from screenshot_lib import ScheduledCapture

# 定期的なスクリーンショット + AI分析
scheduler = ScheduledCapture()

# 30分ごとに画面キャプチャ + AI分析
scheduler.add_task(
    name='periodic_analysis',
    interval=30*60,  # 30 minutes
    action='capture_and_analyze',
    ai_prompt='この画面で何をしているか説明してください',
    save_analysis=True
)

scheduler.start()
```

#### 4.2 バッチ分析
```python
# 既存スクリーンショットの一括分析
from screenshot_lib import BatchProcessor

processor = BatchProcessor()
results = processor.analyze_batch(
    screenshot_folder='./screenshots',
    ai_prompt='この画面の内容を分析してください',
    parallel_workers=3,
    output_format='json'
)
```

### 5. AI連携API

#### 5.1 Claude連携
```python
from screenshot_lib import AIAnalyzer

# Claude APIとの連携
analyzer = AIAnalyzer(
    provider='anthropic',
    model='claude-3-sonnet-20240229',
    api_key='your-api-key'
)

result = analyzer.analyze_screenshot(
    image_path='./screenshot.png',
    prompt='この画面で何が起こっているか詳しく説明してください',
    include_ocr_text=True,
    max_tokens=1000
)
```

#### 5.2 OpenAI Vision連携
```python
# OpenAI GPT-4 Visionとの連携
analyzer = AIAnalyzer(
    provider='openai',
    model='gpt-4-vision-preview',
    api_key='your-api-key'
)

result = analyzer.analyze_screenshot(
    image_path='./screenshot.png',
    prompt='Describe what you see in this screenshot',
    detail_level='high'
)
```

## データベース設計

### 分析結果テーブル
```sql
CREATE TABLE screenshot_analysis (
    id UUID PRIMARY KEY,
    screenshot_path TEXT NOT NULL,
    analysis_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ai_model TEXT NOT NULL,
    prompt TEXT,
    response TEXT,
    confidence_score FLOAT,
    processing_time_ms INTEGER,
    tags TEXT[], -- PostgreSQL array
    metadata JSONB
);

CREATE TABLE screenshot_metadata (
    id UUID PRIMARY KEY,
    file_path TEXT NOT NULL,
    file_size INTEGER,
    resolution TEXT,
    created_at TIMESTAMP,
    active_app TEXT,
    window_title TEXT,
    ocr_text TEXT,
    ui_elements JSONB
);
```

## 設定ファイル拡張

### AI機能設定
```yaml
# ~/.screenshot_config.yaml
ai_integration:
  enabled: true
  default_provider: 'anthropic'
  providers:
    anthropic:
      api_key: '${ANTHROPIC_API_KEY}'
      model: 'claude-3-sonnet-20240229'
      max_tokens: 1000
    openai:
      api_key: '${OPENAI_API_KEY}'
      model: 'gpt-4-vision-preview'
  
  preprocessing:
    auto_resize: true
    target_resolution: [1024, 768]
    format: 'JPEG'
    quality: 85
  
  ocr:
    enabled: true
    engine: 'tesseract'
    languages: ['jpn', 'eng']
  
  analysis_storage:
    database_url: 'sqlite:///./ai_analysis.db'
    save_images: true
    retention_days: 30
```

## 実装順序

### Phase 2.1: 基本AI機能
1. [ ] 画像前処理機能の実装
2. [ ] OCRテキスト抽出の実装
3. [ ] 基本的なAI API連携

### Phase 2.2: 分析結果管理
1. [ ] データベース設計・実装
2. [ ] 分析履歴保存機能
3. [ ] 検索・フィルタリング機能

### Phase 2.3: バッチ処理
1. [ ] スケジューリング機能
2. [ ] バッチ分析機能
3. [ ] レポート生成機能

## 利用例

### AI分析付きスクリーンショット
```python
# my_ai_project.py
from screenshot_lib import ScreenshotCapture, AIAnalyzer

class SmartScreenshotAnalyzer:
    def __init__(self):
        self.capture = ScreenshotCapture(ai_mode=True)
        self.analyzer = AIAnalyzer(provider='anthropic')
        
    def analyze_current_task(self):
        # スクリーンショット撮影
        result = self.capture.capture_with_context(
            include_ocr=True,
            preprocessing={'target_resolution': (1024, 768)}
        )
        
        # AI分析
        analysis = self.analyzer.analyze_screenshot(
            result['image_path'],
            prompt='現在の作業内容を分析し、生産性向上のアドバイスをしてください',
            context=result['metadata']
        )
        
        return {
            'screenshot': result,
            'analysis': analysis,
            'timestamp': datetime.now().isoformat()
        }

# 使用例
analyzer = SmartScreenshotAnalyzer()
report = analyzer.analyze_current_task()
print(f"AI分析結果: {report['analysis']['response']}")
```

---
*設計完了: 2025-06-11*