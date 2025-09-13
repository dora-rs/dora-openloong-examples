import json
import time
from dora import Node


def main():
    print("=" * 60)
    print("🎬 DEMO_UI 节点启动中...")
    print("=" * 60)
    
    node = Node()
    print("✅ [demo_ui] 演示控制节点已启动")
    print("📋 [demo_ui] 将编排机械臂演示序列: GRAB -> RETURN")
    print("=" * 60)
    print("🎯 DEMO_UI 节点运行中，等待触发信号...")
    print("=" * 60)

    phase = 0
    sent = False
    for event in node:
        # Wait for start trigger
        if event["type"] == "INPUT":
            print("🚀 [demo_ui] 收到触发信号，开始演示序列!")
            sent = False
            phase = 0

        if phase == 0 and not sent:
            # Send GRAB command
            print("📤 [demo_ui] 发送抓取命令...")
            cmd = {"action": "GRAB"}
            node.send_output("mani_command", json.dumps(cmd).encode())
            print("✅ [demo_ui] 抓取命令已发送")
            sent = True
        elif event["type"] == "INPUT" and event["id"] == "mani_status":
            status = event["value"]
            if type(status).__name__ == "UInt8Array":
                status = status.to_numpy().tobytes().decode("utf-8")
            elif hasattr(status, "tobytes"):
                status = status.tobytes().decode("utf-8")
            elif isinstance(status, bytes):
                status = status.decode("utf-8")
            elif isinstance(status, str):
                pass
            else:
                continue
            status = json.loads(status)
            print(f"📨 [demo_ui] 收到机械臂状态: {status}")

            if phase == 0 and status.get("action") == "GRAB" and status.get("status") == "SUCCESS":
                # Send RETURN next
                print("⏳ [demo_ui] 等待0.5秒后发送返回命令...")
                time.sleep(0.5)
                print("📤 [demo_ui] 发送返回命令...")
                cmd = {"action": "RETURN"}
                node.send_output("mani_command", json.dumps(cmd).encode())
                print("✅ [demo_ui] 返回命令已发送")
                phase = 1
            elif phase == 1 and status.get("action") == "RETURN" and status.get("status") == "SUCCESS":
                print("🎉 [demo_ui] 演示序列完成!")
                print("=" * 60)
                print("✅ 机械臂演示演示结束")
                print("=" * 60)
                # End or loop; here we stop sending more
                phase = 2


if __name__ == "__main__":
    main()
