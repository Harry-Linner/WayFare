"""
IPC Handler模块

处理与Tauri前端的IPC通信，实现JSON-RPC协议的请求解析、验证、
队列管理和响应封装。支持异步文档解析和主动推送通知。
"""

import json
import asyncio
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class IPCRequest:
    """IPC请求数据模型
    
    符合api-contract.yaml规范的请求消息格式。
    """
    id: str
    seq: int
    method: str
    params: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """验证请求字段"""
        if not self.id:
            raise ValueError("Request id is required")
        if self.seq < 0:
            raise ValueError("Request seq must be non-negative")
        if not self.method:
            raise ValueError("Request method is required")


@dataclass
class IPCResponse:
    """IPC响应数据模型
    
    符合api-contract.yaml规范的响应消息格式。
    """
    id: str
    seq: int
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "id": self.id,
            "seq": self.seq,
            "success": self.success
        }
        if self.success and self.data is not None:
            result["data"] = self.data
        if not self.success and self.error is not None:
            result["error"] = self.error
        return result


class IPCHandler:
    """IPC处理器
    
    负责处理与Tauri前端的通信，包括：
    - 接收和验证JSON-RPC格式的IPC请求
    - 按seq序列号排序处理请求，防止"先发后到"
    - 路由请求到对应的处理器（parse/annotate/query/config）
    - 封装响应消息并返回给前端
    - 处理异步操作（parse请求不阻塞）
    
    Requirements:
    - 5.4: Support four methods: parse, annotate, query, config
    - 5.7: Handle parse requests asynchronously without blocking other requests
    """
    
    # 支持的方法列表
    SUPPORTED_METHODS = ["parse", "annotate", "query", "config", "behavior"]
    
    def __init__(self, 
                 doc_parser=None,
                 annotation_gen=None,
                 vector_store=None,
                 embedding_service=None,
                 config_manager=None,
                 behavior_analyzer=None):
        """初始化IPC Handler
        
        Args:
            doc_parser: DocumentParser实例（可选，用于parse方法）
            annotation_gen: AnnotationGenerator实例（可选，用于annotate方法）
            vector_store: VectorStore实例（可选，用于query方法）
            embedding_service: EmbeddingService实例（可选，用于query方法）
            config_manager: ConfigManager实例（可选，用于config方法）
            behavior_analyzer: BehaviorAnalyzer实例（可选，用于行为分析）
        """
        # 请求队列，按seq排序
        self.request_queue: deque = deque()
        # 处理锁，防止并发处理
        self.processing_lock = asyncio.Lock()
        # 下一个期望的seq（用于顺序处理）
        self.next_expected_seq = 0
        # 待处理的请求缓存（seq不连续时暂存）
        self.pending_requests: Dict[int, IPCRequest] = {}
        
        # 依赖注入的组件
        self.doc_parser = doc_parser
        self.annotation_gen = annotation_gen
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.config_manager = config_manager
        self.behavior_analyzer = behavior_analyzer
        
        # 后台任务：定期检查干预触发条件
        self._intervention_task = None
        self._intervention_check_interval = 30  # 每30秒检查一次
        self._active_pages: Dict[str, Dict[str, Any]] = {}  # 跟踪活跃页面
    
    async def handle_request(self, raw_message: str) -> str:
        """处理IPC请求的入口
        
        Args:
            raw_message: JSON格式的原始请求消息
            
        Returns:
            JSON格式的响应消息
        """
        try:
            # 1. 解析请求
            request = self._parse_request(raw_message)
            
            # 2. 验证请求
            self._validate_request(request)
            
            # 3. 添加到队列并按seq排序
            await self._enqueue_request(request)
            
            # 4. 处理队列
            response = await self._process_queue()
            
            # 5. 返回响应
            if response:
                return self._serialize_response(response)
            else:
                # 如果没有响应（请求被缓存），返回空响应
                return self._serialize_response(IPCResponse(
                    id=request.id,
                    seq=request.seq,
                    success=True,
                    data={"status": "queued"}
                ))
            
        except ValueError as e:
            # 验证错误
            return self._error_response("", 0, str(e))
        except json.JSONDecodeError as e:
            # JSON解析错误
            return self._error_response("", 0, f"Invalid JSON: {str(e)}")
        except Exception as e:
            # 其他错误
            return self._error_response("", 0, f"Internal error: {str(e)}")
    
    def _parse_request(self, raw_message: str) -> IPCRequest:
        """解析JSON-RPC请求
        
        Args:
            raw_message: JSON格式的原始请求消息
            
        Returns:
            IPCRequest对象
            
        Raises:
            json.JSONDecodeError: JSON解析失败
            ValueError: 缺少必需字段
        """
        data = json.loads(raw_message)
        
        # 检查必需字段
        if "id" not in data:
            raise ValueError("Missing required field: id")
        if "seq" not in data:
            raise ValueError("Missing required field: seq")
        if "method" not in data:
            raise ValueError("Missing required field: method")
        
        return IPCRequest(
            id=data["id"],
            seq=data["seq"],
            method=data["method"],
            params=data.get("params", {})
        )
    
    def _validate_request(self, request: IPCRequest):
        """验证请求格式
        
        Args:
            request: IPCRequest对象
            
        Raises:
            ValueError: 验证失败
        """
        if not request.id:
            raise ValueError("Request id cannot be empty")
        
        if request.seq < 0:
            raise ValueError("Request seq must be non-negative")
        
        if request.method not in self.SUPPORTED_METHODS:
            raise ValueError(
                f"Unsupported method: {request.method}. "
                f"Supported methods: {', '.join(self.SUPPORTED_METHODS)}"
            )
        
        # 验证params是字典类型
        if not isinstance(request.params, dict):
            raise ValueError("Request params must be a dictionary")
    
    async def _enqueue_request(self, request: IPCRequest):
        """将请求加入队列并排序
        
        实现按seq顺序处理的逻辑：
        - 如果seq是下一个期望的seq，直接加入队列
        - 如果seq大于期望的seq，暂存到pending_requests
        - 如果seq小于期望的seq，说明是重复请求，忽略
        
        Args:
            request: IPCRequest对象
        """
        async with self.processing_lock:
            if request.seq == self.next_expected_seq:
                # 这是下一个期望的请求，直接加入队列
                self.request_queue.append(request)
                self.next_expected_seq += 1
                
                # 检查pending_requests中是否有后续的连续请求
                while self.next_expected_seq in self.pending_requests:
                    pending_req = self.pending_requests.pop(self.next_expected_seq)
                    self.request_queue.append(pending_req)
                    self.next_expected_seq += 1
                    
            elif request.seq > self.next_expected_seq:
                # seq不连续，暂存到pending_requests
                self.pending_requests[request.seq] = request
            # else: seq < next_expected_seq，说明是重复或过期的请求，忽略
    
    async def _process_queue(self) -> Optional[IPCResponse]:
        """处理队列中的请求
        
        Returns:
            IPCResponse对象，如果队列为空返回None
        """
        async with self.processing_lock:
            if not self.request_queue:
                return None
            
            # 取出队列头部的请求
            request = self.request_queue.popleft()
        
        # 路由请求到对应的处理器
        return await self._route_request(request)
    
    async def _route_request(self, request: IPCRequest) -> IPCResponse:
        """路由请求到对应的处理器
        
        Args:
            request: IPCRequest对象
            
        Returns:
            IPCResponse对象
        """
        try:
            # 根据method路由到对应的处理器
            if request.method == "parse":
                data = await self.handle_parse(request.params)
            elif request.method == "annotate":
                data = await self.handle_annotate(request.params)
            elif request.method == "query":
                data = await self.handle_query(request.params)
            elif request.method == "config":
                data = await self.handle_config(request.params)
            elif request.method == "behavior":
                data = await self.handle_behavior(request.params)
            else:
                raise ValueError(f"Unsupported method: {request.method}")
            
            return IPCResponse(
                id=request.id,
                seq=request.seq,
                success=True,
                data=data
            )
            
        except Exception as e:
            # 处理过程中的错误
            return IPCResponse(
                id=request.id,
                seq=request.seq,
                success=False,
                error=str(e)
            )
    
    async def handle_parse(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理parse请求（异步执行）
        
        实现异步文档解析：
        1. 立即返回"processing"状态，不阻塞其他请求
        2. 在后台异步执行文档解析
        3. 解析完成后通过主动推送通知前端
        
        Requirements:
        - 5.4: Support parse method
        - 5.7: Handle parse requests asynchronously without blocking other requests
        
        Args:
            params: 请求参数，应包含path字段
            
        Returns:
            响应数据字典，包含docHash和status="processing"
            
        Raises:
            ValueError: 缺少必需参数或DocumentParser未初始化
        """
        if "path" not in params:
            raise ValueError("Missing required parameter: path")
        
        # 检查DocumentParser是否已初始化
        if self.doc_parser is None:
            raise ValueError("DocumentParser not initialized")
        
        path = params["path"]
        
        # 计算文档hash（用于立即返回）
        try:
            doc_hash = self.doc_parser.compute_hash(path)
        except Exception as e:
            raise ValueError(f"Failed to compute document hash: {e}")
        
        # 异步处理解析任务（不阻塞）
        asyncio.create_task(self._async_parse(path, doc_hash))
        
        # 立即返回processing状态
        return {
            "docHash": doc_hash,
            "status": "processing"
        }
    
    async def _async_parse(self, path: str, doc_hash: str):
        """异步执行文档解析
        
        在后台执行文档解析，完成后通过主动推送通知前端。
        
        Args:
            path: 文档路径
            doc_hash: 文档hash
        """
        logger.info(f"Starting async parse for document: {path} (hash: {doc_hash})")
        
        try:
            # 执行文档解析
            result = await self.doc_parser.parse_document(path)
            
            logger.info(f"Parse completed for {doc_hash}: {result.segment_count} segments")
            
            # 解析完成后主动推送通知
            await self._send_notification({
                "type": "parse_completed",
                "docHash": doc_hash,
                "segmentCount": result.segment_count,
                "versionHash": result.version_hash,
                "status": "completed"
            })
            
        except Exception as e:
            logger.error(f"Parse failed for {path} (hash: {doc_hash}): {e}")
            
            # 解析失败，推送错误通知
            await self._send_notification({
                "type": "parse_failed",
                "docHash": doc_hash,
                "error": str(e),
                "status": "failed"
            })
    
    async def _send_notification(self, data: Dict[str, Any]):
        """向前端发送主动推送通知
        
        通过stdout发送JSON格式的通知消息，前端通过监听stdout接收。
        
        Args:
            data: 通知数据字典
        """
        import sys
        
        notification = {
            "type": "notification",
            "data": data
        }
        
        logger.debug(f"Sending notification: {notification['data'].get('type')}")
        
        # 输出到stdout，前端会监听并处理
        print(json.dumps(notification, ensure_ascii=False), file=sys.stdout, flush=True)
    
    async def handle_annotate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理annotate请求
        
        完整流程：
        1. 验证请求参数（docHash、page、bbox、type、context）
        2. 调用AnnotationGenerator生成批注
        3. 返回批注ID和内容
        
        Args:
            params: 请求参数，应包含docHash、page、bbox、type、context字段
                - docHash: 文档hash
                - page: 页码
                - bbox: 边界框字典，包含x、y、width、height
                - type: 批注类型（explanation/question/summary）
                - context: 用户选中的文本
            
        Returns:
            响应数据字典，包含：
                - annotationId: 批注ID
                - content: 批注内容
                - type: 批注类型
            
        Raises:
            ValueError: 缺少必需参数或参数无效
            RuntimeError: AnnotationGenerator未初始化
        """
        # 1. 验证必需参数
        required_params = ["docHash", "page", "bbox", "type", "context"]
        for param in required_params:
            if param not in params:
                raise ValueError(f"Missing required parameter: {param}")
        
        # 2. 检查AnnotationGenerator是否已初始化
        if self.annotation_gen is None:
            raise RuntimeError(
                "AnnotationGenerator not initialized. "
                "Please provide annotation_gen during IPCHandler initialization."
            )
        
        # 3. 验证bbox参数结构
        bbox = params["bbox"]
        required_bbox_fields = ["x", "y", "width", "height"]
        for field in required_bbox_fields:
            if field not in bbox:
                raise ValueError(f"Missing required bbox field: {field}")
        
        # 4. 验证批注类型
        valid_types = ["explanation", "question", "summary"]
        if params["type"] not in valid_types:
            raise ValueError(
                f"Invalid annotation type: {params['type']}. "
                f"Must be one of: {', '.join(valid_types)}"
            )
        
        # 5. 调用AnnotationGenerator生成批注
        try:
            annotation = await self.annotation_gen.generate_annotation(
                doc_hash=params["docHash"],
                page=params["page"],
                bbox=bbox,
                annotation_type=params["type"],
                context=params["context"]
            )
            
            # 6. 返回批注结果
            return {
                "annotationId": annotation.id,
                "content": annotation.content,
                "type": annotation.type
            }
            
        except ValueError as e:
            # 参数验证错误或文档不存在
            raise ValueError(f"Failed to generate annotation: {str(e)}")
        except Exception as e:
            # 其他错误（如数据库错误、LLM调用错误等）
            raise RuntimeError(f"Error generating annotation: {str(e)}")
    
    async def handle_query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理query请求
        
        完整流程：
        1. 验证请求参数（docHash、query、可选topK）
        2. 使用EmbeddingService生成查询向量
        3. 调用VectorStore.search_documents()搜索相关片段
        4. 返回检索结果（segmentId、text、page、score）
        
        Args:
            params: 请求参数，应包含docHash、query字段，可选topK字段
                - docHash: 文档hash
                - query: 查询文本
                - topK: 返回结果数量，默认5
            
        Returns:
            响应数据字典，包含：
                - results: 搜索结果列表，每个结果包含：
                    - segmentId: 片段ID
                    - text: 片段文本
                    - page: 页码
                    - score: 相似度分数
            
        Raises:
            ValueError: 缺少必需参数或参数无效
            RuntimeError: VectorStore或EmbeddingService未初始化
        """
        # 1. 验证必需参数
        required_params = ["docHash", "query"]
        for param in required_params:
            if param not in params:
                raise ValueError(f"Missing required parameter: {param}")
        
        # 2. 检查VectorStore是否已初始化
        if self.vector_store is None:
            raise RuntimeError(
                "VectorStore not initialized. "
                "Please provide vector_store during IPCHandler initialization."
            )
        
        # 3. 检查EmbeddingService是否已初始化
        if self.embedding_service is None:
            raise RuntimeError(
                "EmbeddingService not initialized. "
                "Please provide embedding_service during IPCHandler initialization."
            )
        
        # 4. 获取参数
        doc_hash = params["docHash"]
        query = params["query"]
        top_k = params.get("topK", 5)  # 默认返回5个结果
        
        # 5. 验证参数
        if not doc_hash or not doc_hash.strip():
            raise ValueError("docHash cannot be empty")
        
        if not query or not query.strip():
            raise ValueError("query cannot be empty")
        
        if not isinstance(top_k, int) or top_k <= 0:
            raise ValueError(f"topK must be a positive integer, got {top_k}")
        
        # 6. 执行搜索
        try:
            logger.debug(f"Processing query request: docHash={doc_hash}, query='{query}', topK={top_k}")
            
            # 调用VectorStore.search_documents()进行搜索
            search_results = await self.vector_store.search_documents(
                doc_hash=doc_hash,
                query=query,
                embedding_service=self.embedding_service,
                top_k=top_k
            )
            
            # 7. 格式化返回结果
            results = [
                {
                    "segmentId": result.segment_id,
                    "text": result.text,
                    "page": result.page,
                    "score": result.score
                }
                for result in search_results
            ]
            
            logger.debug(f"Query completed successfully, found {len(results)} results")
            
            return {
                "results": results
            }
            
        except ValueError as e:
            # 参数验证错误
            raise ValueError(f"Failed to execute query: {str(e)}")
        except Exception as e:
            # 其他错误（如向量搜索错误、embedding生成错误等）
            raise RuntimeError(f"Error executing query: {str(e)}")
    
    async def handle_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理config请求（占位实现）
        
        Args:
            params: 配置参数字典
            
        Returns:
            响应数据字典
        """
        # TODO: 在Phase 1中集成ConfigManager
        # 目前返回占位响应
        return {
            "updated": True,
            "message": "Config handler not yet implemented"
        }
    
    async def handle_behavior(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理behavior请求
        
        接收前端发送的用户行为数据，调用BehaviorAnalyzer记录行为，
        并跟踪活跃页面以便定期检查干预触发条件。
        
        Requirements:
        - 6.1: THE Behavior_Analyzer SHALL 接收前端发送的用户行为数据
        - 6.2: THE Behavior_Analyzer SHALL 将行为数据存储到SQLite数据库
        
        Args:
            params: 请求参数，应包含：
                - docHash: 文档hash
                - page: 页码
                - eventType: 事件类型 ('page_view', 'text_select', 'scroll')
                - metadata: 可选的额外元数据
            
        Returns:
            响应数据字典，包含：
                - recorded: 是否成功记录
                - eventId: 行为事件ID
            
        Raises:
            ValueError: 缺少必需参数或参数无效
            RuntimeError: BehaviorAnalyzer未初始化
        """
        # 1. 验证必需参数
        required_params = ["docHash", "page", "eventType"]
        for param in required_params:
            if param not in params:
                raise ValueError(f"Missing required parameter: {param}")
        
        # 2. 检查BehaviorAnalyzer是否已初始化
        if self.behavior_analyzer is None:
            raise RuntimeError(
                "BehaviorAnalyzer not initialized. "
                "Please provide behavior_analyzer during IPCHandler initialization."
            )
        
        # 3. 获取参数
        doc_hash = params["docHash"]
        page = params["page"]
        event_type = params["eventType"]
        metadata = params.get("metadata", {})
        
        # 4. 验证参数
        if not doc_hash or not doc_hash.strip():
            raise ValueError("docHash cannot be empty")
        
        if not isinstance(page, int) or page < 0:
            raise ValueError(f"page must be a non-negative integer, got {page}")
        
        valid_event_types = ['page_view', 'text_select', 'scroll']
        if event_type not in valid_event_types:
            raise ValueError(
                f"Invalid eventType: {event_type}. "
                f"Must be one of: {', '.join(valid_event_types)}"
            )
        
        # 5. 调用BehaviorAnalyzer记录行为
        try:
            logger.debug(
                f"Recording behavior: docHash={doc_hash}, page={page}, "
                f"eventType={event_type}"
            )
            
            event = await self.behavior_analyzer.record_behavior(
                doc_hash=doc_hash,
                page=page,
                event_type=event_type,
                metadata=metadata
            )
            
            # 6. 如果是page_view事件，更新活跃页面跟踪
            if event_type == "page_view":
                key = f"{doc_hash}_{page}"
                self._active_pages[key] = {
                    "docHash": doc_hash,
                    "page": page
                }
                
                # 启动干预检查任务（如果尚未启动）
                if self._intervention_task is None or self._intervention_task.done():
                    self._intervention_task = asyncio.create_task(
                        self._periodic_intervention_check()
                    )
            
            logger.debug(f"Behavior recorded successfully: eventId={event.id}")
            
            # 7. 返回成功响应
            return {
                "recorded": True,
                "eventId": event.id
            }
            
        except ValueError as e:
            # 参数验证错误
            raise ValueError(f"Failed to record behavior: {str(e)}")
        except Exception as e:
            # 其他错误（如数据库错误等）
            raise RuntimeError(f"Error recording behavior: {str(e)}")
    
    async def _periodic_intervention_check(self):
        """定期检查干预触发条件
        
        后台任务，每隔一定时间检查所有活跃页面是否需要触发干预。
        
        Requirements:
        - 6.3: WHEN 用户在同一页面停留超过阈值，THE Behavior_Analyzer SHALL 触发主动干预信号
        - 6.4: THE Behavior_Analyzer SHALL 通过IPC向前端发送主动消息推送
        """
        logger.info("Starting periodic intervention check task")
        
        try:
            while True:
                # 等待指定的检查间隔
                await asyncio.sleep(self._intervention_check_interval)
                
                # 如果没有活跃页面，继续等待
                if not self._active_pages:
                    continue
                
                # 检查每个活跃页面
                pages_to_remove = []
                
                for key, page_info in list(self._active_pages.items()):
                    doc_hash = page_info["docHash"]
                    page = page_info["page"]
                    
                    try:
                        # 检查是否应该触发干预
                        should_intervene = await self.behavior_analyzer.check_intervention_trigger(
                            doc_hash=doc_hash,
                            page=page
                        )
                        
                        if should_intervene:
                            logger.info(
                                f"Intervention triggered for {doc_hash} page {page}"
                            )
                            
                            # 发送干预推送
                            await self.behavior_analyzer.send_intervention(
                                doc_hash=doc_hash,
                                page=page,
                                ipc_handler=self
                            )
                            
                            # 从活跃页面列表中移除（已触发干预）
                            pages_to_remove.append(key)
                    
                    except Exception as e:
                        logger.error(
                            f"Error checking intervention for {doc_hash} page {page}: {e}"
                        )
                        # 发生错误时也移除该页面，避免重复错误
                        pages_to_remove.append(key)
                
                # 移除已处理的页面
                for key in pages_to_remove:
                    if key in self._active_pages:
                        del self._active_pages[key]
                
        except asyncio.CancelledError:
            logger.info("Periodic intervention check task cancelled")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in periodic intervention check: {e}")
    
    def stop_intervention_check(self):
        """停止干预检查任务
        
        用于清理资源，例如在测试结束或应用关闭时调用。
        """
        if self._intervention_task and not self._intervention_task.done():
            self._intervention_task.cancel()
            logger.info("Intervention check task stopped")
    
    def _serialize_response(self, response: IPCResponse) -> str:
        """序列化响应为JSON字符串
        
        Args:
            response: IPCResponse对象
            
        Returns:
            JSON格式的响应字符串
        """
        return json.dumps(response.to_dict(), ensure_ascii=False)
    
    def _error_response(self, request_id: str, seq: int, error_message: str) -> str:
        """生成错误响应
        
        Args:
            request_id: 请求ID
            seq: 请求序列号
            error_message: 错误消息
            
        Returns:
            JSON格式的错误响应字符串
        """
        response = IPCResponse(
            id=request_id,
            seq=seq,
            success=False,
            error=error_message
        )
        return self._serialize_response(response)
