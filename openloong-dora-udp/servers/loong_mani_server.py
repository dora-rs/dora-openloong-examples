#!/usr/bin/env python3
# coding=utf-8
"""
龙机器人机械臂控制服务端
基于dora workflow框架，提供机械臂控制服务
"""

import socket
import struct
import numpy as np
import time
import sys
import os

# 添加SDK路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sdk.loong_mani_sdk.loong_mani_sdk_udp import maniSdkClass, maniSdkCtrlDataClass, maniSdkSensDataClass

class LoongManiServer:
    def __init__(self, ip="127.0.0.1", port=8080):
        self.ip = ip
        self.port = port
        self.sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sk.bind((self.ip, self.port))
        print(f"龙机器人机械臂控制服务端启动，监听 {ip}:{port}")

        # 初始化机械臂参数
        self.jnt_num = 12  # 总关节数
        self.finger_dof_left = 3
        self.finger_dof_right = 3
        self.arm_dof = 7
        self.neck_dof = 2
        self.lumbar_dof = 1
        
        # 初始化SDK
        self.sdk = maniSdkClass(
            ip=ip,
            port=port,
            jntNum=self.jnt_num,
            fingerDofLeft=self.finger_dof_left,
            fingerDofRight=self.finger_dof_right
        )
        
        # 初始化传感器数据
        self.sens = maniSdkSensDataClass(self.jnt_num, self.finger_dof_left, self.finger_dof_right)

    def generate_mani_sens_data(self):
        """生成机械臂传感器数据"""
        # 模拟机械臂数据
        current_time = time.time()
        
        # 更新传感器数据
        self.sens.dataSize = np.int32(1024)
        self.sens.timestamp = np.float64(current_time)
        self.sens.key = np.array([1, 2], np.int16)
        self.sens.planName = "mani_plan"  # 字符串类型
        self.sens.state = np.array([0, 1], np.int16)
        self.sens.joy = np.array([0.1, -0.2, 0.3, -0.4], np.float32)
        
        # IMU数据
        self.sens.rpy = np.array([0.05, -0.02, 0.01], np.float32)
        self.sens.gyr = np.array([0.01, 0.02, -0.01], np.float32)
        self.sens.acc = np.array([9.8, 0.1, -0.2], np.float32)
        
        # 关节数据
        self.sens.actJ = np.array([i * 0.1 + 0.01 for i in range(self.jnt_num)], np.float32)
        self.sens.actW = np.array([0.02 * i for i in range(self.jnt_num)], np.float32)
        self.sens.actT = np.array([0.5 * i for i in range(self.jnt_num)], np.float32)
        self.sens.tgtJ = np.array([i * 0.1 for i in range(self.jnt_num)], np.float32)
        self.sens.tgtW = np.array([0.02 * i for i in range(self.jnt_num)], np.float32)
        self.sens.tgtT = np.array([0.5 * i for i in range(self.jnt_num)], np.float32)
        
        # 驱动器数据
        self.sens.drvTemp = np.array([30 + i for i in range(self.jnt_num)], np.int16)
        self.sens.drvState = np.array([0] * self.jnt_num, np.int16)
        self.sens.drvErr = np.array([0] * self.jnt_num, np.int16)
        
        # 手指数据
        self.sens.actFingerLeft = np.array([0.3, 0.3, 0.3], np.float32)
        self.sens.actFingerRight = np.array([0.2, 0.2, 0.2], np.float32)
        self.sens.tgtFingerLeft = np.array([0.3, 0.3, 0.3], np.float32)
        self.sens.tgtFingerRight = np.array([0.2, 0.2, 0.2], np.float32)
        
        # 末端数据
        self.sens.actTipPRpy2B = np.array([[0.4, 0.3, 0.1, 0, 0, 0], [0.2, -0.3, 0.1, 0, 0, 0]], np.float32)
        self.sens.actTipVW2B = np.zeros((2, 6), np.float32)
        self.sens.actTipFM2B = np.zeros((2, 6), np.float32)
        self.sens.tgtTipPRpy2B = np.array([[0.4, 0.3, 0.1, 0, 0, 0], [0.2, -0.3, 0.1, 0, 0, 0]], np.float32)
        self.sens.tgtTipVW2B = np.zeros((2, 6), np.float32)
        self.sens.tgtTipFM2B = np.zeros((2, 6), np.float32)
        
        return self.sens.packSensData()

    def parse_control_command(self, ctrl_buf):
        """解析机械臂控制指令"""
        if len(ctrl_buf) < 12:
            return None
            
        # 解析基础控制参数
        base_ctrl = struct.unpack('6h', ctrl_buf[:12])
        ctrl = maniSdkCtrlDataClass(self.arm_dof, self.finger_dof_left, self.finger_dof_right, self.neck_dof, self.lumbar_dof)
        
        ctrl.inCharge = base_ctrl[0]
        ctrl.filtLevel = base_ctrl[1]
        ctrl.armMode = base_ctrl[2]
        ctrl.fingerMode = base_ctrl[3]
        ctrl.neckMode = base_ctrl[4]
        ctrl.lumbarMode = base_ctrl[5]
        
        # 解析机械臂命令数据
        offset = 12
        
        # 解析armCmd (2 * armDof * 4 bytes)
        arm_cmd_size = 2 * self.arm_dof * 4
        if len(ctrl_buf) >= offset + arm_cmd_size:
            arm_cmd_data = struct.unpack(f'{2 * self.arm_dof}f', ctrl_buf[offset:offset + arm_cmd_size])
            ctrl.armCmd = np.array(arm_cmd_data, dtype=np.float32).reshape(2, self.arm_dof)
            offset += arm_cmd_size
        
        # 解析armFM (2 * 6 * 4 bytes)
        arm_fm_size = 2 * 6 * 4
        if len(ctrl_buf) >= offset + arm_fm_size:
            arm_fm_data = struct.unpack('12f', ctrl_buf[offset:offset + arm_fm_size])
            ctrl.armFM = np.array(arm_fm_data, dtype=np.float32).reshape(2, 6)
            offset += arm_fm_size
        
        # 解析手指命令
        finger_left_size = self.finger_dof_left * 4
        if len(ctrl_buf) >= offset + finger_left_size:
            finger_left_data = struct.unpack(f'{self.finger_dof_left}f', ctrl_buf[offset:offset + finger_left_size])
            ctrl.fingerLeft = np.array(finger_left_data, dtype=np.float32)
            offset += finger_left_size
        
        finger_right_size = self.finger_dof_right * 4
        if len(ctrl_buf) >= offset + finger_right_size:
            finger_right_data = struct.unpack(f'{self.finger_dof_right}f', ctrl_buf[offset:offset + finger_right_size])
            ctrl.fingerRight = np.array(finger_right_data, dtype=np.float32)
            offset += finger_right_size
        
        # 解析颈部命令
        neck_size = self.neck_dof * 4
        if len(ctrl_buf) >= offset + neck_size:
            neck_data = struct.unpack(f'{self.neck_dof}f', ctrl_buf[offset:offset + neck_size])
            ctrl.neckCmd = np.array(neck_data, dtype=np.float32)
            offset += neck_size
        
        # 解析腰部命令
        lumbar_size = self.lumbar_dof * 4
        if len(ctrl_buf) >= offset + lumbar_size:
            lumbar_data = struct.unpack(f'{self.lumbar_dof}f', ctrl_buf[offset:offset + lumbar_size])
            ctrl.lumbarCmd = np.array(lumbar_data, dtype=np.float32)
        
        return ctrl

    def run(self):
        """启动服务端，循环接收并响应"""
        print("机械臂控制服务端运行中...")
        
        while True:
            try:
                # 接收客户端指令
                ctrl_buf, client_addr = self.sk.recvfrom(2048)
                print(f"\n收到客户端 {client_addr} 的机械臂控制指令，长度：{len(ctrl_buf)}字节")

                # 解析控制指令
                ctrl = self.parse_control_command(ctrl_buf)
                if ctrl:
                    print(f"解析到控制参数：inCharge={ctrl.inCharge}, armMode={ctrl.armMode}, fingerMode={ctrl.fingerMode}")
                    
                    # 发送控制指令到SDK
                    self.sdk.send(ctrl)
                    
                    # 接收传感器数据
                    sens = self.sdk.recv()
                    if sens.timestamp > 0:
                        print(f"接收到传感器数据，时间戳：{sens.timestamp:.2f}")
                        sens_buf = sens.packSensData()
                    else:
                        # 如果SDK没有数据，生成模拟数据
                        sens_buf = self.generate_mani_sens_data()
                else:
                    # 生成默认传感器数据
                    sens_buf = self.generate_mani_sens_data()

                # 返回传感器数据
                self.sk.sendto(sens_buf, client_addr)
                print("已返回机械臂传感器数据")

            except Exception as e:
                print(f"处理请求时出错：{e}")
                continue

if __name__ == "__main__":
    server = LoongManiServer()
    server.run()

