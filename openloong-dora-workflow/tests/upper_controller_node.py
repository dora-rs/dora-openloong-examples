#!/usr/bin/env python3
"""
Upper Controller Dora Node
封装 gRPC 客户端，提供机器人上体控制功能
"""

import grpc
import json
import time
from typing import Dict, Any
from dora import Node
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import proto.upper_controller_pb2 as upper_controller_pb2
import proto.upper_controller_pb2_grpc as upper_controller_pb2_grpc
from google.protobuf import empty_pb2


class UpperControllerNode:
    def __init__(self, grpc_server: str = "localhost:50052"):
        """初始化 gRPC 客户端连接"""
        self.grpc_server = grpc_server
        self.channel = None
        self.stub = None
        self.connect()
    
    def connect(self):
        """建立 gRPC 连接"""
        try:
            self.channel = grpc.insecure_channel(self.grpc_server)
            self.stub = upper_controller_pb2_grpc.UpperControllerStub(self.channel)
            print(f"Connected to gRPC server at {self.grpc_server}")
        except Exception as e:
            print(f"Failed to connect to gRPC server: {e}")
            raise
    
    def send_end_action(self, left_end: list, right_end: list, 
                       left_effector: list, right_effector: list) -> Dict[str, Any]:
        """发送末端执行器动作"""
        try:
            end_payload = upper_controller_pb2.EndPayload(
                end=upper_controller_pb2.EndPose(left=left_end, right=right_end),
                effector=upper_controller_pb2.EffectorPosition(
                    left=left_effector, right=right_effector
                )
            )
            resp = self.stub.sendEndAction(end_payload)
            return {
                "succeeded": resp.succeeded,
                "msg": resp.msg
            }
        except Exception as e:
            return {"succeeded": False, "msg": str(e)}
    
    def recv_end_state(self) -> Dict[str, Any]:
        """接收末端执行器状态"""
        try:
            end_state = self.stub.recvEndState(empty_pb2.Empty())
            return {
                "succeeded": True,
                "end": {
                    "left": list(end_state.end.left),
                    "right": list(end_state.end.right)
                },
                "effector": {
                    "left": list(end_state.effector.left),
                    "right": list(end_state.effector.right)
                }
            }
        except Exception as e:
            return {"succeeded": False, "msg": str(e)}
    
    def send_arm_action(self, left_arm: list, right_arm: list,
                       left_effector: list, right_effector: list) -> Dict[str, Any]:
        """发送机械臂动作"""
        try:
            arm_payload = upper_controller_pb2.ArmPayload(
                arm=upper_controller_pb2.ArmPosition(left=left_arm, right=right_arm),
                effector=upper_controller_pb2.EffectorPosition(
                    left=left_effector, right=right_effector
                )
            )
            resp = self.stub.sendArmAction(arm_payload)
            return {
                "succeeded": resp.succeeded,
                "msg": resp.msg
            }
        except Exception as e:
            return {"succeeded": False, "msg": str(e)}
    
    def recv_arm_state(self) -> Dict[str, Any]:
        """接收机械臂状态"""
        try:
            arm_state = self.stub.recvArmState(empty_pb2.Empty())
            return {
                "succeeded": True,
                "arm": {
                    "left": list(arm_state.arm.left),
                    "right": list(arm_state.arm.right)
                },
                "effector": {
                    "left": list(arm_state.effector.left),
                    "right": list(arm_state.effector.right)
                }
            }
        except Exception as e:
            return {"succeeded": False, "msg": str(e)}
    
    def set_config(self, config: Dict[str, int]) -> Dict[str, Any]:
        """设置配置"""
        try:
            config_msg = upper_controller_pb2.Config(
                incharge=config.get("incharge", 0),
                filter_level=config.get("filter_level", 0),
                arm_mode=config.get("arm_mode", 0),
                digit_mode=config.get("digit_mode", 0),
                neck_mode=config.get("neck_mode", 0),
                waist_mode=config.get("waist_mode", 0)
            )
            resp = self.stub.setConfig(config_msg)
            return {
                "succeeded": resp.succeeded,
                "msg": resp.msg
            }
        except Exception as e:
            return {"succeeded": False, "msg": str(e)}
    
    def get_config(self) -> Dict[str, Any]:
        """获取配置"""
        try:
            config_resp = self.stub.getConfig(empty_pb2.Empty())
            return {
                "succeeded": True,
                "config": {
                    "incharge": config_resp.incharge,
                    "filter_level": config_resp.filter_level,
                    "arm_mode": config_resp.arm_mode,
                    "digit_mode": config_resp.digit_mode,
                    "neck_mode": config_resp.neck_mode,
                    "waist_mode": config_resp.waist_mode
                }
            }
        except Exception as e:
            return {"succeeded": False, "msg": str(e)}
    
    def set_neck_pose(self, neck_pose: list) -> Dict[str, Any]:
        """设置颈部姿态"""
        try:
            neck_msg = upper_controller_pb2.NeckPose(neck=neck_pose)
            resp = self.stub.setNeckPose(neck_msg)
            return {
                "succeeded": resp.succeeded,
                "msg": resp.msg
            }
        except Exception as e:
            return {"succeeded": False, "msg": str(e)}
    
    def get_neck_pose(self) -> Dict[str, Any]:
        """获取颈部姿态"""
        try:
            neck_pose_resp = self.stub.getNeckPose(empty_pb2.Empty())
            return {
                "succeeded": True,
                "neck": list(neck_pose_resp.neck)
            }
        except Exception as e:
            return {"succeeded": False, "msg": str(e)}
    
    def set_waist_pose(self, waist_pose: list) -> Dict[str, Any]:
        """设置腰部姿态"""
        try:
            waist_msg = upper_controller_pb2.WaistPose(waist=waist_pose)
            resp = self.stub.setWaistPose(waist_msg)
            return {
                "succeeded": resp.succeeded,
                "msg": resp.msg
            }
        except Exception as e:
            return {"succeeded": False, "msg": str(e)}
    
    def get_waist_pose(self) -> Dict[str, Any]:
        """获取腰部姿态"""
        try:
            waist_pose_resp = self.stub.getWaistPose(empty_pb2.Empty())
            return {
                "succeeded": True,
                "waist": list(waist_pose_resp.waist)
            }
        except Exception as e:
            return {"succeeded": False, "msg": str(e)}


