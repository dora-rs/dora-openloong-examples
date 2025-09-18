#!/usr/bin/env python3
# coding=utf-8
import time
import sys
import os
from dora import Node
import numpy as np

# ================== 配置区 ==================
MAX_STEPS = 2000        # 最大控制步数，设为 None 表示无限运行
CONTROL_FREQ = 50       # 控制频率 (Hz)
dT = 1.0 / CONTROL_FREQ # 控制周期 (s)
PRINT_EVERY_N_STEPS = 10  # 每 N 步打印一次状态
RECV_TIMEOUT_SEC = 0.1     # recv 超时时间（需 SDK 支持）
# ===========================================

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
                        node.send_output("ctrl_status", b"ready")
                        print("🟢 控制已初始化，即将开始循环...")
            except StopIteration:
                pass  # 无新事件
            except Exception as e:
                print(f"❌ 处理 Dora 事件时出错: {e}")

            # --- 2. 执行控制循环 ---
            if started and ctrl and sdk:
                if MAX_STEPS is not None and i >= MAX_STEPS:
                    print(f"✅ 已完成 {MAX_STEPS} 步控制，任务结束。")
                    break

                try:
                    # --- 更新控制指令 ---
                    print("updating control commands...")
                    t = i * dT
                    ctrl.armCmd[0][0] = 0.4 + 0.1 * np.sin(t * 2)
                    ctrl.armCmd[0][2] = 0.1 + 0.1 * np.sin(t * 2)
                    ctrl.armCmd[1][0] = 0.2 + 0.1 * np.sin(t * 2)
                    ctrl.fingerLeft[0] = 40 + 30 * np.sin(t)
                    ctrl.fingerRight[3] = 40 + 30 * np.sin(t)

                    # --- 发送控制指令 ---
                    sdk.send(ctrl)

                    # --- 接收反馈（带超时/异常处理）---
                    sens = None
                    try:
                        start_recv = time.time()
                        print("time: {}".format(start_recv))
                        sens = sdk.recv()
                        if sens is not None:
                            if i % PRINT_EVERY_N_STEPS == 0:
                                print("recv from sdk:")
                                sens.print()  # 定期打印状态
                        else:
                            print(f"⚠️  step {i}: recv() 返回 None")
                    except Exception as e:
                        elapsed = time.time() - start_recv
                        print(f"⚠️  step {i}: recv() 超时或出错 (took {elapsed:.3f}s): {e}")

                    # --- 稳定控制周期 ---
                    end_t = time.time()
                    elapsed = end_t - start_recv if 'start_recv' in locals() else end_t - time.time() + dT
                    print("elapsed time: {:.3f}s".format(elapsed))
                    sleep_time = dT - elapsed
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                    elif elapsed > dT * 2:
                        print(f"🚨 step {i}: 单步耗时过长: {elapsed:.3f}s (> {dT*2:.3f}s)")

                    i += 1
                    if i % PRINT_EVERY_N_STEPS == 0:
                        print(f"📊 已执行 {i} 步控制指令...")

                except Exception as e:
                    print(f"❌ 控制循环第 {i} 步出错: {e}")
                    time.sleep(0.1)  # 避免高速报错
                    continue

            # 小延时避免 CPU 占满（当未启动时）
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