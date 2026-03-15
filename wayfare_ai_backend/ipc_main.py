import sys
import json
import asyncio
import threading
import traceback
import os
from loguru import logger
from datetime import datetime

# 配置标准IO编码
sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# 导入服务模块
from config import settings
from database import init_db_pool, close_db_pool
from services import (
    handle_parse, handle_annotate, handle_query, 
    handle_behavior, handle_config, start_background_tasks
)

# 配置日志 - 所有日志必须输出到stderr或文件，不能污染stdout的JSON流
logger.remove()
logger.add(sys.stderr, level="INFO", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")
logger.add("logs/wayfare_ipc_{time}.log", rotation="10 MB", retention="10 days", level="DEBUG")

# 全局变量
running = True
request_count = 0

async def send_response(payload: dict):
    """向前端Go引擎发送单行JSON响应"""
    try:
        print(json.dumps(payload, ensure_ascii=False), flush=True)
    except Exception as e:
        logger.error(f"发送响应失败: {e}")

async def send_success(req_id: str, seq: int, data: dict):
    """发送成功响应"""
    await send_response({
        "id": req_id,
        "seq": seq,
        "success": True,
        "data": data,
        "timestamp": datetime.now().isoformat()
    })

async def send_error(req_id: str, seq: int, error: str):
    """发送错误响应"""
    await send_response({
        "id": req_id,
        "seq": seq,
        "success": False,
        "error": error,
        "timestamp": datetime.now().isoformat()
    })

async def dispatch_request(req: dict):
    """根据JSON-RPC方法分发调度请求"""
    global request_count
    request_count += 1
    
    req_id = req.get("id", f"unknown_{request_count}")
    seq = req.get("seq", 0)
    method = req.get("method")
    params = req.get("params", {})
    
    start_time = datetime.now()
    
    try:
        logger.info(f"📥 收到请求 [{req_id}] {method} - 参数: {json.dumps(params, ensure_ascii=False)[:200]}...")
        
        # 根据方法分发处理
        if method == "parse":
            data = await handle_parse(params)
        elif method == "annotate":
            data = await handle_annotate(params)
        elif method == "query":
            data = await handle_query(params)
        elif method == "behavior":
            data = await handle_behavior(params)
        elif method == "config":
            data = await handle_config(params)
        else:
            raise ValueError(f"未知的方法: {method}")
            
        # 发送成功响应
        await send_success(req_id, seq, data)
        
        # 记录处理时间
        process_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ 请求处理完成 [{req_id}] {method} - 耗时: {process_time:.2f}s")
        
    except Exception as e:
        error_msg = f"处理请求失败 [{req_id}] {method}: {str(e)}"
        logger.error(f"❌ {error_msg}\n{traceback.format_exc()}")
        await send_error(req_id, seq, str(e))

async def stdin_reader(queue: asyncio.Queue):
    """标准输入读取器 - 在后台线程运行"""
    logger.info("🚀 启动标准输入监听器...")
    
    while running:
        try:
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                logger.warning("🚪 标准输入流结束，准备退出...")
                await queue.put(None)  # 发送结束信号
                break
                
            line = line.strip()
            if not line:
                continue
                
            await queue.put(line)
            
        except Exception as e:
            logger.error(f"读取标准输入失败: {e}")
            await queue.put(None)
            break

async def process_requests(queue: asyncio.Queue):
    """请求处理器"""
    logger.info("🔄 启动请求处理器...")
    
    while running:
        try:
            line = await queue.get()
            if line is None:  # 结束信号
                logger.info("🛑 收到退出信号，停止处理请求")
                break
                
            # 解析JSON请求
            try:
                req = json.loads(line)
                if not isinstance(req, dict):
                    raise ValueError("请求必须是JSON对象")
                    
                # 异步处理请求
                asyncio.create_task(dispatch_request(req))
                
            except json.JSONDecodeError as e:
                logger.error(f"解析JSON失败: {e} - 原始数据: {line[:200]}")
                await send_error("invalid", 0, "无效的JSON格式")
                
            except Exception as e:
                logger.error(f"处理请求异常: {e}")
                await send_error("error", 0, str(e))
                
        except Exception as e:
            logger.error(f"请求处理器异常: {e}")
            await asyncio.sleep(1)  # 避免快速重试

async def health_check():
    """健康检查协程"""
    while running:
        try:
            # 定期发送心跳
            await asyncio.sleep(30)
            logger.debug(f"💓 服务运行正常 - 已处理 {request_count} 个请求")
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"健康检查异常: {e}")

async def main():
    """主函数"""
    global running
    
    logger.info("🎯 WayFare Python AI Sidecar 启动中...")
    
    try:
        # 初始化数据库连接池
        logger.info("📊 初始化数据库连接池...")
        await init_db_pool()
        
        # 启动后台任务
        logger.info("⚙️ 启动后台任务...")
        await start_background_tasks()
        
        # 创建请求队列
        request_queue = asyncio.Queue(maxsize=1000)
        
        # 启动协程
        tasks = [
            asyncio.create_task(stdin_reader(request_queue)),
            asyncio.create_task(process_requests(request_queue)),
            asyncio.create_task(health_check())
        ]
        
        logger.info("✅ WayFare Python AI Sidecar 已就绪，等待Go后端请求...")
        logger.info("📝 提示: 所有日志输出到 stderr，stdout 仅用于JSON响应")
        
        # 等待所有任务完成
        await asyncio.gather(*tasks)
        
    except KeyboardInterrupt:
        logger.info("🛑 收到键盘中断，优雅关闭中...")
    except Exception as e:
        logger.error(f"💥 致命错误: {e}\n{traceback.format_exc()}")
    finally:
        running = False
        
        # 清理资源
        logger.info("🧹 清理资源...")
        try:
            await close_db_pool()
        except Exception as e:
            logger.error(f"关闭数据库连接失败: {e}")
            
        logger.info("👋 WayFare Python AI Sidecar 已关闭")

if __name__ == "__main__":
    # 确保日志目录存在
    os.makedirs("logs", exist_ok=True)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序异常退出: {e}")
        sys.exit(1)