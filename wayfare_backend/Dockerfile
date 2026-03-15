# Go后端 Dockerfile
# 使用毫秒镜像源（2025年12月实测可用）
FROM docker.1ms.run/golang:1.23-alpine AS builder

# 安装构建依赖（添加ca-certificates支持HTTPS）
RUN apk add --no-cache git gcc musl-dev ca-certificates

# 设置工作目录
WORKDIR /app

# 配置Go模块代理和镜像源
ENV GOPROXY=https://goproxy.cn,direct
ENV GOSUMDB=off
ENV GO111MODULE=on

# 复制go.mod和go.sum
COPY go.mod go.sum ./

# 下载依赖（添加验证）
RUN go mod download && go mod verify

# 复制源代码
COPY . .

# 构建应用（优化参数和日志）
RUN echo "🔨 开始构建Go应用..." && \
    CGO_ENABLED=0 GOOS=linux go build -v -ldflags="-s -w" -o wayfare-backend . && \
    echo "✅ 构建完成，二进制文件大小:" && ls -lh wayfare-backend

# 运行时镜像
FROM alpine:latest

# 安装运行时依赖（完整Python环境和工具）
RUN apk add --no-cache \
    ca-certificates \
    tzdata \
    python3 \
    py3-pip \
    bash \
    curl \
    && rm -rf /var/cache/apk/*

# 设置时区
ENV TZ=Asia/Shanghai

# 创建工作目录
WORKDIR /root/

# 复制二进制文件
COPY --from=builder /app/wayfare-backend .

# 创建必要的目录结构
RUN mkdir -p uploads logs && \
    chmod 755 uploads logs

# 暴露端口
EXPOSE 8080

# 健康检查（延长启动时间，给Python侧车足够启动时间）
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

# 启动命令（添加启动日志）
CMD echo "🚀 启动WayFare Go后端服务..." && \
    echo "📁 工作目录:$(pwd)" && \
    echo "📊 文件列表:$(ls -la)" && \
    exec ./wayfare-backend