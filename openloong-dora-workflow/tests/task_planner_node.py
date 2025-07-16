#!/usr/bin/env python3
"""
Task Planner Dora Node
负责机器人任务规划和状态管理
"""

import json
import time
from typing import Dict, Any, List
from dora import Node
from enum import Enum


class TaskState(Enum):
    """任务状态枚举"""
    IDLE = "idle"
    MOVING = "moving"
    GRASPING = "grasping"
    RETURNING = "returning"
    COMPLETED = "completed"
    ERROR = "error"


class TaskPlanner:
    def __init__(self):
        """初始化任务规划器"""
        self.current_state = TaskState.IDLE
        self.task_queue = []
        self.current_task = None
        self.task_results = {}
        
        # 预定义的任务参数
        self.task_configs = {
            "move_to_target": {
                "neck_pose": [0.0, 0.0, 0.0],  # 头部朝向目标
                "waist_pose": [0.0, 0.0, 0.0],  # 腰部姿态
                "arm_pose": {
                    "left": [0.0, 0.0, 0.0],
                    "right": [0.0, 0.0, 0.0]
                },
                "effector_pose": {
                    "left": [0.0, 0.0, 0.0],
                    "right": [0.0, 0.0, 0.0]
                }
            },
            "grasp_object": {
                "neck_pose": [0.0, -0.3, 0.0],  # 低头看物体
                "waist_pose": [0.0, 0.0, 0.0],
                "arm_pose": {
                    "left": [0.5, 0.0, 0.3],  # 伸向物体
                    "right": [0.5, 0.0, 0.3]
                },
                "effector_pose": {
                    "left": [0.0, 0.0, 0.0],
                    "right": [0.0, 0.0, 0.0]
                }
            },
            "return_home": {
                "neck_pose": [0.0, 0.0, 0.0],  # 回到初始姿态
                "waist_pose": [0.0, 0.0, 0.0],
                "arm_pose": {
                    "left": [0.0, 0.0, 0.0],
                    "right": [0.0, 0.0, 0.0]
                },
                "effector_pose": {
                    "left": [0.0, 0.0, 0.0],
                    "right": [0.0, 0.0, 0.0]
                }
            }
        }
    
    def add_task(self, task_type: str, task_params: Dict[str, Any] = None) -> str:
        """添加新任务到队列"""
        task_id = f"{task_type}_{int(time.time())}"
        task = {
            "id": task_id,
            "type": task_type,
            "params": task_params or {},
            "status": "pending",
            "created_at": time.time()
        }
        self.task_queue.append(task)
        print(f"Added task: {task_id} ({task_type})")
        return task_id
    
    def get_next_task(self) -> Dict[str, Any]:
        """获取下一个待执行任务"""
        if self.task_queue and self.current_state == TaskState.IDLE:
            self.current_task = self.task_queue.pop(0)
            self.current_task["status"] = "executing"
            self.current_state = TaskState.MOVING
            return self.current_task
        return None
    
    def update_task_status(self, task_id: str, status: str, result: Dict[str, Any] = None):
        """更新任务状态"""
        if self.current_task and self.current_task["id"] == task_id:
            self.current_task["status"] = status
            if result:
                self.current_task["result"] = result
    
    def complete_current_task(self, result: Dict[str, Any] = None):
        """完成当前任务"""
        if self.current_task:
            self.current_task["status"] = "completed"
            if result:
                self.current_task["result"] = result
            self.task_results[self.current_task["id"]] = self.current_task
            self.current_task = None
            self.current_state = TaskState.IDLE
    
    def fail_current_task(self, error_msg: str):
        """标记当前任务失败"""
        if self.current_task:
            self.current_task["status"] = "failed"
            self.current_task["error"] = error_msg
            self.current_task = None
            self.current_state = TaskState.ERROR
    
    def get_task_config(self, task_type: str) -> Dict[str, Any]:
        """获取任务配置"""
        return self.task_configs.get(task_type, {})
    
    def create_move_command(self, target_pose: Dict[str, Any]) -> Dict[str, Any]:
        """创建移动命令"""
        config = self.get_task_config("move_to_target")
        return {
            "action": "send_arm_action",
            "left_arm": target_pose.get("left_arm", config["arm_pose"]["left"]),
            "right_arm": target_pose.get("right_arm", config["arm_pose"]["right"]),
            "left_effector": target_pose.get("left_effector", config["effector_pose"]["left"]),
            "right_effector": target_pose.get("right_effector", config["effector_pose"]["right"])
        }
    
    def create_grasp_command(self, grasp_params: Dict[str, Any]) -> Dict[str, Any]:
        """创建抓取命令"""
        config = self.get_task_config("grasp_object")
        return {
            "action": "send_end_action",
            "left_end": grasp_params.get("left_end", [0.0, 0.0, 0.0]),
            "right_end": grasp_params.get("right_end", [0.0, 0.0, 0.0]),
            "left_effector": grasp_params.get("left_effector", config["effector_pose"]["left"]),
            "right_effector": grasp_params.get("right_effector", config["effector_pose"]["right"])
        }
    
    def create_return_command(self) -> Dict[str, Any]:
        """创建返回命令"""
        config = self.get_task_config("return_home")
        return {
            "action": "send_arm_action",
            "left_arm": config["arm_pose"]["left"],
            "right_arm": config["arm_pose"]["right"],
            "left_effector": config["effector_pose"]["left"],
            "right_effector": config["effector_pose"]["right"]
        }
    
    def create_neck_command(self, pose: List[float]) -> Dict[str, Any]:
        """创建颈部控制命令"""
        return {
            "action": "set_neck_pose",
            "neck_pose": pose
        }
    
    def create_waist_command(self, pose: List[float]) -> Dict[str, Any]:
        """创建腰部控制命令"""
        return {
            "action": "set_waist_pose",
            "waist_pose": pose
        }
    
    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        return {
            "current_state": self.current_state.value,
            "current_task": self.current_task,
            "queue_length": len(self.task_queue),
            "completed_tasks": len(self.task_results)
        }


