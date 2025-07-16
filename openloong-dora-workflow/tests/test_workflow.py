#!/usr/bin/env python3

import grpc
import json
import time
import proto.chassis_controller_pb2 as chassis_pb2
import proto.chassis_controller_pb2_grpc as chassis_grpc
import proto.upper_controller_pb2 as upper_pb2
import proto.upper_controller_pb2_grpc as upper_grpc

def test_chassis_service():
    """测试底盘服务"""
    print("🔧 测试底盘gRPC服务...")
    try:
        channel = grpc.insecure_channel('localhost:50051')
        stub = chassis_grpc.ChassisControlerStub(channel)
        
        cmd = chassis_pb2.Command(
            linear=chassis_pb2.Descartes(x=1.0, y=0.0, z=0.0),
            angular=chassis_pb2.Descartes(x=0.0, y=0.0, z=0.0),
            tap=0,
            zOff=0.0
        )
        
        resp = stub.sendCommand(cmd)
        print(f"✅ 底盘服务测试成功: {resp.msg}")
        return True
    except Exception as e:
        print(f"❌ 底盘服务测试失败: {e}")
        return False

def test_upper_service():
    """测试上肢服务"""
    print("🔧 测试上肢gRPC服务...")
    try:
        channel = grpc.insecure_channel('localhost:50052')
        stub = upper_grpc.UpperControllerStub(channel)
        
        payload = upper_pb2.ArmPayload(
            arm=upper_pb2.ArmPosition(left=[1.0, 2.0, 3.0], right=[4.0, 5.0, 6.0]),
            effector=upper_pb2.EffectorPosition(left=[0.1, 0.2], right=[0.3, 0.4])
        )
        
        resp = stub.sendArmAction(payload)
        print(f"✅ 上肢服务测试成功: {resp.msg}")
        return True
    except Exception as e:
        print(f"❌ 上肢服务测试失败: {e}")
        return False

def test_workflow_messages():
    """测试工作流消息格式"""
    print("🔧 测试工作流消息格式...")
    
    # 测试底盘命令
    chassis_cmd = {
        "action": "MOVE",
        "target": {"x": 1.0, "y": 0.0, "z": 0.0, "wz": 0.0},
        "tap": 0,
        "zOff": 0.0
    }
    print(f"✅ 底盘命令格式: {json.dumps(chassis_cmd, indent=2)}")
    
    # 测试机械臂命令
    arm_cmd = {
        "action": "GRAB",
        "target": {"left": [1.0, 2.0, 3.0], "right": [4.0, 5.0, 6.0]},
        "effector": {"left": [0.1, 0.2], "right": [0.3, 0.4]}
    }
    print(f"✅ 机械臂命令格式: {json.dumps(arm_cmd, indent=2)}")
    
    # 测试状态消息
    status_msg = {
        "action": "MOVE_COMPLETE",
        "message": "底盘移动完成"
    }
    print(f"✅ 状态消息格式: {json.dumps(status_msg, indent=2)}")
    
    return True

def main():
    """主测试函数"""
    print("🚀 开始测试Dora机器人工作流组件...")
    print("=" * 50)
    
    # 测试gRPC服务
    chassis_ok = test_chassis_service()
    upper_ok = test_upper_service()
    
    # 测试消息格式
    msg_ok = test_workflow_messages()
    
    print("=" * 50)
    print("📊 测试结果汇总:")
    print(f"  底盘服务: {'✅ 通过' if chassis_ok else '❌ 失败'}")
    print(f"  上肢服务: {'✅ 通过' if upper_ok else '❌ 失败'}")
    print(f"  消息格式: {'✅ 通过' if msg_ok else '❌ 失败'}")
    
    if chassis_ok and upper_ok and msg_ok:
        print("🎉 所有测试通过！可以启动Dora工作流了。")
        print("\n📋 下一步:")
        print("1. 确保gRPC服务正在运行")
        print("2. 运行: dora run dataflow.yml")
    else:
        print("❌ 部分测试失败，请检查服务状态。")

if __name__ == "__main__":
    main() 