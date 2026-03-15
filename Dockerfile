# 前端 Dockerfile
# 使用毫秒镜像源（2025年12月实测可用）
FROM docker.1ms.run/node:18-alpine AS builder

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY package*.json ./

# 安装依赖（使用npm install替代npm ci避免锁定文件问题）
RUN npm install --only=production

# 复制源码
COPY . .

# 构建应用
RUN npm run build

# 运行时镜像
FROM nginx:alpine

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制nginx配置
COPY nginx.conf /etc/nginx/nginx.conf

# 暴露端口
EXPOSE 3000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

# 启动nginx
CMD ["nginx", "-g", "daemon off;"]