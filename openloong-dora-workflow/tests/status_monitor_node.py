#!/usr/bin/env python3
"""
Status Monitor Dora Node
负责监控机器人状态，进行条件判断和任务协调
"""

import json
import time
from typing import Dict, Any
from dora import Node


class StatusMonitor:
    def __init__(self):
        """初始化状态监控器"""
        self.robot_status = {
            "arm_state": None,
            "end_state": None,
            "neck_pose": None,
            "waist_pose": None,
            "last_update": None
        }
        self.task_status = {
            "current_task": None,
            "task_progress": 0.0,
            "task_start_time": None
        }
        self.conditions = {
            "arm_reached_target": False,
            "grasp_successful": False,
            "return_completed": False
        }
        
        # 状态阈值配置
        self.thresholds = {
            "position_tolerance": 0.05,  # 位置误差容忍度
            "timeout_duration": 30.0,    # 任务超时时间（秒）
            "grasp_force_threshold": 0.1  # 抓取力阈值
        }
    
    def update_robot_status(self, status_type: str, status_data: Dict[str, Any]):
        """更新机器人状态"""
        self.robot_status[status_type] = status_data
        self.robot_status["last_update"] = time.time()
        
        # 根据状态更新条件判断
        self._update_conditions()
    
    def update_task_status(self, task_info: Dict[str, Any]):
        """更新任务状态"""
        self.task_status.update(task_info)
        if "task_start_time" not in task_info:
            self.task_status["task_start_time"] = time.time()
    
    def _update_conditions(self):
        """更新条件判断"""
        # 检查机械臂是否到达目标位置
        if self.robot_status["arm_state"]:
            arm_data = self.robot_status["arm_state"]
            if arm_data.get("succeeded"):
                # 这里可以添加更复杂的位置检查逻辑
                self.conditions["arm_reached_target"] = True
        
        # 检查抓取是否成功
        if self.robot_status["end_state"]:
            end_data = self.robot_status["end_state"]
            if end_data.get("succeeded"):
                # 这里可以添加抓取力检查逻辑
                self.conditions["grasp_successful"] = True
        
        # 检查返回是否完成
        if self.task_status["current_task"]:
            task_type = self.task_status["current_task"].get("type")
            if task_type == "return_home" and self.conditions["arm_reached_target"]:
                self.conditions["return_completed"] = True
    
    def check_task_completion(self) -> Dict[str, Any]:
        """检查任务完成状态"""
        current_task = self.task_status["current_task"]
        if not current_task:
            return {"completed": False, "reason": "No current task"}
        
        task_type = current_task.get("type")
        task_id = current_task.get("id")
        
        # 检查任务超时
        if self.task_status["task_start_time"]:
            elapsed_time = time.time() - self.task_status["task_start_time"]
            if elapsed_time > self.thresholds["timeout_duration"]:
                return {
                    "completed": True,
                    "success": False,
                    "reason": "Task timeout",
                    "task_id": task_id
                }
        
        # 根据任务类型检查完成条件
        if task_type == "move_to_target":
            if self.conditions["arm_reached_target"]:
                return {
                    "completed": True,
                    "success": True,
                    "reason": "Arm reached target position",
                    "task_id": task_id
                }
        
        elif task_type == "grasp_object":
            if self.conditions["grasp_successful"]:
                return {
                    "completed": True,
                    "success": True,
                    "reason": "Grasp successful",
                    "task_id": task_id
                }
        
        elif task_type == "return_home":
            if self.conditions["return_completed"]:
                return {
                    "completed": True,
                    "success": True,
                    "reason": "Return to home position completed",
                    "task_id": task_id
                }
        
        return {"completed": False, "reason": "Task still in progress"}
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            "robot_status": self.robot_status,
            "task_status": self.task_status,
            "conditions": self.conditions,
            "thresholds": self.thresholds
        }
    
    def reset_conditions(self):
        """重置条件状态"""
        self.conditions = {
            "arm_reached_target": False,
            "grasp_successful": False,
            "return_completed": False
        }
    
    def should_proceed_to_next_task(self) -> bool:
        """判断是否应该进行下一个任务"""
        completion_check = self.check_task_completion()
        return completion_check["completed"] and completion_check["success"]


def main():
    """主函数 - 状态监控节点入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Status Monitor Dora Node")
    parser.add_argument("--name", type=str, default="status_monitor", 
                       help="Node name in dataflow")
    
    args = parser.parse_args()
    
    # 初始化状态监控器
    monitor = StatusMonitor()
    node = Node(args.name)
    
    print(f"Status Monitor Node '{args.name}' started")
    
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
                if command.get("cmd") == "update_robot_status":
                    # 更新机器人状态
                    status_type = command.get("status_type")
                    status_data = command.get("status_data", {})
                    monitor.update_robot_status(status_type, status_data)
                    
                    result = {
                        "succeeded": True,
                        "message": f"Robot status updated: {status_type}"
                    }
                
                elif command.get("cmd") == "update_task_status":
                    # 更新任务状态
                    task_info = command.get("task_info", {})
                    monitor.update_task_status(task_info)
                    
                    result = {
                        "succeeded": True,
                        "message": "Task status updated"
                    }
                
                elif command.get("cmd") == "check_completion":
                    # 检查任务完成状态
                    completion = monitor.check_task_completion()
                    result = {
                        "succeeded": True,
                        "completion": completion
                    }
                
                elif command.get("cmd") == "get_system_status":
                    # 获取系统状态
                    status = monitor.get_system_status()
                    result = {
                        "succeeded": True,
                        "status": status
                    }
                
                elif command.get("cmd") == "reset_conditions":
                    # 重置条件状态
                    monitor.reset_conditions()
                    result = {
                        "succeeded": True,
                        "message": "Conditions reset"
                    }
                
                elif command.get("cmd") == "should_proceed":
                    # 判断是否应该进行下一个任务
                    should_proceed = monitor.should_proceed_to_next_task()
                    result = {
                        "succeeded": True,
                        "should_proceed": should_proceed
                    }
                
                elif command.get("cmd") == "monitor_continuously":
                    # 连续监控模式
                    while True:
                        completion = monitor.check_task_completion()
                        if completion["completed"]:
                            # 发送任务完成通知
                            if completion["success"]:
                                node.send_output("task_completed", json.dumps({
                                    "task_id": completion["task_id"],
                                    "result": {"status": "success"}
                                }).encode('utf-8'))
                            else:
                                node.send_output("task_failed", json.dumps({
                                    "task_id": completion["task_id"],
                                    "error": completion["reason"]
                                }).encode('utf-8'))
                            
                            # 重置条件
                            monitor.reset_conditions()
                        
                        # 检查是否应该进行下一个任务
                        if monitor.should_proceed_to_next_task():
                            node.send_output("proceed_to_next", json.dumps({
                                "ready": True
                            }).encode('utf-8'))
                        
                        time.sleep(0.1)  # 100ms 检查间隔
                    
                    result = {"succeeded": True, "message": "Continuous monitoring started"}
                
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