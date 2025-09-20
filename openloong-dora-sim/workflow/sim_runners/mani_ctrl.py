#!/usr/bin/env python3
# coding=utf-8
import time
import sys
import os
from dora import Node
import numpy as np

# 添加 SDK 路径
sys.path.append(os.path.join(os.path.dirname(__file__), "../..", "loong_sim_sdk_release"))
from sdk.loong_mani_sdk.loong_mani_sdk_udp import maniSdkCtrlDataClass, maniSdkClass, maniSdkSensDataClass

# 配置参数
dT = 0.02  # 50Hz 控制频率
MAX_STEPS = 2000

def main():
    print("🤖 MANI_CTRL 节点启动...")
    
    node = Node()
    
    # 等待启动信号
    while True:
        try:
            event = next(node)
            if event["type"] == "INPUT" and event["id"] == "cmd_ready":
                print("收到启动信号，开始控制...")
                break
        except StopIteration:
            time.sleep(0.01)
    
    # 初始化控制参数
    jntNum = 19
    armDof = 7
    fingerDofLeft = 6
    fingerDofRight = 6
    neckDof = 2
    lumbarDof = 3

    ctrl = maniSdkCtrlDataClass(armDof, fingerDofLeft, fingerDofRight, neckDof, lumbarDof)
    sdk = maniSdkClass("127.0.0.1", 8003, jntNum, fingerDofLeft, fingerDofRight)

    ctrl.inCharge = 1
    ctrl.filtLevel = 1
    ctrl.armMode = 4
    ctrl.fingerMode = 3
    ctrl.neckMode = 5
    ctrl.lumbarMode = 0
    ctrl.armCmd = np.array([
        [0.4, 0.4, 0.1, 0, 0, 0, 0.5],
        [0.2, -0.4, 0.1, 0, 0, 0, 0.5]
    ], np.float32)
    ctrl.armFM = np.zeros((2, 6), np.float32)
    ctrl.fingerLeft = np.zeros(fingerDofLeft, np.float32)
    ctrl.fingerRight = np.zeros(fingerDofRight, np.float32)
    ctrl.neckCmd = np.zeros(2, np.float32)
    ctrl.lumbarCmd = np.zeros(3, np.float32)

    node.send_output("ctrl_status", b"ready")
    
    tim = time.time()
    for i in range(MAX_STEPS):
        # 更新控制指令
        ctrl.armCmd[0][0] = 0.4 + 0.1 * np.sin(i * dT * 2)
        ctrl.armCmd[0][2] = 0.1 + 0.1 * np.sin(i * dT * 2)
        ctrl.armCmd[1][0] = 0.2 + 0.1 * np.sin(i * dT * 2)
        ctrl.fingerLeft[0] = 40 + 30 * np.sin(i * dT)
        ctrl.fingerRight[3] = 40 + 30 * np.sin(i * dT)
        
        # 发送控制指令
        sdk.send(ctrl)
        
        # 接收反馈
        sens = sdk.recv()
        if sens is not None and i % 10 == 0:
            sens.print()
        
        # 时间控制
        tim += dT
        dt = tim - time.time()
        if dt > 0:
            time.sleep(dt)

    print(f"控制完成，共执行 {MAX_STEPS} 步")

if __name__ == "__main__":
    main()
