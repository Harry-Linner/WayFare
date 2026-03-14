import sys
import json
import asyncio
import threading
import traceback
from loguru import logger
sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
from config import settings
from database import init_db_pool, close_db_pool
from services import (
    handle_parse, handle_annotate, handle_query, 
    handle_behavior, handle_config, start_background_tasks,
    send_notification
)

# 核心规范: 所有的日志必须走到 stderr 或者文件，绝对不能污染 stdout 的 JSON 流！
logger.remove()
logger.add(sys.stderr, level="DEBUG")
logger.add("logs/wayfare_ipc_{time}.log", rotation="10 MB", retention="10 days", level="DEBUG")

def send_response(payload: dict):
    """向前端 C 引擎发送单行 JSON (唯一允许写入 stdout 的地方)"""
    print(json.dumps(payload, ensure_ascii=False), flush=True)

def send_success(req_id: str, seq: int, data: dict):
    send_response({
        "id": req_id,
        "seq": seq,
        "success": True,
        "data": data
    })

def send_error(req_id: str, seq: int, error: str):
    send_response({
        "id": req_id,
        "seq": seq,
        "success": False,
        "error": error
    })

async def dispatch_request(req: dict):
    """根据 JSON-RPC 方法分发调度请求"""
    req_id = req.get("id", "unknown_id")
    seq = req.get("seq", 0)
    method = req.get("method")
    params = req.get("params", {})
    
    try:
        logger.debug(f"IPC RECV -> [req_id={req_id}] {method}")
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
            raise ValueError(f"Unknown RPC method: {method}")
            
        send_success(req_id, seq, data)
    except Exception as e:
        logger.error(f"Error handling IPC request {req_id}: {traceback.format_exc()}")
        send_error(req_id, seq, str(e))

async def main():
    logger.info("Initializing DB Pool...")
    try:
        await init_db_pool()
        pass
    except Exception as e:
        logger.warning(f"Database unavailable: {e}")
        
    # 启动定时行为监听，触发滞留主动发问
    await start_background_tasks()

    # 安全地将阻塞的 stdin 放置到后台线程并用 Queue 通信
    queue = asyncio.Queue()
    loop = asyncio.get_running_loop()
    
    def stdin_reader():
        for line in sys.stdin:
            if not line.strip():
                continue
            loop.call_soon_threadsafe(queue.put_nowait, line)
            
    # 设置 daemon=True 防止线程阻塞退出
    listener_thread = threading.Thread(target=stdin_reader, daemon=True)
    listener_thread.start()
    
    logger.info("WayFare Python Sidecar ready. Listening on stdin.")
    
    while True:
        line = await queue.get()
        try:
            req = json.loads(line)
            asyncio.create_task(dispatch_request(req))
        except json.JSONDecodeError:
            logger.error(f"Failed to decode IPC message: {line}")
            # 不是标准 JSON，可能是脏数据，直接丢弃

if __name__ == "__main__":
    try:
        
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Sidecar shut down cleanly.")
        # db 清理
        if "close_db_pool" in globals():
            asyncio.run(close_db_pool())
    except Exception as e:
        logger.error(f"Fatal unhandled exception in sidecar: {e}")
