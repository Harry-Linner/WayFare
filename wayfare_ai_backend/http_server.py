#!/usr/bin/env python3
"""
WayFare Python AI HTTP服务器
提供HTTP接口供Go后端调用
"""

import json
import asyncio
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from loguru import logger
import uvicorn

# 导入IPC服务处理模块
from services import (
    handle_parse, handle_annotate, handle_query, 
    handle_behavior, handle_config, start_background_tasks
)
from database import init_db_pool, close_db_pool
from config import settings

# 请求模型
class ProcessRequest(BaseModel):
    method: str
    params: Dict[str, Any] = {}

# 响应模型  
class ProcessResponse(BaseModel):
    success: bool
    data: Dict[str, Any] = {}
    error: str = ""

# 创建FastAPI应用
app = FastAPI(
    title="WayFare Python AI Service",
    description="AI服务处理文档解析、注释生成等功能",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 服务映射
SERVICE_HANDLERS = {
    'parse': handle_parse,
    'annotate': handle_annotate, 
    'query': handle_query,
    'behavior': handle_behavior,
    'config': handle_config
}

@app.on_event("startup")
async def startup_event():
    """服务启动事件"""
    logger.info("🚀 WayFare Python AI HTTP服务启动中...")
    
    try:
        # 初始化数据库连接池
        logger.info("📊 初始化数据库连接池...")
        await init_db_pool()
        
        # 启动后台任务
        logger.info("⚙️ 启动后台任务...")
        await start_background_tasks()
        
        logger.info("✅ WayFare Python AI HTTP服务已就绪")
        
    except Exception as e:
        logger.error(f"❌ 服务启动失败: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """服务关闭事件"""
    logger.info("🛑 WayFare Python AI HTTP服务关闭中...")
    try:
        await close_db_pool()
        logger.info("✅ 数据库连接已关闭")
    except Exception as e:
        logger.error(f"❌ 关闭数据库连接失败: {e}")

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok", "service": "python-ai"}

@app.post("/api/process", response_model=ProcessResponse)
async def process_request(request: ProcessRequest):
    """处理AI请求的主接口"""
    try:
        method = request.method
        params = request.params
        
        logger.info(f"📨 收到请求: method={method}, params={json.dumps(params, ensure_ascii=False)}")
        
        # 检查方法是否支持
        if method not in SERVICE_HANDLERS:
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的方法: {method}. 支持的方法: {list(SERVICE_HANDLERS.keys())}"
            )
        
        # 调用对应的处理函数
        handler = SERVICE_HANDLERS[method]
        
        # 异步调用处理函数
        if asyncio.iscoroutinefunction(handler):
            result = await handler(params)
        else:
            # 如果是同步函数，在线程池中运行
            import concurrent.futures
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                result = await loop.run_in_executor(pool, handler, params)
        
        logger.info(f"✅ 请求处理成功: method={method}")
        
        return ProcessResponse(
            success=True,
            data=result if isinstance(result, dict) else {"result": result}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 请求处理失败: method={method}, error={e}")
        return ProcessResponse(
            success=False,
            error=str(e)
        )

@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "WayFare Python AI",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "process": "/api/process"
        }
    }

if __name__ == "__main__":
    """主函数"""
    logger.info("🎯 启动WayFare Python AI HTTP服务器...")
    
    # 确保日志目录存在
    import os
    os.makedirs("logs", exist_ok=True)
    
    # 启动HTTP服务器
    uvicorn.run(
        "http_server:app",
        host="0.0.0.0",
        port=8001,
        log_level="info",
        access_log=True,
        reload=False
    )