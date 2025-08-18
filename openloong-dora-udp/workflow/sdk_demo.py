import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sdk.loong_mani_sdk.loong_mani_sdk_udp import maniSdkClass, maniSdkCtrlDataClass
import numpy as np
import time

def main():
    # 配置参数（与模拟服务端一致）
    ROBOT_IP = "127.0.0.1"  # 本地IP
    ROBOT_PORT = 8080       # 与服务端监听端口一致
    jnt_num = 12            # 总关节数（需与服务端匹配）
    finger_dof_left = 3
    finger_dof_right = 3
    arm_dof = 7             # 单臂自由度
    neck_dof = 2
    lumbar_dof = 1

    # 初始化SDK
    sdk = maniSdkClass(
        ip=ROBOT_IP,
        port=ROBOT_PORT,
        jntNum=jnt_num,
        fingerDofLeft=finger_dof_left,
        fingerDofRight=finger_dof_right
    )

    # 创建控制指令
    ctrl = maniSdkCtrlDataClass(
        armDof=arm_dof,
        fingerDofLeft=finger_dof_left,
        fingerDofRight=finger_dof_right,
        neckDof=neck_dof,
        lumbarDof=lumbar_dof
    )

    # 配置控制指令（示例：关节轴控模式）
    ctrl.armMode = 3                # 手臂关节轴控
    ctrl.fingerMode = 3             # 手指关节轴控
    ctrl.neckMode = 5               # 颈部看左手
    ctrl.armCmd = np.array([
        [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7],  # 左臂目标角度
        [-0.1, -0.2, -0.3, -0.4, -0.5, -0.6, -0.7]  # 右臂目标角度
    ], dtype=np.float32)
    ctrl.fingerLeft = np.array([0.5, 0.5, 0.5], dtype=np.float32)  # 左手弯曲

    # 循环发送指令并接收数据
    try:
        while True:
            # 发送指令
            sdk.send(ctrl)
            print("\n=== 发送控制指令 ===")
            print(f"手臂模式：{ctrl.armMode}，左臂目标角度：{ctrl.armCmd[0][:3]}...")

            # 接收并解析数据
            sens = sdk.recv()
            print("\n=== 接收模拟传感器数据 ===")
            print(f"时间戳：{sens.timestamp[0]:.2f}")
            print(f"左臂实际角度：{sens.actJ[:3]}...")  # 打印前3个关节
            print(f"左手实际角度：{sens.actFingerLeft}")
            print(f"驱动器温度：{sens.drvTemp[:3]}...")

            time.sleep(1)  # 1秒发送一次

    except KeyboardInterrupt:
        print("\n程序退出")

if __name__ == "__main__":
    main()