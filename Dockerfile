# Screenshot Manager Production Docker Image
FROM python:3.11-slim

# メタデータ
LABEL maintainer="Screenshot Manager Team"
LABEL description="AI-powered screenshot automation tool for web applications"
LABEL version="3.0.0"

# 環境変数
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV APP_HOME=/app
ENV ENV=production

# システム依存関係のインストール
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    software-properties-common \
    curl \
    xvfb \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libgtk-3-0 \
    libgdk-pixbuf2.0-0 \
    libdrm2 \
    libxss1 \
    libxrandr2 \
    libasound2 \
    libpangocairo-1.0-0 \
    libatk1.0-0 \
    libcairo-gobject2 \
    libgtk-3-0 \
    libgdk-pixbuf2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリ作成
WORKDIR $APP_HOME

# Python依存関係をコピー
COPY requirements.txt requirements-dev.txt ./

# Python依存関係インストール
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install gunicorn

# Playwrightブラウザインストール
RUN pip install playwright \
    && playwright install chromium \
    && playwright install-deps chromium

# アプリケーションコードをコピー
COPY . .

# ディレクトリ作成
RUN mkdir -p logs screenshots config

# 設定ファイルテンプレートをコピー
RUN if [ ! -f config/config.json ]; then \
        cp config/config.json.template config/config.json; \
    fi

RUN if [ ! -f config/webapp_config.json ]; then \
        cp config/webapp_config.json.template config/webapp_config.json; \
    fi

# 実行権限付与
RUN chmod +x scripts/*.sh

# 非rootユーザー作成
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser $APP_HOME
USER appuser

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')" || exit 1

# ポート公開
EXPOSE 8080

# エントリーポイント
COPY docker-entrypoint.sh /usr/local/bin/
ENTRYPOINT ["docker-entrypoint.sh"]

# デフォルトコマンド
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "src.integrations.mcp_http_server:app"]