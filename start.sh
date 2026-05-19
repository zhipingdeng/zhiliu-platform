#!/bin/bash

# 智流平台启动脚本

set -e

echo "=========================================="
echo "  智流 — 企业级智能流程自动化平台"
echo "=========================================="

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "错误: Docker 未安装，请先安装 Docker"
    exit 1
fi

# 检查 Docker Compose 是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "错误: Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 复制环境配置
if [ ! -f .env ]; then
    echo "创建环境配置文件..."
    cp .env.example .env
    echo "请编辑 .env 文件配置您的环境变量"
fi

# 解析命令行参数
case "$1" in
    start)
        echo "启动所有服务..."
        docker-compose up -d
        echo ""
        echo "服务启动完成！"
        echo "  前端: http://localhost"
        echo "  后端: http://localhost:8000"
        echo "  API 文档: http://localhost:8000/docs"
        echo ""
        echo "使用 'docker-compose logs -f' 查看日志"
        ;;
    stop)
        echo "停止所有服务..."
        docker-compose down
        echo "服务已停止"
        ;;
    restart)
        echo "重启所有服务..."
        docker-compose down
        docker-compose up -d
        echo "服务已重启"
        ;;
    build)
        echo "构建镜像..."
        docker-compose build
        echo "构建完成"
        ;;
    logs)
        docker-compose logs -f
        ;;
    status)
        docker-compose ps
        ;;
    clean)
        echo "清理所有容器和数据..."
        read -p "确认删除所有数据？(y/N) " confirm
        if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
            docker-compose down -v
            echo "清理完成"
        else
            echo "取消清理"
        fi
        ;;
    *)
        echo "使用方法: $0 {start|stop|restart|build|logs|status|clean}"
        echo ""
        echo "命令说明:"
        echo "  start   - 启动所有服务"
        echo "  stop    - 停止所有服务"
        echo "  restart - 重启所有服务"
        echo "  build   - 构建 Docker 镜像"
        echo "  logs    - 查看服务日志"
        echo "  status  - 查看服务状态"
        echo "  clean   - 清理所有容器和数据"
        exit 1
        ;;
esac
