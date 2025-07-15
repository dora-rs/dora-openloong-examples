#!/usr/bin/env python3
"""
Logger Dora Node
记录工作流执行日志
"""

import json
import time
from datetime import datetime
from typing import Dict, Any
from dora import Node


class WorkflowLogger:
    def __init__(self, log_file: str = "workflow.log"):
        """初始化日志记录器"""
        self.log_file = log_file
        self.log_entries = []
    
    def _clean_data_for_json(self, data):
        """清理数据以确保可以序列化为JSON"""
        # 处理 pyarrow UInt8Array
        if hasattr(data, '__class__') and 'pyarrow' in str(data.__class__):
            try:
                # 尝试转换为 Python 列表
                if hasattr(data, 'tolist'):
                    return {
                        "data_type": "pyarrow_array",
                        "data_size": len(data),
                        "data_preview": data.tolist()[:10] if len(data) > 10 else data.tolist()
                    }
                else:
                    return {
                        "data_type": "pyarrow_object",
                        "data_size": len(data) if hasattr(data, '__len__') else "unknown",
                        "data_preview": str(data)[:100]
                    }
            except Exception as e:
                return {
                    "data_type": "pyarrow_error",
                    "error": str(e),
                    "data_preview": str(data)[:100]
                }
        
        # 处理二进制数据
        elif isinstance(data, (bytes, bytearray)):
            return {
                "data_type": "binary_data",
                "data_size": len(data),
                "data_preview": data[:100].hex() if len(data) > 100 else data.hex()
            }
        elif isinstance(data, dict):
            return {k: self._clean_data_for_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._clean_data_for_json(item) for item in data]
        elif hasattr(data, '__dict__'):
            return str(data)
        else:
            return data
        
    def log_event(self, event_type: str, event_data: Dict[str, Any]):
        """记录事件"""
        timestamp = datetime.now().isoformat()
        
        # 清理数据以确保可以序列化
        cleaned_data = self._clean_data_for_json(event_data)
        
        log_entry = {
            "timestamp": timestamp,
            "event_type": event_type,
            "data": cleaned_data
        }
        
        self.log_entries.append(log_entry)
        
        # 写入文件
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        
        # 打印到控制台
        print(f"[{timestamp}] {event_type}: {json.dumps(cleaned_data, ensure_ascii=False)}")
    
    def get_log_summary(self) -> Dict[str, Any]:
        """获取日志摘要"""
        if not self.log_entries:
            return {"message": "No log entries"}
        
        event_counts = {}
        for entry in self.log_entries:
            event_type = entry["event_type"]
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        return {
            "total_entries": len(self.log_entries),
            "event_counts": event_counts,
            "first_entry": self.log_entries[0]["timestamp"],
            "last_entry": self.log_entries[-1]["timestamp"]
        }


def main():
    """主函数 - 日志记录节点入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Workflow Logger Dora Node")
    parser.add_argument("--name", type=str, default="logger", 
                       help="Node name in dataflow")
    parser.add_argument("--log-file", type=str, default="workflow.log",
                       help="Log file path")
    
    args = parser.parse_args()
    
    # 初始化日志记录器
    logger = WorkflowLogger(args.log_file)
    node = Node(args.name)
    
    print(f"Workflow Logger Node '{args.name}' started, logging to {args.log_file}")
    
    # 处理 Dora 事件
    for event in node:
        event_type = event["type"]
        
        if event_type == "INPUT":
            event_id = event["id"]
            data = event["value"]
            
            try:
                # 添加调试信息
                print(f"🔍 Logger received event: {event_id}")
                print(f"🔍 Data type: {type(data)}")
                print(f"🔍 Data length: {len(data) if hasattr(data, '__len__') else 'N/A'}")
                
                # 检查是否是 pyarrow 类型
                if hasattr(data, '__class__') and 'pyarrow' in str(data.__class__):
                    print(f"🔍 Detected pyarrow type: {data.__class__}")
                    if hasattr(data, 'tolist'):
                        try:
                            # 尝试转换为 Python 列表
                            python_data = data.tolist()
                            print(f"✅ Converted pyarrow to Python list, length: {len(python_data)}")
                            event_data = {
                                "data_type": "pyarrow_array",
                                "data_size": len(data),
                                "data_preview": python_data[:10] if len(python_data) > 10 else python_data
                            }
                        except Exception as e:
                            print(f"⚠️ Failed to convert pyarrow to list: {e}")
                            event_data = {
                                "data_type": "pyarrow_error",
                                "error": str(e),
                                "data_preview": str(data)[:100]
                            }
                    else:
                        event_data = {
                            "data_type": "pyarrow_object",
                            "data_size": len(data) if hasattr(data, '__len__') else "unknown",
                            "data_preview": str(data)[:100]
                        }
                # 解析输入数据
                elif isinstance(data, bytes):
                    try:
                        event_data = json.loads(data.decode('utf-8'))
                        print(f"✅ Successfully parsed JSON data")
                    except (json.JSONDecodeError, UnicodeDecodeError) as e:
                        print(f"⚠️ JSON decode error: {e}")
                        # 如果是二进制数据，转换为字符串描述
                        event_data = {
                            "data_type": "binary_data",
                            "data_size": len(data),
                            "data_preview": data[:100].hex() if len(data) > 100 else data.hex()
                        }
                else:
                    event_data = data
                    print(f"✅ Using data as-is: {type(event_data)}")
                
                # 根据事件ID记录不同类型的日志
                if event_id == "workflow_started":
                    logger.log_event("WORKFLOW_STARTED", event_data)
                
                elif event_id == "task_completed":
                    logger.log_event("TASK_COMPLETED", event_data)
                
                elif event_id == "task_failed":
                    logger.log_event("TASK_FAILED", event_data)
                
                elif event_id == "step_completed":
                    logger.log_event("STEP_COMPLETED", event_data)
                
                elif event_id == "step_failed":
                    logger.log_event("STEP_FAILED", event_data)
                
                elif event_id == "result":
                    logger.log_event("WORKFLOW_RESULT", event_data)
                
                else:
                    logger.log_event("UNKNOWN_EVENT", {
                        "event_id": event_id,
                        "data": event_data
                    })
                
                # 发送日志摘要
                summary = logger.get_log_summary()
                node.send_output("log", json.dumps(summary).encode('utf-8'))
                
            except Exception as e:
                error_data = {"error": str(e), "event_id": event_id}
                logger.log_event("LOGGER_ERROR", error_data)
                print(f"Logger error processing event {event_id}: {e}")
        
        elif event_type == "ERROR":
            logger.log_event("DORA_ERROR", {"error": event["error"]})


if __name__ == "__main__":
    main() 