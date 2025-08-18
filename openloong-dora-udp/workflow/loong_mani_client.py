#!/usr/bin/env python3
# coding=utf-8
"""
龙机器人机械臂控制客户端
基于dora workflow框架，作为机械臂控制客户端节点
"""

import json
import time
import sys
import os
import socket
import struct
import numpy as np
from dora import Node

class LoongManiClient:
    def __init__(self, server_ip="127.0.0.1", server_port=8080):
        self.server_ip = server_ip
        self.server_port = server_port
        
        # 初始化机械臂参数
        self.jnt_num = 12  # 总关节数
        self.finger_dof_left = 3
        self.finger_dof_right = 3
        self.arm_dof = 7
        self.neck_dof = 2
        self.lumbar_dof = 1
        
        # 初始化UDP socket
        self.sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sk.settimeout(1.0)  # 设置超时时间
        
        # 初始化dora节点
        self.node = Node()
        print("机械臂控制客户端节点启动")

    def parse_mani_command(self, command_data):
        """解析机械臂控制命令，兼容 UInt8Array/bytes/内存视图/整型列表"""
        try:
            payload = command_data
            # dora 可能传来的是 pyarrow UInt8Array
            if type(payload).__name__ == "UInt8Array":
                payload = payload.to_numpy().tobytes().decode("utf-8")
            elif hasattr(payload, "tobytes"):
                payload = payload.tobytes().decode("utf-8")
            elif isinstance(payload, (bytes, bytearray, memoryview)):
                payload = bytes(payload).decode("utf-8")
            elif isinstance(payload, str):
                pass
            elif isinstance(payload, (list, tuple)) and all(isinstance(x, int) for x in payload):
                # 兼容整型列表（ASCII 码）
                payload = bytes(payload).decode("utf-8")
            else:
                raise TypeError(f"未知输入类型: {type(payload)}")

            return json.loads(payload)
        except Exception as e:
            print(f"解析机械臂命令失败: {e}")
            return None

    def pack_control_data(self, command):
        """打包控制数据"""
        # 获取控制参数
        in_charge = command.get('in_charge', 1)
        filt_level = command.get('filt_level', 2)
        arm_mode = command.get('arm_mode', 0)
        finger_mode = command.get('finger_mode', 0)
        neck_mode = command.get('neck_mode', 5)
        lumbar_mode = command.get('lumbar_mode', 0)
        
        # 获取手臂命令
        arm_cmd = command.get('arm_cmd', [[0.4, 0.3, 0.1, 0.0, 0.0, 0.0, 0.5], [0.2, -0.3, 0.1, 0.0, 0.0, 0.0, 0.5]])
        if len(arm_cmd) < 2:
            arm_cmd = [[0.0] * self.arm_dof, [0.0] * self.arm_dof]
        elif len(arm_cmd[0]) < self.arm_dof:
            arm_cmd[0].extend([0.0] * (self.arm_dof - len(arm_cmd[0])))
        if len(arm_cmd[1]) < self.arm_dof:
            arm_cmd[1].extend([0.0] * (self.arm_dof - len(arm_cmd[1])))
        
        # 获取手臂前馈力
        arm_fm = command.get('arm_fm', [[0.0] * 6, [0.0] * 6])
        if len(arm_fm) < 2:
            arm_fm = [[0.0] * 6, [0.0] * 6]
        elif len(arm_fm[0]) < 6:
            arm_fm[0].extend([0.0] * (6 - len(arm_fm[0])))
        if len(arm_fm[1]) < 6:
            arm_fm[1].extend([0.0] * (6 - len(arm_fm[1])))
        
        # 获取手指命令
        finger_left = command.get('finger_left', [0.0] * self.finger_dof_left)
        finger_right = command.get('finger_right', [0.0] * self.finger_dof_right)
        if len(finger_left) < self.finger_dof_left:
            finger_left.extend([0.0] * (self.finger_dof_left - len(finger_left)))
        if len(finger_right) < self.finger_dof_right:
            finger_right.extend([0.0] * (self.finger_dof_right - len(finger_right)))
        
        # 获取颈部命令
        neck_cmd = command.get('neck_cmd', [0.0] * self.neck_dof)
        if len(neck_cmd) < self.neck_dof:
            neck_cmd.extend([0.0] * (self.neck_dof - len(neck_cmd)))
        
        # 获取腰部命令
        lumbar_cmd = command.get('lumbar_cmd', [0.0] * self.lumbar_dof)
        if len(lumbar_cmd) < self.lumbar_dof:
            lumbar_cmd.extend([0.0] * (self.lumbar_dof - len(lumbar_cmd)))
        
        # 打包数据
        buf = struct.pack('6h', in_charge, filt_level, arm_mode, finger_mode, neck_mode, lumbar_mode)
        buf += struct.pack(f'{2 * self.arm_dof}f', *arm_cmd[0], *arm_cmd[1])  # armCmd
        buf += struct.pack('12f', *arm_fm[0], *arm_fm[1])  # armFM
        buf += struct.pack(f'{self.finger_dof_left}f', *finger_left)  # fingerLeft
        buf += struct.pack(f'{self.finger_dof_right}f', *finger_right)  # fingerRight
        buf += struct.pack(f'{self.neck_dof}f', *neck_cmd)  # neckCmd
        buf += struct.pack(f'{self.lumbar_dof}f', *lumbar_cmd)  # lumbarCmd
        
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
            offset += self.finger_dof_right * 4
            
            # 解析末端数据
            act_tip_left = struct.unpack('6f', data_buf[offset:offset+24])
            offset += 24
            act_tip_right = struct.unpack('6f', data_buf[offset:offset+24])
            offset += 24
            act_tip_vw_left = struct.unpack('6f', data_buf[offset:offset+24])
            offset += 24
            act_tip_vw_right = struct.unpack('6f', data_buf[offset:offset+24])
            offset += 24
            act_tip_fm_left = struct.unpack('6f', data_buf[offset:offset+24])
            offset += 24
            act_tip_fm_right = struct.unpack('6f', data_buf[offset:offset+24])
            offset += 24
            
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
                'tgt_finger_right': tgt_finger_right,
                'act_tip_left': act_tip_left,
                'act_tip_right': act_tip_right,
                'act_tip_vw_left': act_tip_vw_left,
                'act_tip_vw_right': act_tip_vw_right,
                'act_tip_fm_left': act_tip_fm_left,
                'act_tip_fm_right': act_tip_fm_right
            }
        except Exception as e:
            print(f"解包传感器数据失败: {e}")
            return None

    def execute_mani_command(self, command):
        """执行机械臂控制命令"""
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
                    "action": command.get("action", "MANI_CONTROL"),
                    "timestamp": sensor_data['timestamp'],
                    "joint_angles": list(sensor_data['act_j']),
                    "target_angles": list(sensor_data['tgt_j']),
                    "joint_velocities": list(sensor_data['act_w']),
                    "joint_torques": list(sensor_data['act_t']),
                    "finger_left": list(sensor_data['act_finger_left']),
                    "finger_right": list(sensor_data['act_finger_right']),
                    "tip_left_pos": list(sensor_data['act_tip_left']),
                    "tip_right_pos": list(sensor_data['act_tip_right']),
                    "tip_left_vel": list(sensor_data['act_tip_vw_left']),
                    "tip_right_vel": list(sensor_data['act_tip_vw_right']),
                    "tip_left_force": list(sensor_data['act_tip_fm_left']),
                    "tip_right_force": list(sensor_data['act_tip_fm_right']),
                    "drv_temp": list(sensor_data['drv_temp']),
                    "drv_state": list(sensor_data['drv_state']),
                    "drv_error": list(sensor_data['drv_err']),
                    "imu_rpy": list(sensor_data['rpy']),
                    "imu_gyr": list(sensor_data['gyr']),
                    "imu_acc": list(sensor_data['acc']),
                    "status": "SUCCESS"
                }
            else:
                status = {
                    "action": command.get("action", "MANI_CONTROL"),
                    "timestamp": time.time(),
                    "joint_angles": [0.0] * self.jnt_num,
                    "target_angles": [0.0] * self.jnt_num,
                    "joint_velocities": [0.0] * self.jnt_num,
                    "joint_torques": [0.0] * self.jnt_num,
                    "finger_left": [0.0] * self.finger_dof_left,
                    "finger_right": [0.0] * self.finger_dof_right,
                    "tip_left_pos": [0.0] * 6,
                    "tip_right_pos": [0.0] * 6,
                    "tip_left_vel": [0.0] * 6,
                    "tip_right_vel": [0.0] * 6,
                    "tip_left_force": [0.0] * 6,
                    "tip_right_force": [0.0] * 6,
                    "drv_temp": [0] * self.jnt_num,
                    "drv_state": [0] * self.jnt_num,
                    "drv_error": [0] * self.jnt_num,
                    "imu_rpy": [0.0] * 3,
                    "imu_gyr": [0.0] * 3,
                    "imu_acc": [0.0] * 3,
                    "status": "SUCCESS"
                }
            
            return status
            
        except Exception as e:
            print(f"执行机械臂命令失败: {e}")
            return {
                "action": command.get("action", "MANI_CONTROL"),
                "status": "ERROR",
                "error": str(e)
            }

    def run(self):
        """运行客户端节点"""
        print("机械臂控制客户端运行中...")
        
        for event in self.node:
            if event["type"] == "INPUT":
                if event["id"] == "mani_command":
                    raw = event["value"]
                    # 降低日志噪音，不打印巨大数组，只提示收到命令
                    print("收到机械臂控制命令")
                    
                    # 解析命令
                    command = self.parse_mani_command(raw)
                    if command:
                        # 执行命令
                        status = self.execute_mani_command(command)
                        
                        # 发送状态
                        status_json = json.dumps(status).encode()
                        self.node.send_output("mani_status", status_json)
                        print(f"机械臂控制状态: {status['status']}")
                    else:
                        # 发送错误状态
                        error_status = {
                            "action": "MANI_CONTROL",
                            "status": "ERROR",
                            "error": "Invalid command format"
                        }
                        self.node.send_output("mani_status", json.dumps(error_status).encode())

if __name__ == "__main__":
    client = LoongManiClient()
    client.run()

