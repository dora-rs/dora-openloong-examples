# en_node.py
import socket
import struct
import time
import threading
from dora import Node

# -----------------------------
# 配置参数
# -----------------------------
UDP_IP = "127.0.0.1"        # 根据 interface.log 推断，它在本地运行
UDP_PORT = 8000             # OCU (遥控器) 接口端口

# -----------------------------
# 全局变量
# -----------------------------
# 初始化一个长度为 85 的字节数组，初始值为 0
cmd = bytearray(85)

# 用于控制 cmd_loop 线程的标志
running = True

# 控制指令描述映射（可选，用于调试）
tips = [
    "idle", "en", "dis", "damp", "rc", "rl", "jntSdk", "start", "stop",
    "mani", "act"
]
keys = [100, 1, 13, 12, 114, 116, 106, 107, 108, 152, 151]

# -----------------------------
# UDP 发送线程函数
# -----------------------------
def cmd_loop():
    """持续发送 cmd 数组到 UDP 目标"""
    global running, cmd
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    print(f"🟢 UDP 发送线程启动，目标: {UDP_IP}:{UDP_PORT}")
    
    while running:
        try:
            sock.sendto(cmd, (UDP_IP, UDP_PORT))
            # 🔍 调试：打印当前发送的 key 值
            # print(f"📤 发送指令: key={cmd[84]}")
            time.sleep(0.5)  # 每 500ms 发送一次（与遥控器频率一致）
        except Exception as e:
            print(f"❌ UDP 发送失败: {e}")
            time.sleep(1)
    
    sock.close()
    print("🛑 UDP 发送线程已停止")

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
    print(f"✅ 已设置指令: [{key}] {desc}")

# -----------------------------
# 主函数
# -----------------------------
def main():
    global running, cmd

    # 创建 dora 节点
    node = Node()

    print("🚀 启动 OpenLoong 控制节点...")

    # ✅ 初始化标志变量
    test_ready = False
    start_time = None

    # 启动 UDP 发送线程
    thread = threading.Thread(target=cmd_loop, daemon=True)
    thread.start()

    try:
        # --- 正确的使能流程 ---
        print("\n🔧 准备使能...")
        set_cmd(13, "下使能 [dis]")
        time.sleep(2)

        print("\n🔑 发送上使能指令...")
        set_cmd(1, "上使能 [en]")
        time.sleep(2)

        print("\n🔄 发送复位指令...")
        set_cmd(114, "复位 [rc]")
        time.sleep(5)

        print("\n🎉 机器人已成功使能并复位！")
        print("💡 现在可以开始发送其他控制指令。")

        print("📤 发送外部操作指令 [116]")
        set_cmd(116, "外部操作 [mani]")
        time.sleep(2)

        # 发送 cmd_ready 信号通知 test_node
        node.send_output("cmd_ready", b"1")
        print("📤 已发送 cmd_ready 信号，等待 test_node 就绪...")

        while True:
            try:
                event = next(node)
                if event["type"] == "INPUT" and event["id"] == "ctrl_status":
                    if not test_ready:
                        print("📨 收到 test_node 就绪信号")
                        test_ready = True
                        print("📤 发送开始响应指令 [152]")
                        set_cmd(152, "上肢运动开始")
                        start_time = time.time()

                if test_ready and start_time is not None:
                    elapsed = time.time() - start_time
                    if elapsed >= 60.0:
                        print(f"⏱️ 已运行 {elapsed:.1f} 秒，发送停止指令 [151]")
                        set_cmd(151, "上肢运动停止")
                        start_time = None
                    elif int(elapsed) > int(elapsed - 1):
                        print(f"⏱️ 运行时间: {elapsed:.1f} 秒")

            except StopIteration:
                time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n👋 收到中断信号，正在关闭...")
    except Exception as e:
        print(f"❌ 主循环发生异常: {e}")
    finally:
        running = False
        thread.join(timeout=2)
        print("🧹 资源已清理，节点退出。")

if __name__ == "__main__":
    main()