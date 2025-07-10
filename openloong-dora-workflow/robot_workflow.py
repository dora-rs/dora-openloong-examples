#!/usr/bin/env python3

import dora
from dora import Node
import json
import time

class RobotWorkflowNode(Node):
    def __init__(self):
        super().__init__()
        self.workflow_state = "INIT"
        self.step_count = 0
        self.max_steps = 10  # 防止无限循环
        
    def on_event(self, event):
        if event["type"] == "INPUT":
            if event["id"] == "start_trigger":
                print("🚀 机器人工作流启动")
                self.workflow_state = "MOVE_TO_TARGET"
                self.step_count = 0
                self.send_chassis_command()
                
            elif event["id"] == "next_action":
                action_data = event["value"]
                if isinstance(action_data, bytes):
                    action_data = action_data.decode('utf-8')
                action = json.loads(action_data)
                
                print(f"📋 收到下一步动作: {action}")
                
                if action.get("action") == "MOVE_COMPLETE":
                    self.workflow_state = "CHECK_CONDITION"
                    self.check_condition()
                    
                elif action.get("action") == "CONDITION_MET":
                    self.workflow_state = "GRAB_OBJECT"
                    self.send_grab_command()
                    
                elif action.get("action") == "GRAB_COMPLETE":
                    self.workflow_state = "RETURN_HOME"
                    self.send_return_command()
                    
                elif action.get("action") == "RETURN_COMPLETE":
                    self.workflow_state = "COMPLETE"
                    self.send_completion_status()
                    
                elif action.get("action") == "CONDITION_NOT_MET":
                    self.workflow_state = "COMPLETE"
                    print("❌ 条件不满足，工作流终止")
                    self.send_completion_status()
    
    def send_chassis_command(self):
        """发送底盘移动命令"""
        command = {
            "action": "MOVE",
            "target": {"x": 1.0, "y": 0.0, "z": 0.0, "wz": 0.0},
            "tap": 0,
            "zOff": 0.0
        }
        self.send_output("chassis_command", json.dumps(command).encode())
        print("🔄 发送底盘移动命令")
    
    def check_condition(self):
        """检查条件（模拟到达目标点）"""
        # 模拟条件检查
        condition_met = True  # 可以根据实际情况调整
        if condition_met:
            print("✅ 条件满足，准备抓取")
            self.send_output("workflow_status", json.dumps({"status": "CONDITION_MET"}).encode())
        else:
            print("❌ 条件不满足")
            self.send_output("workflow_status", json.dumps({"status": "CONDITION_NOT_MET"}).encode())
    
    def send_grab_command(self):
        """发送抓取命令"""
        command = {
            "action": "GRAB",
            "target": {"left": [1.0, 2.0, 3.0], "right": [4.0, 5.0, 6.0]},
            "effector": {"left": [0.1, 0.2], "right": [0.3, 0.4]}
        }
        self.send_output("arm_command", json.dumps(command).encode())
        print("🤖 发送机械臂抓取命令")
    
    def send_return_command(self):
        """发送返回命令"""
        command = {
            "action": "RETURN",
            "target": {"left": [0.0, 0.0, 0.0], "right": [0.0, 0.0, 0.0]},
            "effector": {"left": [0.0, 0.0], "right": [0.0, 0.0]}
        }
        self.send_output("arm_command", json.dumps(command).encode())
        print("🏠 发送机械臂返回命令")
    
    def send_completion_status(self):
        """发送完成状态"""
        status = {
            "status": "COMPLETE",
            "message": "机器人工作流执行完成"
        }
        self.send_output("workflow_status", json.dumps(status).encode())
        print("🎉 机器人工作流执行完成")

if __name__ == "__main__":
    node = RobotWorkflowNode()
    node.run() 