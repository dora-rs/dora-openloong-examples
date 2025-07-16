#!/usr/bin/env python3
"""
Workflow Coordinator Dora Node
负责协调整个机器人工作流程：移动->抓取->返回
"""

import json
import time
from typing import Dict, Any
from dora import Node


class WorkflowCoordinator:
    def __init__(self):
        """初始化工作流协调器"""
        self.workflow_state = "idle"  # idle, moving, grasping, returning, completed
        self.current_workflow = None
        self.workflow_results = {}
        
        # 工作流配置
        self.workflow_configs = {
            "pick_and_place": {
                "name": "Pick and Place Workflow",
                "steps": ["move_to_target", "grasp_object", "return_home"],
                "params": {
                    "move_to_target": {
                        "target_left_arm": [0.5, 0.0, 0.3],
                        "target_right_arm": [0.5, 0.0, 0.3]
                    },
                    "grasp_object": {
                        "grasp_left_end": [0.0, 0.0, 0.0],
                        "grasp_right_end": [0.0, 0.0, 0.0]
                    },
                    "return_home": {}
                }
            }
        }
    
    def start_workflow(self, workflow_type: str, custom_params: Dict[str, Any] = None) -> str:
        """启动工作流"""
        if workflow_type not in self.workflow_configs:
            raise ValueError(f"Unknown workflow type: {workflow_type}")
        
        workflow_id = f"{workflow_type}_{int(time.time())}"
        config = self.workflow_configs[workflow_type]
        
        # 合并自定义参数
        params = config["params"].copy()
        if custom_params:
            for step, step_params in custom_params.items():
                if step in params:
                    params[step].update(step_params)
        
        self.current_workflow = {
            "id": workflow_id,
            "type": workflow_type,
            "name": config["name"],
            "steps": config["steps"],
            "params": params,
            "current_step": 0,
            "status": "running",
            "start_time": time.time(),
            "results": {}
        }
        
        self.workflow_state = "moving"
        print(f"Started workflow: {workflow_id} ({workflow_type})")
        return workflow_id
    
    def get_next_step(self) -> Dict[str, Any]:
        """获取下一个步骤"""
        if not self.current_workflow:
            return None
        
        workflow = self.current_workflow
        current_step_idx = workflow["current_step"]
        
        if current_step_idx >= len(workflow["steps"]):
            # 工作流完成
            self.workflow_state = "completed"
            workflow["status"] = "completed"
            return None
        
        step_name = workflow["steps"][current_step_idx]
        step_params = workflow["params"].get(step_name, {})
        
        return {
            "step_name": step_name,
            "step_params": step_params,
            "step_index": current_step_idx,
            "total_steps": len(workflow["steps"])
        }
    
    def complete_current_step(self, result: Dict[str, Any]):
        """完成当前步骤"""
        if not self.current_workflow:
            return
        
        workflow = self.current_workflow
        current_step_idx = workflow["current_step"]
        step_name = workflow["steps"][current_step_idx]
        
        # 记录步骤结果
        workflow["results"][step_name] = result
        
        # 移动到下一个步骤
        workflow["current_step"] += 1
        
        # 更新工作流状态
        if step_name == "move_to_target":
            self.workflow_state = "grasping"
        elif step_name == "grasp_object":
            self.workflow_state = "returning"
        elif step_name == "return_home":
            self.workflow_state = "completed"
            workflow["status"] = "completed"
        
        print(f"Completed step: {step_name}, moving to next step")
    
    def fail_current_step(self, error_msg: str):
        """标记当前步骤失败"""
        if not self.current_workflow:
            return
        
        workflow = self.current_workflow
        current_step_idx = workflow["current_step"]
        step_name = workflow["steps"][current_step_idx]
        
        workflow["status"] = "failed"
        workflow["error"] = error_msg
        workflow["failed_step"] = step_name
        
        self.workflow_state = "idle"
        print(f"Failed step: {step_name}, error: {error_msg}")
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """获取工作流状态"""
        if not self.current_workflow:
            return {"status": "no_workflow"}
        
        workflow = self.current_workflow
        progress = (workflow["current_step"] / len(workflow["steps"])) * 100
        
        return {
            "workflow_id": workflow["id"],
            "workflow_type": workflow["type"],
            "workflow_name": workflow["name"],
            "status": workflow["status"],
            "current_step": workflow["current_step"],
            "total_steps": len(workflow["steps"]),
            "progress": progress,
            "state": self.workflow_state,
            "results": workflow["results"],
            "elapsed_time": time.time() - workflow["start_time"]
        }
    
    def reset_workflow(self):
        """重置工作流"""
        if self.current_workflow:
            workflow_id = self.current_workflow["id"]
            self.workflow_results[workflow_id] = self.current_workflow
        
        self.current_workflow = None
        self.workflow_state = "idle"
        print("Workflow reset")