def main():
    """主函数 - Dora 节点入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Upper Controller Dora Node")
    parser.add_argument("--name", type=str, default="upper_controller", 
                       help="Node name in dataflow")
    parser.add_argument("--grpc-server", type=str, default="localhost:50052",
                       help="gRPC server address")
    
    args = parser.parse_args()
    
    # 初始化 gRPC 客户端
    controller = UpperControllerNode(args.grpc_server)
    node = Node(args.name)
    
    print(f"Upper Controller Node '{args.name}' started")
    
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
                
                # 根据命令类型执行相应操作
                if command.get("action") == "send_end_action":
                    result = controller.send_end_action(
                        command.get("left_end", []),
                        command.get("right_end", []),
                        command.get("left_effector", []),
                        command.get("right_effector", [])
                    )
                
                elif command.get("action") == "recv_end_state":
                    result = controller.recv_end_state()
                
                elif command.get("action") == "send_arm_action":
                    result = controller.send_arm_action(
                        command.get("left_arm", []),
                        command.get("right_arm", []),
                        command.get("left_effector", []),
                        command.get("right_effector", [])
                    )
                
                elif command.get("action") == "recv_arm_state":
                    result = controller.recv_arm_state()
                
                elif command.get("action") == "set_config":
                    result = controller.set_config(command.get("config", {}))
                
                elif command.get("action") == "get_config":
                    result = controller.get_config()
                
                elif command.get("action") == "set_neck_pose":
                    result = controller.set_neck_pose(command.get("neck_pose", []))
                
                elif command.get("action") == "get_neck_pose":
                    result = controller.get_neck_pose()
                
                elif command.get("action") == "set_waist_pose":
                    result = controller.set_waist_pose(command.get("waist_pose", []))
                
                elif command.get("action") == "get_waist_pose":
                    result = controller.get_waist_pose()
                
                else:
                    result = {"succeeded": False, "msg": f"Unknown action: {command.get('action')}"}
                
                # 发送结果
                node.send_output("result", json.dumps(result).encode('utf-8'))
                
            except Exception as e:
                error_result = {"succeeded": False, "msg": str(e)}
                node.send_output("result", json.dumps(error_result).encode('utf-8'))
        
        elif event_type == "ERROR":
            print(f"Received dora error: {event['error']}")


if __name__ == "__main__":
    main() 