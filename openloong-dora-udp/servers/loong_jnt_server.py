#!/usr/bin/env python3
# coding=utf-8
"""
龙机器人关节控制服务端
基于dora workflow框架，提供关节控制服务
"""

import socket
import struct
import numpy as np
import time
import sys
import os

# 添加SDK路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sdk.loong_jnt_sdk.loong_jnt_sdk_udp import jntSdkClass
from sdk.loong_jnt_sdk.loong_jnt_sdk_datas import jntSdkSensDataClass, jntSdkCtrlDataClass

class LoongJntServer:
    def __init__(self, ip="127.0.0.1", port=8081):
        self.ip = ip
        self.port = port
        self.sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sk.bind((self.ip, self.port))
        print(f"龙机器人关节控制服务端启动，监听 {ip}:{port}")

        # 初始化关节参数
        self.jnt_num = 31  # 总关节数：左臂7+右臂7+颈2+腰3+左腿6+右腿6
        self.finger_dof_left = 3
        self.finger_dof_right = 3
        
        # 初始化传感器数据
        self.sens = jntSdkSensDataClass(self.jnt_num, self.finger_dof_left, self.finger_dof_right)

    def generate_jnt_sens_data(self):
        """生成关节传感器数据"""
        # 模拟关节数据
        current_time = time.time()
        
        # 更新传感器数据
        self.sens.size = np.int32(1024)
        self.sens.timestamp = np.float64(current_time)
        self.sens.key = np.array([1, 2], np.int16)
        self.sens.planName = "jnt_plan"  # 字符串类型
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
        
        return self.pack_sens_data()

    def pack_sens_data(self):
        """打包传感器数据"""
        # 构建格式字符串
        fmt_list = [
            'i', 'd', '2h', '16s', '2h', '4f',  # 基础数据
            '3f', '3f', '3f',  # IMU数据
            f'{self.jnt_num}f', f'{self.jnt_num}f', f'{self.jnt_num}f',  # 关节数据
            f'{self.jnt_num}h', f'{self.jnt_num}h', f'{self.jnt_num}h',  # 驱动器数据
            f'{self.jnt_num}f', f'{self.jnt_num}f', f'{self.jnt_num}f',  # 目标关节数据
            f'{self.finger_dof_left}f', f'{self.finger_dof_right}f',  # 手指数据
            f'{self.finger_dof_left}f', f'{self.finger_dof_right}f'
        ]
        
        # 打包数据
        buf = b""
        buf += struct.pack('i', self.sens.size.item())
        buf += struct.pack('d', self.sens.timestamp.item())
        buf += self.sens.key.astype(np.int16).tobytes()
        buf += self.sens.planName.encode('utf-8')[:16].ljust(16, b'\x00')
        buf += self.sens.state.astype(np.int16).tobytes()
        buf += self.sens.joy.astype(np.float32).tobytes()
        buf += self.sens.rpy.astype(np.float32).tobytes()
        buf += self.sens.gyr.astype(np.float32).tobytes()
        buf += self.sens.acc.astype(np.float32).tobytes()
        buf += self.sens.actJ.astype(np.float32).tobytes()
        buf += self.sens.actW.astype(np.float32).tobytes()
        buf += self.sens.actT.astype(np.float32).tobytes()
        buf += self.sens.drvTemp.astype(np.int16).tobytes()
        buf += self.sens.drvState.astype(np.int16).tobytes()
        buf += self.sens.drvErr.astype(np.int16).tobytes()
        buf += self.sens.tgtJ.astype(np.float32).tobytes()
        buf += self.sens.tgtW.astype(np.float32).tobytes()
        buf += self.sens.tgtT.astype(np.float32).tobytes()
        buf += self.sens.actFingerLeft.astype(np.float32).tobytes()
        buf += self.sens.actFingerRight.astype(np.float32).tobytes()
        buf += self.sens.tgtFingerLeft.astype(np.float32).tobytes()
        buf += self.sens.tgtFingerRight.astype(np.float32).tobytes()
        
        return buf

    def parse_control_command(self, ctrl_buf):
        """解析控制指令"""
        if len(ctrl_buf) < 12:
            return None
            
        # 解析基础控制参数
        base_ctrl = struct.unpack('2hi', ctrl_buf[:8])  # checker, size, state
        ctrl = jntSdkCtrlDataClass(self.jnt_num, self.finger_dof_left, self.finger_dof_right)
        
        ctrl.checker = base_ctrl[0]
        ctrl.size = base_ctrl[1]
        ctrl.state = base_ctrl[2]
        
        # 解析其他参数
        offset = 8
        if len(ctrl_buf) > offset:
            # 解析torLimitRate和filtRate
            if len(ctrl_buf) >= offset + 8:
                tor_filt = struct.unpack('ff', ctrl_buf[offset:offset + 8])
                ctrl.torLimitRate = tor_filt[0]
                ctrl.filtRate = tor_filt[1]
                offset += 8
        
        return ctrl

    def run(self):
        """启动服务端，循环接收并响应"""
        print("关节控制服务端运行中...")
        
        while True:
            try:
                # 接收客户端指令
                ctrl_buf, client_addr = self.sk.recvfrom(2048)
                print(f"\n收到客户端 {client_addr} 的关节控制指令，长度：{len(ctrl_buf)}字节")

                # 解析控制指令
                ctrl = self.parse_control_command(ctrl_buf)
                if ctrl:
                    print(f"解析到控制参数：checker={ctrl.checker}, state={ctrl.state}")

                # 生成传感器数据
                sens_buf = self.generate_jnt_sens_data()

                # 返回传感器数据
                self.sk.sendto(sens_buf, client_addr)
                print("已返回关节传感器数据")

            except Exception as e:
                print(f"处理请求时出错：{e}")
                continue

if __name__ == "__main__":
    server = LoongJntServer()
    server.run()