def main():
    """主函数 - 工作流协调节点入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Workflow Coordinator Dora Node")
    parser.add_argument("--name", type=str, default="workflow_coordinator", 
                       help="Node name in dataflow")
    
    args = parser.parse_args()
    
    # 初始化工作流协调器
    coordinator = WorkflowCoordinator()
    node = Node(args.name)
    
    print(f"Workflow Coordinator Node '{args.name}' started")
    
    # 处理 Dora 事件
    for event in node:
        event_type = event["type"]
        
        if event_type == "INPUT":
            event_id = event["id"]
            data = event["value"]
            
            try:
                # 解析输入数据
                if isinstance(data, bytes):
                    command = json.loads(data.decode('utf-8'))
                else:
                    command = data
                
                # 处理不同类型的命令
                if command.get("cmd") == "start_workflow":
                    # 启动工作流
                    workflow_type = command.get("workflow_type", "pick_and_place")
                    custom_params = command.get("params", {})
                    
                    try:
                        workflow_id = coordinator.start_workflow(workflow_type, custom_params)
                        result = {
                            "succeeded": True,
                            "workflow_id": workflow_id,
                            "message": f"Workflow {workflow_type} started"
                        }
                    except Exception as e:
                        result = {
                            "succeeded": False,
                            "error": str(e)
                        }
                
                elif command.get("cmd") == "get_next_step":
                    # 获取下一个步骤
                    next_step = coordinator.get_next_step()
                    if next_step:
                        result = {
                            "succeeded": True,
                            "next_step": next_step
                        }
                    else:
                        result = {
                            "succeeded": False,
                            "message": "No next step available"
                        }
                
                elif command.get("cmd") == "complete_step":
                    # 完成当前步骤
                    step_result = command.get("result", {})
                    coordinator.complete_current_step(step_result)
                    
                    result = {
                        "succeeded": True,
                        "message": "Step completed"
                    }
                
                elif command.get("cmd") == "fail_step":
                    # 标记步骤失败
                    error_msg = command.get("error", "Unknown error")
                    coordinator.fail_current_step(error_msg)
                    
                    result = {
                        "succeeded": False,
                        "message": f"Step failed: {error_msg}"
                    }
                
                elif command.get("cmd") == "get_status":
                    # 获取工作流状态
                    status = coordinator.get_workflow_status()
                    result = {
                        "succeeded": True,
                        "status": status
                    }
                
                elif command.get("cmd") == "reset_workflow":
                    # 重置工作流
                    coordinator.reset_workflow()
                    result = {
                        "succeeded": True,
                        "message": "Workflow reset"
                    }
                
                elif command.get("cmd") == "auto_execute":
                    # 自动执行工作流
                    workflow_type = command.get("workflow_type", "pick_and_place")
                    custom_params = command.get("params", {})
                    
                    try:
                        workflow_id = coordinator.start_workflow(workflow_type, custom_params)
                        
                        # 发送工作流启动通知
                        node.send_output("workflow_started", json.dumps({
                            "workflow_id": workflow_id,
                            "workflow_type": workflow_type
                        }).encode('utf-8'))
                        
                        result = {
                            "succeeded": True,
                            "workflow_id": workflow_id,
                            "message": f"Auto-executing workflow: {workflow_type}"
                        }
                    except Exception as e:
                        result = {
                            "succeeded": False,
                            "error": str(e)
                        }
                
                else:
                    result = {
                        "succeeded": False,
                        "message": f"Unknown command: {command.get('cmd')}"
                    }
                
                # 发送结果
                node.send_output("result", json.dumps(result).encode('utf-8'))
                
            except Exception as e:
                error_result = {"succeeded": False, "msg": str(e)}
                node.send_output("result", json.dumps(error_result).encode('utf-8'))
        
        elif event_type == "ERROR":
            print(f"Received dora error: {event['error']}")


if __name__ == "__main__":
    main() 