def main():
    """主函数 - 任务规划节点入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Task Planner Dora Node")
    parser.add_argument("--name", type=str, default="task_planner", 
                       help="Node name in dataflow")
    
    args = parser.parse_args()
    
    # 初始化任务规划器
    planner = TaskPlanner()
    node = Node(args.name)
    
    print(f"Task Planner Node '{args.name}' started")
    
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
                if command.get("cmd") == "add_task":
                    # 添加新任务
                    task_type = command.get("task_type")
                    task_params = command.get("params", {})
                    task_id = planner.add_task(task_type, task_params)
                    
                    result = {
                        "succeeded": True,
                        "task_id": task_id,
                        "message": f"Task {task_type} added to queue"
                    }
                
                elif command.get("cmd") == "get_next_task":
                    # 获取下一个任务
                    next_task = planner.get_next_task()
                    if next_task:
                        # 根据任务类型生成相应的控制命令
                        task_type = next_task["type"]
                        task_params = next_task["params"]
                        
                        if task_type == "move_to_target":
                            control_cmd = planner.create_move_command(task_params)
                            neck_cmd = planner.create_neck_command(
                                planner.get_task_config("move_to_target")["neck_pose"]
                            )
                            waist_cmd = planner.create_waist_command(
                                planner.get_task_config("move_to_target")["waist_pose"]
                            )
                            
                            # 发送多个控制命令
                            node.send_output("control", json.dumps(control_cmd).encode('utf-8'))
                            node.send_output("neck_control", json.dumps(neck_cmd).encode('utf-8'))
                            node.send_output("waist_control", json.dumps(waist_cmd).encode('utf-8'))
                            
                        elif task_type == "grasp_object":
                            control_cmd = planner.create_grasp_command(task_params)
                            neck_cmd = planner.create_neck_command(
                                planner.get_task_config("grasp_object")["neck_pose"]
                            )
                            
                            node.send_output("control", json.dumps(control_cmd).encode('utf-8'))
                            node.send_output("neck_control", json.dumps(neck_cmd).encode('utf-8'))
                            
                        elif task_type == "return_home":
                            control_cmd = planner.create_return_command()
                            neck_cmd = planner.create_neck_command(
                                planner.get_task_config("return_home")["neck_pose"]
                            )
                            waist_cmd = planner.create_waist_command(
                                planner.get_task_config("return_home")["waist_pose"]
                            )
                            
                            node.send_output("control", json.dumps(control_cmd).encode('utf-8'))
                            node.send_output("neck_control", json.dumps(neck_cmd).encode('utf-8'))
                            node.send_output("waist_control", json.dumps(waist_cmd).encode('utf-8'))
                        
                        result = {
                            "succeeded": True,
                            "task": next_task,
                            "message": f"Executing task: {task_type}"
                        }
                    else:
                        result = {
                            "succeeded": False,
                            "message": "No tasks in queue or system busy"
                        }
                
                elif command.get("cmd") == "task_completed":
                    # 任务完成通知
                    task_id = command.get("task_id")
                    task_result = command.get("result", {})
                    planner.complete_current_task(task_result)
                    
                    result = {
                        "succeeded": True,
                        "message": f"Task {task_id} completed"
                    }
                
                elif command.get("cmd") == "task_failed":
                    # 任务失败通知
                    task_id = command.get("task_id")
                    error_msg = command.get("error", "Unknown error")
                    planner.fail_current_task(error_msg)
                    
                    result = {
                        "succeeded": False,
                        "message": f"Task {task_id} failed: {error_msg}"
                    }
                
                elif command.get("cmd") == "get_status":
                    # 获取状态
                    status = planner.get_status()
                    result = {
                        "succeeded": True,
                        "status": status
                    }
                
                elif command.get("cmd") == "create_workflow":
                    # 创建完整工作流
                    workflow_params = command.get("params", {})
                    
                    # 添加移动任务
                    planner.add_task("move_to_target", {
                        "left_arm": workflow_params.get("target_left_arm", [0.5, 0.0, 0.3]),
                        "right_arm": workflow_params.get("target_right_arm", [0.5, 0.0, 0.3])
                    })
                    
                    # 添加抓取任务
                    planner.add_task("grasp_object", {
                        "left_end": workflow_params.get("grasp_left_end", [0.0, 0.0, 0.0]),
                        "right_end": workflow_params.get("grasp_right_end", [0.0, 0.0, 0.0])
                    })
                    
                    # 添加返回任务
                    planner.add_task("return_home", {})
                    
                    result = {
                        "succeeded": True,
                        "message": "Workflow created with move->grasp->return sequence"
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