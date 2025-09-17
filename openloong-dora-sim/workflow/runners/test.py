#!/usr/bin/env python3
# coding=utf-8
'''=========== ***doc description @ yyp*** ===========
Copyright 2025 人形机器人（上海）有限公司, https://www.openloong.net/
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
Author: YYP
调用 mani sdk udp，接口定义见之
======================================================'''
import time
import sys
import os
from dora import Node
import numpy as np

# ================== ⚙️ 配置区 ==================
ROBOT_IP = "127.0.0.1"        # 🟠 必须改为你的机器人真实IP
ROBOT_CMD_PORT = 8001             # 🟠 机器人接收指令的端口（通常是8001）
LOCAL_LISTEN_PORT = 8003          # 本地接收反馈的端口
CONTROL_FREQ = 50                 # 控制频率：50Hz
dT = 1.0 / CONTROL_FREQ           # 控制周期：0.02s
MAX_STEPS = None                  # None 表示无限运行，或设为 2000
PRINT_STATUS_EVERY = 100          # 每100步打印一次状态
# =================================================

# 添加 SDK 路径
sys.path.append(os.path.join(os.path.dirname(__file__), "../..", "loong_sim_sdk_release"))
from sdk.loong_mani_sdk.loong_mani_sdk_udp import maniSdkCtrlDataClass, maniSdkClass, maniSdkSensDataClass


def init_ctrl():
    """初始化控制参数"""
    jntNum = 19
    armDof = 7
    fingerDofLeft = 6
    fingerDofRight = 6
    neckDof = 2
    lumbarDof = 3

    # 初始化控制数据
    ctrl = maniSdkCtrlDataClass(armDof, fingerDofLeft, fingerDofRight, neckDof, lumbarDof)
    
    # 初始化 SDK：监听本地 8003 端口接收反馈
    sdk = maniSdkClass("0.0.0.0", LOCAL_LISTEN_PORT, jntNum, fingerDofLeft, fingerDofRight)

    # --- 🌟 关键：设置目标机器人IP和端口 ---
    # 检查 SDK 是否支持 set_target 方法
    if hasattr(sdk, 'set_target_ip') and hasattr(sdk, 'set_target_port'):
        sdk.set_target_ip(ROBOT_IP)
        sdk.set_target_port(ROBOT_CMD_PORT)
        print(f"🟢 SDK 已设置目标: {ROBOT_IP}:{ROBOT_CMD_PORT}")
    else:
        print("⚠️  SDK 不支持 set_target_ip/port，请确认初始化方式是否包含目标地址")

    # --- 设置控制模式 ---
    ctrl.inCharge = 1           # 🌟 必须为1，表示当前节点拥有控制权
    ctrl.filtLevel = 1
    ctrl.armMode = 1            # 🌟 改为1：关节位置控制（原4可能不正确）
    ctrl.fingerMode = 1         # 手指位置控制
    ctrl.neckMode = 5           # 原值保留
    ctrl.lumbarMode = 0

    # 初始目标位置
    ctrl.armCmd = np.array([
        [0.4, 0.4, 0.1, 0, 0, 0, 0.5],  # 右臂
        [0.2, -0.4, 0.1, 0, 0, 0, 0.5]  # 左臂
    ], np.float32)
    ctrl.armFM = np.zeros((2, 6), np.float32)
    ctrl.fingerLeft = np.zeros(fingerDofLeft, np.float32)
    ctrl.fingerRight = np.zeros(fingerDofRight, np.float32)
    ctrl.neckCmd = np.zeros(2, np.float32)
    ctrl.lumbarCmd = np.zeros(3, np.float32)

    return ctrl, sdk


def main():
    print("=" * 60)
    print("🤖 TEST_NODE 节点启动中...")
    print("=" * 60)

    node = Node()
    print("✅ TEST_NODE 已启动，等待 cmd_ready 信号...")

    ctrl = None
    sdk = None
    started = False
    i = 0

    try:
        while True:
            # --- 1. 处理 Dora 事件 ---
            try:
                event = next(node)
                if event["type"] == "INPUT" and event["id"] == "cmd_ready":
                    if not started:
                        print("[test-node] 收到 cmd_ready 信号，开始执行控制...")
                        ctrl, sdk = init_ctrl()
                        started = True
                        node.send_output("test_status", b"ready")
                        print("🟢 控制已初始化，即将开始循环...")
            except StopIteration:
                pass
            except Exception as e:
                print(f"❌ 处理 Dora 事件时出错: {e}")

            # --- 2. 执行控制循环 ---
            if started and ctrl and sdk:
                if MAX_STEPS is not None and i >= MAX_STEPS:
                    print(f"✅ 已完成 {MAX_STEPS} 步控制，任务结束。")
                    break

                try:
                    # --- 更新控制指令 ---
                    t = i * dT
                    ctrl.armCmd[0][0] = 0.4 + 0.1 * np.sin(t * 2)  # 右肩
                    ctrl.armCmd[0][2] = 0.1 + 0.1 * np.sin(t * 2)  # 右肘
                    ctrl.armCmd[1][0] = 0.2 + 0.1 * np.sin(t * 2)  # 左肩
                    ctrl.fingerLeft[0] = 40 + 30 * np.sin(t)       # 左手
                    ctrl.fingerRight[3] = 40 + 30 * np.sin(t)      # 右手

                    # --- 发送控制指令 ---
                    sdk.send(ctrl)
                    if i % 50 == 0:  # 每50步打印一次发送日志
                        print(f"📤 第 {i} 步: 发送指令 → 右肩={ctrl.armCmd[0][0]:.3f}, 左肩={ctrl.armCmd[1][0]:.3f}")

                    # --- 接收反馈 ---
                    try:
                        sens = sdk.recv()
                        if not hasattr(sens, 'dataSize'):
                            print(f"⚠️  step {i}: recv() 返回对象缺少 dataSize 字段")
                        elif sens.dataSize[0] == 0:
                            print(f"🚨 step {i}: dataSize=0，未收到有效反馈！检查 IP={ROBOT_IP} 是否正确？")
                        else:
                            if i % PRINT_STATUS_EVERY == 0:
                                print(f"📊 step {i}: 收到有效反馈，时间戳={sens.timestamp[0]:.3f}")
                                # sens.print()  # 可选：打印详细状态
                    except Exception as e:
                        print(f"⚠️  step {i}: recv() 异常: {e}")

                    # --- 固定周期控制 ---
                    start_t = time.time()
                    elapsed = time.time() - start_t
                    if elapsed < dT:
                        time.sleep(dT - elapsed)
                    else:
                        print(f"⏱️  step {i}: 单步耗时过长: {elapsed:.3f}s")

                    i += 1

                except Exception as e:
                    print(f"❌ 控制循环第 {i} 步出错: {e}")
                    time.sleep(0.1)
                    continue

            # 未启动时，避免 CPU 占用过高
            if not started:
                time.sleep(0.01)

    except KeyboardInterrupt:
        print("\n🛑 收到中断信号，正在关闭...")
    except Exception as e:
        print(f"❌ 主循环外发生未知错误: {e}")
    finally:
        print(f"🔚 程序结束，共执行 {i} 步。")


if __name__ == "__main__":
    main()