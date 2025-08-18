import socket
import struct
import numpy as np
import time

class RobotSimulator:
    def __init__(self, ip="127.0.0.1", port=8080):
        self.ip = ip
        self.port = port
        self.sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sk.bind((self.ip, self.port))
        print(f"模拟机器人服务端启动，监听 {ip}:{port}")

        # 初始化模拟数据（与SDK的maniSdkSensDataClass对应）
        self.jnt_num = 12  # 假设总关节数12
        self.finger_dof_left = 3
        self.finger_dof_right = 3

    def generate_sim_sens_data(self):
        """生成模拟的传感器数据，按SDK格式打包（修复numpy类型问题）"""
        data = {
            # 将numpy标量转换为原生Python类型（用.item()）
            "dataSize": np.int32(1024).item(),  # 关键修复：np类型→原生类型
            "timestamp": np.float64(time.time()).item(),
            "key": np.array([1, 2], np.int16),  # 数组无需转换， unpack时会处理
            "planName": b"sim_plan\x00" * 2,  # 保持16字节
            "state": np.array([0, 1], np.int16),
            "joy": np.array([0.1, -0.2, 0.3, -0.4], np.float32),

            "rpy": np.array([0.05, -0.02, 0.01], np.float32),
            "gyr": np.array([0.01, 0.02, -0.01], np.float32),
            "acc": np.array([9.8, 0.1, -0.2], np.float32),

            # 关节数据（数组保持numpy类型，打包时会自动处理）
            "actJ": np.array([i * 0.1 + 0.01 for i in range(self.jnt_num)], np.float32),
            "actW": np.array([0.02 * i for i in range(self.jnt_num)], np.float32),
            "actT": np.array([0.5 * i for i in range(self.jnt_num)], np.float32),
            "tgtJ": np.array([i * 0.1 for i in range(self.jnt_num)], np.float32),
            "tgtW": np.array([0.02 * i for i in range(self.jnt_num)], np.float32),
            "tgtT": np.array([0.5 * i for i in range(self.jnt_num)], np.float32),

            "drvTemp": np.array([30 + i for i in range(self.jnt_num)], np.int16),
            "drvState": np.array([0] * self.jnt_num, np.int16),
            "drvErr": np.array([0] * self.jnt_num, np.int16),

            "actFingerLeft": np.array([0.3, 0.3, 0.3], np.float32),
            "actFingerRight": np.array([0.2, 0.2, 0.2], np.float32),
            "tgtFingerLeft": np.array([0.3, 0.3, 0.3], np.float32),
            "tgtFingerRight": np.array([0.2, 0.2, 0.2], np.float32),

            "actTipPRpy2B": np.array([[0.4, 0.3, 0.1, 0, 0, 0], [0.2, -0.3, 0.1, 0, 0, 0]], np.float32),
            "actTipVW2B": np.zeros((2, 6), np.float32),
            "actTipFM2B": np.zeros((2, 6), np.float32),
            "tgtTipPRpy2B": np.array([[0.4, 0.3, 0.1, 0, 0, 0], [0.2, -0.3, 0.1, 0, 0, 0]], np.float32),
            "tgtTipVW2B": np.zeros((2, 6), np.float32),
            "tgtTipFM2B": np.zeros((2, 6), np.float32),
        }

        # 打包逻辑保持不变，但确保标量已转换为原生类型
        fmt_list = [
            'i', 'd', '2h', '16s', '2h', '4f',
            '3f', '3f', '3f',
            f'{self.jnt_num}f', f'{self.jnt_num}f', f'{self.jnt_num}f',
            f'{self.jnt_num}h', f'{self.jnt_num}h', f'{self.jnt_num}h',
            f'{self.jnt_num}f', f'{self.jnt_num}f', f'{self.jnt_num}f',
            f'{self.finger_dof_left}f', f'{self.finger_dof_right}f',
            f'{self.finger_dof_left}f', f'{self.finger_dof_right}f',
            '12f', '12f', '12f', '12f', '12f', '12f'
        ]

        buf = b""
        for fmt in fmt_list:
            key = {
                'i': 'dataSize', 'd': 'timestamp', '2h': 'key', '16s': 'planName',
                '2h': 'state', '4f': 'joy', '3f': 'rpy', '3f': 'gyr', '3f': 'acc',
                f'{self.jnt_num}f': 'actJ', f'{self.jnt_num}f': 'actW', f'{self.jnt_num}f': 'actT',
                f'{self.jnt_num}h': 'drvTemp', f'{self.jnt_num}h': 'drvState', f'{self.jnt_num}h': 'drvErr',
                f'{self.jnt_num}f': 'tgtJ', f'{self.jnt_num}f': 'tgtW', f'{self.jnt_num}f': 'tgtT',
                f'{self.finger_dof_left}f': 'actFingerLeft', f'{self.finger_dof_right}f': 'actFingerRight',
                f'{self.finger_dof_left}f': 'tgtFingerLeft', f'{self.finger_dof_right}f': 'tgtFingerRight',
                '12f': 'actTipPRpy2B', '12f': 'actTipVW2B', '12f': 'actTipFM2B',
                '12f': 'tgtTipPRpy2B', '12f': 'tgtTipVW2B', '12f': 'tgtTipFM2B'
            }[fmt]

            value = data[key]
            if isinstance(value, np.ndarray) and value.ndim > 1:
                value = value.flatten()
            # 新增：如果不是 iterable，则包装成 list
            if not isinstance(value, (list, tuple, np.ndarray)):
                value = [value]
            # 打包时确保所有元素都是原生类型（numpy数组会自动转换）
            buf += struct.pack(fmt, *value)

        return buf

    def run(self):
        """启动服务端，循环接收并响应"""
        while True:
            # 接收客户端指令（最多2048字节）
            ctrl_buf, client_addr = self.sk.recvfrom(2048)
            print(f"\n收到客户端 {client_addr} 的指令，长度：{len(ctrl_buf)}字节")

            # 解析指令（可选，用于调试）
            if len(ctrl_buf) >= 12:  # 前6个short（12字节）是基础控制参数
                base_ctrl = struct.unpack('6h', ctrl_buf[:12])
                print(f"解析到基础控制参数：inCharge={base_ctrl[0]}, armMode={base_ctrl[2]}")

            # 生成模拟传感器数据并返回
            sens_buf = self.generate_sim_sens_data()
            self.sk.sendto(sens_buf, client_addr)
            print("已返回模拟传感器数据")

if __name__ == "__main__":
    simulator = RobotSimulator()
    simulator.run()