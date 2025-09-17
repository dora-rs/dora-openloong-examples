import socket
import struct
import time
from threading import Thread
from dora import Node

UDP_IP = '0.0.0.0'
UDP_PORT = 8000

tips=['en','dis','idle','damp','rc','act','mani']
keys=[1,13,112,113,114,115,116]

# 全局 cmd 变量，用于持续发送
cmd = bytearray([0x81,0,0,0,0x60,0,
    0,
    0,0,0,0,
    0,0,0,0,
    0,0,0,0,
    0,0,0,0,  0,0,0,0,  0,0,0,0,  0,0,0,0,  0,0,0,0,  0,0,0,0,  0,0,0,0,  0,0,0,0,
    0x29,0x5c,0xf,0x3f,  0,0,0,0,  0,0,0,0,  0,0,0,0,  0,0,0,0,  0,0,0,0,  0,0,0,0,  0x9a,0x99,0x19,0x3e,
    0,13,0,
    0,0,0,0,0,0,0,0,0,0])

def cmd_loop(sock):
    """持续发送 cmd 的线程函数"""
    while True:
        print(f"📤 发送指令: [{cmd[84]}] {tips[keys.index(cmd[84])] if cmd[84] in keys else ''}")
        sock.sendto(cmd, (UDP_IP, UDP_PORT))
        time.sleep(0.5)

def update_cmd():
    """更新 cmd 中的浮点数字段"""
    # global cmd
    # 清零速度值
    vx, vy, wz = 0, 0, 0
    cmd[7:11] = struct.pack('<f', vy*100)
    cmd[11:15] = struct.pack('<f', -wz*100)
    cmd[15:19] = struct.pack('<f', -vx*100)

def set_cmd(key, desc=""):
    """修改 cmd[84] 的值并打印提示"""
    global cmd
    # update_cmd()  # 先更新浮点数字段
    cmd[84] = key
    print(f"已设置指令: [{key}] {desc}")

def main():
    print("=" * 60)
    print("🎬 CMD_NODE 自动化节点启动中...")
    print("=" * 60)

    node = Node()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # 启动持续发送 cmd 的线程
    th = Thread(target=cmd_loop, args=(sock,))
    th.daemon = True
    th.start()

    try:
        print("✅ CMD_NODE 运行中，开始初始化流程...")
        test_ready = False
        start_time = None
        
        # 1. 使能
        print("📤 发送使能指令 [1]")
        set_cmd(1, "使能 [en]")
        time.sleep(10)  # 等待使能完成
        
        # 2. 复位
        print("📤 发送复位指令 [114]")
        set_cmd(114, "复位 [rc]")
        time.sleep(10)  # 等待复位完成
        
        # 3. 外部操作
        # print("📤 发送外部操作指令 [116]")
        # set_cmd(116, "外部操作 [mani]")
        # time.sleep(2)
        
        # 发送 cmd_ready 信号通知 test_node
        node.send_output("cmd_ready", b"1")
        print("📤 已发送 cmd_ready 信号，等待 test_node 就绪...")
        
        while True:
            try:
                event = next(node)
                if event["type"] == "INPUT" and event["id"] == "test_status":
                    if not test_ready:
                        print("📨 收到 test_node 就绪信号")
                        test_ready = True
                        # 发送开始响应指令
                        print("📤 发送开始响应指令 [152]")
                        set_cmd(152, "上肢运动开始")
                        start_time = time.time()
                        
                if test_ready and start_time:
                    elapsed = time.time() - start_time
                    if elapsed >= 15.0:  # 运行15秒后停止
                        print(f"⏱️ 已运行 {elapsed:.1f} 秒，发送停止指令 [151]")
                        set_cmd(151, "上肢运动停止")
                        start_time = None  # 防止重复发送
                    else:
                        # 每秒打印一次运行时间
                        if int(elapsed) > int(elapsed - 0.1):  # 取整对比避免频繁打印
                            print(f"⏱️ 运行时间: {elapsed:.1f} 秒")
                            
            except StopIteration:
                time.sleep(0.1)
                
    except KeyboardInterrupt:
        print("\n🛑 收到中断信号，正在关闭...")
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        raise e

if __name__ == "__main__":
    main()