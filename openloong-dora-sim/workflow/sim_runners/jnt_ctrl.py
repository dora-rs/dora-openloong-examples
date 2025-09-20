#!/usr/bin/env python3
# coding=utf-8
import time
import sys
import os
from dora import Node
import numpy as np

# 添加 SDK 路径
sys.path.append(os.path.join(os.path.dirname(__file__), "../..", "loong_sim_sdk_release"))
from sdk.loong_jnt_sdk.loong_jnt_sdk_datas import jntSdkSensDataClass, jntSdkCtrlDataClass
from sdk.loong_jnt_sdk.loong_jnt_sdk_udp import jntSdkClass

# 配置参数
dT = 0.02  # 50Hz 控制频率
MAX_STEPS = 500  # 10秒 * 50Hz = 500步

def main():
    print("🤖 JNT_CTRL 节点启动...")
    
    node = Node()
    
    # 等待启动信号
    while True:
        try:
            event = next(node)
            if event["type"] == "INPUT" and event["id"] == "jnt_cmd_ready":
                print("收到 jnt 启动信号，开始控制...")
                break
        except StopIteration:
            time.sleep(0.01)
    
    # 初始化控制参数 - 完全按照 test_jnt.py
    jntNum = 31
    fingerDofLeft = 6
    fingerDofRight = 6

    ctrl = jntSdkCtrlDataClass(jntNum, fingerDofLeft, fingerDofRight)
    sdk = jntSdkClass('127.0.0.1', 8006, jntNum, fingerDofLeft, fingerDofRight)
    
    # 等待传感器数据
    sdk.waitSens()

    # 初始化控制参数 - 完全按照 test_jnt.py
    ctrl.reset()
    ctrl.filtRate = 1
    ctrl.kp = np.array([
        10, 10, 10, 10, 10, 10, 10,
        10, 10, 10, 10, 10, 10, 10,
        10, 10, 10, 10, 10,
        500, 400, 500, 500, 200, 200,
        500, 400, 500, 500, 200, 200,
    ], np.float32)
    ctrl.kd = np.array([
        0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1,
        0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1,
        0.1, 0.1, 0.1, 0.1, 0.1,
        1, 1, 2, 2, 1, 1,
        1, 1, 2, 2, 1, 1,
    ], np.float32)

    # 获取标准关节位置
    stdJnt = ctrl.getStdJnt()

    node.send_output("jnt_ctrl_status", b"ready")
    
    # 控制循环 - 完全采用 mani_ctrl 和 test_jnt 的成功方式
    tim = time.time()
    for i in range(MAX_STEPS):
        # 设置控制状态 - 按照 test_jnt.py
        ctrl.state = 5
        
        # 更新控制指令 - 完全按照 test_jnt.py 的运动模式
        ctrl.j[0] = stdJnt[0] + 0.5 * np.sin(i / 50)      # 左腿
        ctrl.j[10] = stdJnt[10] + 0.5 * np.sin(i / 100)   # 右腿
        ctrl.j[21] = stdJnt[21] + 0.2 * np.sin(i / 20)    # 左手
        ctrl.j[28] = stdJnt[28] + 0.5 * np.sin(i / 50)    # 右手
        
        # 发送控制指令
        sdk.send(ctrl)
        
        # 接收反馈 - 按照 test_jnt.py 的方式
        sens = sdk.recv()
        if sens is not None and i % 10 == 0:
            delayT = time.time() - sens.timestamp
            print(f"📊 JNT 步骤 {i}: 延迟 {float(delayT):.3f}s")
        
        # 时间控制 - 完全采用 mani_ctrl 和 test_jnt 的精确方式
        tim += dT
        dt = tim - time.time()
        if dt > 0:
            time.sleep(dt)

    print(f"JNT 控制完成，共执行 {MAX_STEPS} 步")

if __name__ == "__main__":
    main()