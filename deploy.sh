#!/bin/bash

# Screenshot Manager Deployment Script
# Usage: ./deploy.sh [docker|k8s|prod]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="screenshot-manager"
VERSION=${VERSION:-"latest"}
NAMESPACE="screenshot-system"

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log "Prerequisites チェック中..."
    
    if [[ "$1" == "docker" || "$1" == "prod" ]]; then
        if ! command -v docker &> /dev/null; then
            error "Docker がインストールされていません"
            exit 1
        fi
        
        if ! command -v docker-compose &> /dev/null; then
            error "Docker Compose がインストールされていません"
            exit 1
        fi
    fi
    
    if [[ "$1" == "k8s" ]]; then
        if ! command -v kubectl &> /dev/null; then
            error "kubectl がインストールされていません"
            exit 1
        fi
        
        if ! kubectl cluster-info &> /dev/null; then
            error "Kubernetes クラスターに接続できません"
            exit 1
        fi
    fi
    
    success "Prerequisites チェック完了"
}

# Docker development deployment
deploy_docker() {
    log "Docker 開発環境デプロイを開始..."
    
    # Build image
    log "Docker イメージをビルド中..."
    docker build -t ${APP_NAME}:${VERSION} .
    
    # Start services
    log "Docker サービスを開始中..."
    docker-compose up -d
    
    # Wait for services
    log "サービスの起動を待機中..."
    sleep 30
    
    # Check health
    check_docker_health
    
    success "Docker デプロイが完了しました"
    log "アプリケーション: http://localhost:8080"
    log "MCP サーバー: http://localhost:8081"
    log "Grafana 監視: http://localhost:3001"
}

# Production Docker deployment
deploy_production() {
    log "本番環境デプロイを開始..."
    
    # Build image
    log "本番用 Docker イメージをビルド中..."
    docker build -t ${APP_NAME}:${VERSION} .
    
    # Start production services
    log "本番サービスを開始中..."
    docker-compose -f docker-compose.prod.yml up -d
    
    # Wait for services
    log "本番サービスの起動を待機中..."
    sleep 60
    
    # Check health
    check_docker_health
    
    success "本番デプロイが完了しました"
    warning "SSL証明書とドメイン設定を確認してください"
}

# Kubernetes deployment
deploy_kubernetes() {
    log "Kubernetes デプロイを開始..."
    
    # Create namespace
    log "Namespace を作成中..."
    kubectl apply -f k8s/configmap.yaml
    
    # Apply storage
    log "ストレージを設定中..."
    kubectl apply -f k8s/storage.yaml
    
    # Apply monitoring
    log "監視コンポーネントをデプロイ中..."
    kubectl apply -f k8s/monitoring.yaml
    
    # Apply main application
    log "メインアプリケーションをデプロイ中..."
    kubectl apply -f k8s/deployment.yaml
    kubectl apply -f k8s/service.yaml
    
    # Apply ingress
    log "Ingress を設定中..."
    kubectl apply -f k8s/ingress.yaml
    
    # Wait for deployment
    log "デプロイメントの完了を待機中..."
    kubectl wait --for=condition=available --timeout=300s deployment/${APP_NAME} -n ${NAMESPACE}
    kubectl wait --for=condition=available --timeout=300s deployment/mcp-server -n ${NAMESPACE}
    kubectl wait --for=condition=available --timeout=300s deployment/webapp-monitor -n ${NAMESPACE}
    
    # Check status
    check_kubernetes_health
    
    success "Kubernetes デプロイが完了しました"
}

# Health check for Docker
check_docker_health() {
    log "Docker サービスの健全性をチェック中..."
    
    # Check screenshot-manager
    if curl -f http://localhost:8080/health &> /dev/null; then
        success "Screenshot Manager: 正常"
    else
        warning "Screenshot Manager: 応答なし"
    fi
    
    # Check MCP server
    if curl -f http://localhost:8081/status &> /dev/null; then
        success "MCP Server: 正常"
    else
        warning "MCP Server: 応答なし"
    fi
    
    # Check Grafana
    if curl -f http://localhost:3001/api/health &> /dev/null; then
        success "Grafana: 正常"
    else
        warning "Grafana: 応答なし"
    fi
}

# Health check for Kubernetes
check_kubernetes_health() {
    log "Kubernetes サービスの健全性をチェック中..."
    
    # Check pods
    kubectl get pods -n ${NAMESPACE}
    
    # Check services
    kubectl get services -n ${NAMESPACE}
    
    # Check ingress
    kubectl get ingress -n ${NAMESPACE}
    
    success "Kubernetes 健全性チェック完了"
}

# Stop services
stop_services() {
    log "サービスを停止中..."
    
    if [[ -f "docker-compose.yml" ]]; then
        docker-compose down
    fi
    
    if [[ -f "docker-compose.prod.yml" ]]; then
        docker-compose -f docker-compose.prod.yml down
    fi
    
    success "サービスが停止されました"
}

# Remove Kubernetes deployment
remove_kubernetes() {
    log "Kubernetes デプロイメントを削除中..."
    
    kubectl delete -f k8s/ --ignore-not-found=true
    kubectl delete namespace ${NAMESPACE} --ignore-not-found=true
    
    success "Kubernetes デプロイメントが削除されました"
}

# Show logs
show_logs() {
    case "$1" in
        "docker")
            docker-compose logs -f
            ;;
        "k8s")
            kubectl logs -f deployment/${APP_NAME} -n ${NAMESPACE}
            ;;
        *)
            tail -f logs/*.log
            ;;
    esac
}

# Main execution
main() {
    case "$1" in
        "docker")
            check_prerequisites "docker"
            deploy_docker
            ;;
        "prod")
            check_prerequisites "docker"
            deploy_production
            ;;
        "k8s")
            check_prerequisites "k8s"
            deploy_kubernetes
            ;;
        "stop")
            stop_services
            ;;
        "remove-k8s")
            remove_kubernetes
            ;;
        "logs")
            show_logs "$2"
            ;;
        "status")
            case "$2" in
                "docker")
                    docker-compose ps
                    ;;
                "k8s")
                    kubectl get all -n ${NAMESPACE}
                    ;;
                *)
                    echo "使用法: $0 status [docker|k8s]"
                    ;;
            esac
            ;;
        *)
            echo "Screenshot Manager Deployment Script"
            echo ""
            echo "使用法: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  docker    - Docker 開発環境デプロイ"
            echo "  prod      - Docker 本番環境デプロイ"
            echo "  k8s       - Kubernetes デプロイ"
            echo "  stop      - サービス停止"
            echo "  remove-k8s - Kubernetes デプロイメント削除"
            echo "  logs      - ログ表示"
            echo "  status    - ステータス確認"
            echo ""
            echo "例:"
            echo "  $0 docker"
            echo "  $0 prod"
            echo "  $0 k8s"
            echo "  $0 logs docker"
            echo "  $0 status k8s"
            exit 1
            ;;
    esac
}

# Execute main function
main "$@"