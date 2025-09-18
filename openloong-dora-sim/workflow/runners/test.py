#!/usr/bin/env python3
# coding=utf-8
import time
import sys
import os
import select
import signal
import numpy as np

# 确保路径正确
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.append("..")

# 导入官方 SDK
sys.path.append(os.path.join(os.path.dirname(__file__), "../..", "loong_sim_sdk_release"))
from sdk.loong_mani_sdk.loong_mani_sdk_udp import maniSdkCtrlDataClass, maniSdkClass, maniSdkSensDataClass


# ==================== 配置参数 ====================
JNT_NUM = 19
ARM_DOF = 7
FINGER_DOF_LEFT = 6
FINGER_DOF_RIGHT = 6
NECK_DOF = 2
LUMBAR_DOF = 3

# 仿真器 IP 和控制端口
ROBOT_IP = "127.0.0.1"
CONTROL_PORT = 8003  # 机器人接收指令的端口

# 控制频率
CONTROL_FREQ = 50.0  # Hz
DT = 1.0 / CONTROL_FREQ  # 0.02s

# 最大步数（设为 None 表示无限运行）
MAX_STEPS = None  # 可改为 2000 测试有限步数
# =================================================

# 全局变量
running = True


def signal_handler(signum, frame):
    """优雅退出"""
    global running
    print(f"\n🛑 收到信号 {signum}，准备退出...", flush=True)
    running = False


def main():
    global running

    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("🤖 TEST_NODE 节点启动中...", flush=True)
    print("=" * 60, flush=True)

    # 初始化控制数据
    ctrl = maniSdkCtrlDataClass(ARM_DOF, FINGER_DOF_LEFT, FINGER_DOF_RIGHT, NECK_DOF, LUMBAR_DOF)

    # 初始化 SDK（关键：发送到 8001，绑定本地 8003）
    try:
        sdk = maniSdkClass(ROBOT_IP, CONTROL_PORT, JNT_NUM, FINGER_DOF_LEFT, FINGER_DOF_RIGHT)
        print(f"🟢 UDP 连接已建立: 发送到 {ROBOT_IP}:{CONTROL_PORT}", flush=True)
    except Exception as e:
        print(f"❌ SDK 初始化失败: {e}", flush=True)
        return

    # 设置初始模式和指令
    ctrl.inCharge = 1
    ctrl.filtLevel = 1
    ctrl.armMode = 4
    ctrl.fingerMode = 3
    ctrl.neckMode = 5
    ctrl.lumbarMode = 0

    # 初始目标位置（安全位置）
    ctrl.armCmd = np.array([
        [0.4, 0.4, 0.1, 0.0, 0.0, 0.0, 0.5],
        [0.2, -0.4, 0.1, 0.0, 0.0, 0.0, 0.5]
    ], dtype=np.float32)
    ctrl.armFM = np.zeros((2, 6), dtype=np.float32)
    ctrl.fingerLeft = np.zeros(FINGER_DOF_LEFT, dtype=np.float32)
    ctrl.fingerRight = np.zeros(FINGER_DOF_RIGHT, dtype=np.float32)
    ctrl.neckCmd = np.zeros(NECK_DOF, dtype=np.float32)
    ctrl.lumbarCmd = np.zeros(LUMBAR_DOF, dtype=np.float32)

    print("✅ 控制已初始化，即将开始循环...", flush=True)
    time.sleep(1.0)

    # 主控制循环
    step = 0
    start_time = time.time()
    next_print_time = start_time + 1.0  # 每秒打印一次状态

    while running:
        current_time = time.time()

        # ========== 更新控制指令 ==========
        # 🔥 每帧都必须设置 inCharge=1
        ctrl.inCharge = 1
        ctrl.filtLevel = 1
        ctrl.armMode = 4
        ctrl.fingerMode = 3

        # 双臂正弦波运动
        ctrl.armCmd[0][0] = 0.4 + 0.1 * np.sin(step * DT * 2)  # 左臂肩摆
        ctrl.armCmd[0][2] = 0.1 + 0.1 * np.sin(step * DT * 2)  # 左臂肩抬
        ctrl.armCmd[1][0] = 0.2 + 0.1 * np.sin(step * DT * 2)  # 右臂肩摆

        # 手指开合
        ctrl.fingerLeft[0] = 40.0 + 30.0 * np.sin(step * DT)   # 左手拇指
        ctrl.fingerRight[3] = 40.0 + 30.0 * np.sin(step * DT)  # 右手无名指

        # ========== 发送指令 ==========
        try:
            sdk.send(ctrl)
        except Exception as e:
            print(f"❌ 发送失败: {e}", flush=True)

        # ========== 非阻塞接收反馈 ==========
        try:
            ready = select.select([sdk.sk], [], [], 0.01)  # 10ms 超时
            if ready[0]:
                data, _ = sdk.sk.recvfrom(4096)
                sens = sdk.unpackData(data)
                if step % 50 == 0:  # 每 50 步打印一次
                    print(f"Step {step}: dataSize={sens.dataSize[0]}, key={sens.key}, plan={sens.planName.decode().strip()}", flush=True)
            else:
                # 可选：打印超时（调试用）
                # print(f"Step {step}: ⚠️  recv timeout", flush=True)
                pass
        except Exception as e:
            print(f"❌ 接收异常: {e}", flush=True)

        # ========== 打印运行状态（每秒一次） ==========
        if current_time >= next_print_time:
            print(f"📊 已执行 {step} 步，运行时间: {current_time - start_time:.1f}s", flush=True)
            next_print_time = current_time + 1.0

        # ========== 下一步 ==========
        step += 1
        if MAX_STEPS is not None and step >= MAX_STEPS:
            print(f"✅ 已完成 {MAX_STEPS} 步控制任务", flush=True)
            break

        # 保持 50Hz 频率
        sleep_time = (start_time + step * DT) - time.time()
        if sleep_time > 0:
            time.sleep(sleep_time)
        else:
            # 控制频率跟不上（警告）
            if step % 100 == 0:
                print(f"⚠️  控制延迟: {-sleep_time*1000:.1f}ms", flush=True)

    # ========== 退出前发送停止指令 ==========
    print("🛑 正在停止控制...", flush=True)
    try:
        # 发送停止指令（可选：发给 en_node 的 8000 端口）
        # 这里只是停止发送，机器人会超时退出
        pass
    except:
        pass

    print("👋 TEST_NODE 已退出", flush=True)


if __name__ == "__main__":
    main()