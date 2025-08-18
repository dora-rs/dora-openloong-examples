#!/usr/bin/env python3
# coding=utf-8
"""
龙机器人关节控制客户端
基于dora workflow框架，作为关节控制客户端节点
"""

import json
import time
import sys
import os
import socket
import struct
import numpy as np
from dora import Node

class LoongJntClient:
    def __init__(self, server_ip="127.0.0.1", server_port=8081):
        self.server_ip = server_ip
        self.server_port = server_port
        
        # 初始化关节参数
        self.jnt_num = 31  # 总关节数：左臂7+右臂7+颈2+腰3+左腿6+右腿6
        self.finger_dof_left = 3
        self.finger_dof_right = 3
        
        # 初始化UDP socket
        self.sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sk.settimeout(1.0)  # 设置超时时间
        
        # 初始化dora节点
        self.node = Node()
        print("关节控制客户端节点启动")

    def parse_joint_command(self, command_data):
        """解析关节控制命令，兼容 UInt8Array/bytes/内存视图/整型列表"""
        try:
            payload = command_data
            if type(payload).__name__ == "UInt8Array":
                payload = payload.to_numpy().tobytes().decode("utf-8")
            elif hasattr(payload, "tobytes"):
                payload = payload.tobytes().decode("utf-8")
            elif isinstance(payload, (bytes, bytearray, memoryview)):
                payload = bytes(payload).decode("utf-8")
            elif isinstance(payload, str):
                pass
            elif isinstance(payload, (list, tuple)) and all(isinstance(x, int) for x in payload):
                payload = bytes(payload).decode("utf-8")
            else:
                raise TypeError(f"未知输入类型: {type(payload)}")
            return json.loads(payload)
        except Exception as e:
            print(f"解析关节命令失败: {e}")
            return None

    def pack_control_data(self, command):
        """打包控制数据"""
        # 创建控制数据结构
        checker = 3480  # 约定值
        size = 16 + self.jnt_num * 4 * 5 + (self.finger_dof_left + self.finger_dof_right) * 4
        state = 1 if command.get('state', 1) else 0
        tor_limit_rate = command.get('tor_limit_rate', 0.2)
        filt_rate = command.get('filt_rate', 0.05)
        
        # 获取关节角度
        joint_angles = command.get('joint_angles', [0.0] * self.jnt_num)
        if len(joint_angles) < self.jnt_num:
            joint_angles.extend([0.0] * (self.jnt_num - len(joint_angles)))
        
        # 获取手指角度
        finger_left = command.get('finger_left', [0.0] * self.finger_dof_left)
        finger_right = command.get('finger_right', [0.0] * self.finger_dof_right)
        
        # 打包数据
        buf = struct.pack('2hi', checker, size, state)  # checker, size, state
        buf += struct.pack('ff', tor_limit_rate, filt_rate)  # torLimitRate, filtRate
        buf += struct.pack(f'{self.jnt_num}f', *joint_angles)  # j
        buf += struct.pack(f'{self.jnt_num}f', *([0.0] * self.jnt_num))  # w
        buf += struct.pack(f'{self.jnt_num}f', *([0.0] * self.jnt_num))  # t
        buf += struct.pack(f'{self.jnt_num}f', *([0.0] * self.jnt_num))  # kp
        buf += struct.pack(f'{self.jnt_num}f', *([0.0] * self.jnt_num))  # kd
        buf += struct.pack(f'{self.finger_dof_left}f', *finger_left)  # fingerLeft
        buf += struct.pack(f'{self.finger_dof_right}f', *finger_right)  # fingerRight
        
        return buf

    def unpack_sensor_data(self, data_buf):
        """解包传感器数据"""
        try:
            # 解析基础数据
            offset = 0
            size = struct.unpack('i', data_buf[offset:offset+4])[0]
            offset += 4
            timestamp = struct.unpack('d', data_buf[offset:offset+8])[0]
            offset += 8
            key = struct.unpack('2h', data_buf[offset:offset+4])
            offset += 4
            plan_name = data_buf[offset:offset+16].decode('utf-8').rstrip('\x00')
            offset += 16
            state = struct.unpack('2h', data_buf[offset:offset+4])
            offset += 4
            joy = struct.unpack('4f', data_buf[offset:offset+16])
            offset += 16
            
            # 解析IMU数据
            rpy = struct.unpack('3f', data_buf[offset:offset+12])
            offset += 12
            gyr = struct.unpack('3f', data_buf[offset:offset+12])
            offset += 12
            acc = struct.unpack('3f', data_buf[offset:offset+12])
            offset += 12
            
            # 解析关节数据
            act_j = struct.unpack(f'{self.jnt_num}f', data_buf[offset:offset+self.jnt_num*4])
            offset += self.jnt_num * 4
            act_w = struct.unpack(f'{self.jnt_num}f', data_buf[offset:offset+self.jnt_num*4])
            offset += self.jnt_num * 4
            act_t = struct.unpack(f'{self.jnt_num}f', data_buf[offset:offset+self.jnt_num*4])
            offset += self.jnt_num * 4
            
            # 解析驱动器数据
            drv_temp = struct.unpack(f'{self.jnt_num}h', data_buf[offset:offset+self.jnt_num*2])
            offset += self.jnt_num * 2
            drv_state = struct.unpack(f'{self.jnt_num}h', data_buf[offset:offset+self.jnt_num*2])
            offset += self.jnt_num * 2
            drv_err = struct.unpack(f'{self.jnt_num}h', data_buf[offset:offset+self.jnt_num*2])
            offset += self.jnt_num * 2
            
            # 解析目标关节数据
            tgt_j = struct.unpack(f'{self.jnt_num}f', data_buf[offset:offset+self.jnt_num*4])
            offset += self.jnt_num * 4
            tgt_w = struct.unpack(f'{self.jnt_num}f', data_buf[offset:offset+self.jnt_num*4])
            offset += self.jnt_num * 4
            tgt_t = struct.unpack(f'{self.jnt_num}f', data_buf[offset:offset+self.jnt_num*4])
            offset += self.jnt_num * 4
            
            # 解析手指数据
            act_finger_left = struct.unpack(f'{self.finger_dof_left}f', data_buf[offset:offset+self.finger_dof_left*4])
            offset += self.finger_dof_left * 4
            act_finger_right = struct.unpack(f'{self.finger_dof_right}f', data_buf[offset:offset+self.finger_dof_right*4])
            offset += self.finger_dof_right * 4
            tgt_finger_left = struct.unpack(f'{self.finger_dof_left}f', data_buf[offset:offset+self.finger_dof_left*4])
            offset += self.finger_dof_left * 4
            tgt_finger_right = struct.unpack(f'{self.finger_dof_right}f', data_buf[offset:offset+self.finger_dof_right*4])
            
            return {
                'size': size,
                'timestamp': timestamp,
                'key': key,
                'plan_name': plan_name,
                'state': state,
                'joy': joy,
                'rpy': rpy,
                'gyr': gyr,
                'acc': acc,
                'act_j': act_j,
                'act_w': act_w,
                'act_t': act_t,
                'drv_temp': drv_temp,
                'drv_state': drv_state,
                'drv_err': drv_err,
                'tgt_j': tgt_j,
                'tgt_w': tgt_w,
                'tgt_t': tgt_t,
                'act_finger_left': act_finger_left,
                'act_finger_right': act_finger_right,
                'tgt_finger_left': tgt_finger_left,
                'tgt_finger_right': tgt_finger_right
            }
        except Exception as e:
            print(f"解包传感器数据失败: {e}")
            return None

    def execute_joint_command(self, command):
        """执行关节控制命令"""
        try:
            # 打包控制数据
            ctrl_buf = self.pack_control_data(command)
            
            # 发送控制指令
            self.sk.sendto(ctrl_buf, (self.server_ip, self.server_port))
            
            # 接收传感器数据
            try:
                data_buf, _ = self.sk.recvfrom(2048)
                sensor_data = self.unpack_sensor_data(data_buf)
            except socket.timeout:
                print("接收传感器数据超时")
                sensor_data = None
            
            # 构建状态信息
            if sensor_data:
                status = {
                    "action": command.get("action", "JOINT_CONTROL"),
                    "timestamp": sensor_data['timestamp'],
                    "joint_angles": list(sensor_data['act_j']),
                    "target_angles": list(sensor_data['tgt_j']),
                    "joint_velocities": list(sensor_data['act_w']),
                    "joint_torques": list(sensor_data['act_t']),
                    "finger_left": list(sensor_data['act_finger_left']),
                    "finger_right": list(sensor_data['act_finger_right']),
                    "drv_temp": list(sensor_data['drv_temp']),
                    "drv_state": list(sensor_data['drv_state']),
                    "drv_error": list(sensor_data['drv_err']),
                    "status": "SUCCESS"
                }
            else:
                status = {
                    "action": command.get("action", "JOINT_CONTROL"),
                    "timestamp": time.time(),
                    "joint_angles": [0.0] * self.jnt_num,
                    "target_angles": [0.0] * self.jnt_num,
                    "joint_velocities": [0.0] * self.jnt_num,
                    "joint_torques": [0.0] * self.jnt_num,
                    "finger_left": [0.0] * self.finger_dof_left,
                    "finger_right": [0.0] * self.finger_dof_right,
                    "drv_temp": [0] * self.jnt_num,
                    "drv_state": [0] * self.jnt_num,
                    "drv_error": [0] * self.jnt_num,
                    "status": "SUCCESS"
                }
            
            return status
            
        except Exception as e:
            print(f"执行关节命令失败: {e}")
            return {
                "action": command.get("action", "JOINT_CONTROL"),
                "status": "ERROR",
                "error": str(e)
            }

    def run(self):
        """运行客户端节点"""
        print("关节控制客户端运行中...")
        
        for event in self.node:
            if event["type"] == "INPUT":
                if event["id"] == "joint_command":
                    raw = event["value"]
                    print("收到关节控制命令")
                    
                    # 解析命令
                    command = self.parse_joint_command(raw)
                    if command:
                        # 执行命令
                        status = self.execute_joint_command(command)
                        
                        # 发送状态
                        status_json = json.dumps(status).encode()
                        self.node.send_output("joint_status", status_json)
                        print(f"关节控制状态: {status['status']}")
                    else:
                        # 发送错误状态
                        error_status = {
                            "action": "JOINT_CONTROL",
                            "status": "ERROR",
                            "error": "Invalid command format"
                        }
                        self.node.send_output("joint_status", json.dumps(error_status).encode())

if __name__ == "__main__":
    client = LoongJntClient()
    client.run()

