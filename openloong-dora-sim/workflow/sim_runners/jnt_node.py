#!/usr/bin/env python3
# coding=utf-8
import socket
import struct
import time
import threading
from dora import Node

# -----------------------------
# 配置参数
# -----------------------------
UDP_IP = "127.0.0.1"        # 根据 interface.log 推断，它在本地运行
UDP_PORT = 8000             # OCU (遥控器) 接口端口 - jnt 使用 8004

# -----------------------------
# 全局变量
# -----------------------------
# 初始化一个长度为 85 的字节数组，初始值为 0
cmd = bytearray(85)

# 用于控制 cmd_loop 线程的标志
running = True

# 控制指令描述映射（可选，用于调试）
tips = [
    "idle", "en", "dis", "damp", "rc", "rl", "jntSdk"
]
keys = [3, 1, 13, 12, 2, 4, 23]

# -----------------------------
# UDP 发送线程函数
# -----------------------------
def cmd_loop():
    """持续发送 cmd 数组到 UDP 目标"""
    global running, cmd
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    print(f"UDP 发送线程启动，目标: {UDP_IP}:{UDP_PORT}")
    
    while running:
        try:
            sock.sendto(cmd, (UDP_IP, UDP_PORT))
            # 调试：打印当前发送的 key 值
            # print(f"发送指令: key={cmd[84]}")
            time.sleep(0.5)  # 每 500ms 发送一次（与遥控器频率一致）
        except Exception as e:
            print(f"UDP 发送失败: {e}")
            time.sleep(1)
    
    sock.close()
    print("UDP 发送线程已停止")

# -----------------------------
# 设置指令函数
# -----------------------------
def set_cmd(key, desc=""):
    """设置控制指令"""
    global cmd
    # 清零速度（vy, -wz, -vx）
    for i, val in enumerate([0.0, 0.0, 0.0]):
        packed = struct.pack('<f', -val * 100)
        if i == 0:
            cmd[7:11] = packed   # vy
        elif i == 1:
            cmd[11:15] = packed  # -wz
        elif i == 2:
            cmd[15:19] = packed  # -vx

    cmd[84] = key  # 设置指令码
    print(f"已设置指令: [{key}] {desc}")

# -----------------------------
# 主函数
# -----------------------------
def main():
    global running, cmd

    # 创建 dora 节点
    node = Node()

    print("启动 OpenLoong JNT 控制节点...")

    # 初始化标志变量
    test_ready = False
    start_time = None
    jnt_running = False

    # 启动 UDP 发送线程
    thread = threading.Thread(target=cmd_loop, daemon=True)
    thread.start()

    try:
        # --- 按照 readme 中的 jnt sdk 控制流程 ---
        print("\n准备使能...")
        set_cmd(13, "下使能 [dis]")
        time.sleep(2)

        print("\n发送上使能指令...")
        set_cmd(1, "上使能 [en]")
        time.sleep(2)

        print("\n发送复位指令...")
        set_cmd(2, "复位 [rc]")
        time.sleep(5)

        print("\n机器人已成功使能并复位！")
        print("现在可以开始发送其他控制指令。")

        print("发送站立指令 [rl]")
        set_cmd(4, "站立 [rl]")
        time.sleep(3)

        print("发送 jntSdk 控制指令 [23]")
        set_cmd(23, "jntSdk 控制")
        time.sleep(2)

        # 发送 cmd_ready 信号通知 jnt_ctrl
        node.send_output("jnt_cmd_ready", b"1")
        print("已发送 jnt_cmd_ready 信号，等待 jnt_ctrl 就绪...")

        while True:
            try:
                event = next(node)
                if event["type"] == "INPUT" and event["id"] == "jnt_ctrl_status":
                    if not test_ready:
                        print("收到 jnt_ctrl 就绪信号")
                        test_ready = True
                        print("发送开始踏步指令 [107]")
                        set_cmd(107, "开始踏步")
                        start_time = time.time()
                        jnt_running = True

                if test_ready and start_time is not None:
                    elapsed = time.time() - start_time
                    if elapsed >= 10.0 and jnt_running:  # 运行10秒后停止 jnt
                        print(f"已运行 {elapsed:.1f} 秒，停止 jnt 控制")
                        set_cmd(108, "停止踏步")
                        jnt_running = False
                        
                        # 发送信号启动 mani 流程
                        print("发送 mani 启动信号")
                        node.send_output("mani_cmd_ready", b"1")
                        
                    elif jnt_running and int(elapsed) > int(elapsed - 1):
                        print(f"JNT 运行时间: {elapsed:.1f} 秒")

            except StopIteration:
                time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n收到中断信号，正在关闭...")
    except Exception as e:
        print(f"主循环发生异常: {e}")
    finally:
        running = False
        thread.join(timeout=2)
        print("资源已清理，节点退出。")

if __name__ == "__main__":
    main()